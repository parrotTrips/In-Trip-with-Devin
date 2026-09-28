import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { http, HttpResponse } from 'msw';
import { afterEach, beforeEach, vi } from 'vitest';

import { server } from '../test/server';

vi.mock('../features/staff/pages/StaffScreen', () => ({
  default: function MockStaffScreen({ onSwitchToTravelerView }: { onSwitchToTravelerView: () => void }) {
    return (
      <div>
        <p>Staff shell</p>
        <button onClick={onSwitchToTravelerView}>Traveler view</button>
      </div>
    );
  },
}));

import App from './App';
import type { TripChoice } from '../features/auth/services/auth-api';

const OTP_TRIP_CURRENT: TripChoice = {
  trip_id: 'test-001',
  title: 'Rio Adventure',
  destination: 'Rio de Janeiro',
  start_date: '2026-01-10',
  end_date: '2026-01-20',
  role: 'traveler',
  is_current: true,
};

const OTP_TRIP_FUTURE: TripChoice = {
  trip_id: 'test-future',
  title: 'Lisbon Kickoff',
  destination: 'Lisbon',
  start_date: '2026-06-01',
  end_date: '2026-06-10',
  role: 'traveler',
  is_current: false,
};

async function goThroughPhoneAndCode() {
  server.use(
    http.post('http://localhost:8000/auth/request-otp', () =>
      HttpResponse.json({ message: 'OTP generated', debug_code: '111111' })
    )
  );

  await userEvent.type(screen.getByPlaceholderText('Phone number'), '5551234567');
  await userEvent.click(screen.getByRole('button', { name: /send whatsapp code/i }));
  await screen.findByText('Verification Code');

  const user = userEvent.setup();
  for (let i = 0; i < 6; i++) {
    const input = document.getElementById(`code-${i}`);
    if (!input) throw new Error(`Missing code input code-${i}`);
    await user.type(input, '1');
  }
}

const MOCK_TRIP = {
  trip: { wetravel_trip_uuid: 'test-001', title: 'Test Trip', destination: 'Test', start_date: '2026-02-27', end_date: '2026-03-08', url: null },
};
const MOCK_PHASES = {
  wetravel_trip_uuid: 'test-001',
  phases: [
    { id: 'ph-1', phase_type: 'pre-trip', title: 'Visa', subtitle: null, icon: 'passport', short_description: 'Visa', detailed_description: null, sort_order: 0, starts_at: null, is_locked_by_default: false, checklist_items: [], links: [] },
  ],
};
const MOCK_TRAVELERS = { travelers: [] };

function setupTripHandlers() {
  server.use(
    http.get('http://localhost:8000/me/trip', () => HttpResponse.json(MOCK_TRIP)),
    http.get('http://localhost:8000/me/trip/phases', () => HttpResponse.json(MOCK_PHASES)),
    http.get('http://localhost:8000/me/trip/travelers', () => HttpResponse.json(MOCK_TRAVELERS)),
    http.get('http://localhost:8000/me/announcements', () => HttpResponse.json({
      announcements: [],
      unread_count: 0,
    })),
    http.get('http://localhost:8000/me/qr-code', () =>
      HttpResponse.json({
        trip_uuid: 'test-001',
        trip_traveler_id: 'traveler-001',
        qr_payload: 'parrot-trip-checkin:test-001:traveler-001',
      })
    ),
  );
}

describe('App composition', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.unstubAllEnvs();
    setupTripHandlers();
  });

  afterEach(() => {
    localStorage.clear();
    vi.unstubAllEnvs();
  });

  test('renders login when there is no authenticated user', () => {
    window.history.pushState({}, '', '/');

    render(<App />);

    expect(screen.getByText('Welcome, Traveler!')).toBeInTheDocument();
  });

  test('renders main routes when the user is authenticated', async () => {
    localStorage.setItem(
      'parrot_user',
      JSON.stringify({ userId: 'uid-1', phone: '+15551111111', name: 'Alice', token: 'tok', role: 'traveler', tripId: 'test-001', activeTrip: null })
    );
    window.history.pushState({}, '', '/');

    render(<App />);

    await waitFor(() => {
      expect(screen.getByText('Trip Progress')).toBeInTheDocument();
    });
    expect(screen.getByText('Journey')).toBeInTheDocument();
    expect(screen.getByText('Information')).toBeInTheDocument();
    expect(screen.getByText('My Profile')).toBeInTheDocument();
    expect(screen.queryByText('Secret Missions')).not.toBeInTheDocument();
    expect(screen.queryByText('Sharing XP')).not.toBeInTheDocument();
  });

  test('renders main routes when dev auto-login is enabled', async () => {
    vi.stubEnv('VITE_DEV_AUTO_LOGIN', 'true');
    vi.stubEnv('VITE_DEV_USER_ID', 'uid-7');
    vi.stubEnv('VITE_DEV_USER_PHONE', '+15557777777');
    vi.stubEnv('VITE_DEV_USER_NAME', 'Dev Traveler');

    window.history.pushState({}, '', '/');

    render(<App />);

    await waitFor(() => {
      expect(screen.getByText('Trip Progress')).toBeInTheDocument();
    });
    expect(screen.getByText('Journey')).toBeInTheDocument();
    expect(screen.getByText('Information')).toBeInTheDocument();
    expect(screen.getByText('My Profile')).toBeInTheDocument();
    expect(screen.queryByText('Secret Missions')).not.toBeInTheDocument();
    expect(screen.queryByText('Sharing XP')).not.toBeInTheDocument();
  });

  test('shows a minimal floating return button when a staff user opens traveler preview', async () => {
    localStorage.setItem(
      'parrot_user',
      JSON.stringify({ userId: 'uid-2', phone: '+15552222222', name: 'Bob Staff', token: 'tok', role: 'staff', tripId: 'test-001', activeTrip: null })
    );
    window.history.pushState({}, '', '/');

    render(<App />);
    const user = userEvent.setup();

    expect(screen.getByText('Staff shell')).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: 'Traveler view' }));

    await waitFor(() => {
      expect(screen.getByText('Trip Progress')).toBeInTheDocument();
    });
    expect(screen.getByRole('button', { name: 'Staff view' })).toBeInTheDocument();
    expect(screen.queryByText('Viewing as traveler')).not.toBeInTheDocument();
  });

  test('resets a staff traveler preview when switching to a different staff-role trip', async () => {
    localStorage.setItem(
      'parrot_user',
      JSON.stringify({ userId: 'uid-4', phone: '+15554444444', name: 'Dave Staff', token: 'tok', role: 'staff', tripId: 'test-001', activeTrip: null })
    );
    window.history.pushState({}, '', '/');

    server.use(
      http.get('http://localhost:8000/auth/trips', () =>
        HttpResponse.json({
          trips: [
            { ...OTP_TRIP_CURRENT, role: 'staff' },
            { trip_id: 'test-staff-2', title: 'Lisbon Staff Trip', destination: 'Lisbon', start_date: '2026-06-01', end_date: '2026-06-10', role: 'staff', is_current: false },
          ],
        })
      ),
      http.post('http://localhost:8000/auth/select-trip', () =>
        HttpResponse.json({
          status: 'trip_selected',
          user_id: 'uid-4',
          phone: '+15554444444',
          name: 'Dave Staff',
          role: 'staff',
          message: 'Login successful',
          access_token: 'tok-switched',
          active_trip: { trip_id: 'test-staff-2', title: 'Lisbon Staff Trip', destination: 'Lisbon', start_date: '2026-06-01', end_date: '2026-06-10', role: 'staff', is_current: false },
        })
      ),
      http.get('http://localhost:8000/profile/uid-4', () =>
        HttpResponse.json({
          user_id: 'uid-4',
          phone: '+15554444444',
          name: 'Dave Staff',
          profile: null,
          roommate: null,
        })
      )
    );

    render(<App />);
    const user = userEvent.setup();

    expect(screen.getByText('Staff shell')).toBeInTheDocument();

    // Preview the traveler view on the current staff trip first.
    await user.click(screen.getByRole('button', { name: 'Traveler view' }));
    await waitFor(() => {
      expect(screen.getByText('Trip Progress')).toBeInTheDocument();
    });

    // The trip switcher lives on the real traveler profile screen — navigate
    // there (the mocked StaffScreen isn't rendered while previewing).
    await user.click(screen.getByText('My Profile', { selector: 'span' }).closest('button')!);
    await screen.findByRole('heading', { name: 'My Profile' });

    // Switch to a different staff-role trip while still previewing traveler view.
    await user.click(screen.getByRole('button', { name: /trocar de viagem/i }));
    await screen.findByText('Escolha sua viagem');
    await user.click(screen.getByText('Lisbon Staff Trip').closest('button')!);

    // Landing on the new (staff-role) trip must show the staff UI, not a
    // carried-over traveler preview from the previous trip.
    await waitFor(() => {
      expect(screen.getByText('Staff shell')).toBeInTheDocument();
    });
    expect(screen.queryByText('Trip Progress')).not.toBeInTheDocument();
  });

  test('consumes the ?view=traveler deep link once, so a later trip switch remount does not reapply it', async () => {
    localStorage.setItem(
      'parrot_user',
      JSON.stringify({ userId: 'uid-5', phone: '+15555555555', name: 'Eve Staff', token: 'tok', role: 'staff', tripId: 'test-001', activeTrip: null })
    );
    window.history.pushState({}, '', '/profile?view=traveler');

    server.use(
      http.get('http://localhost:8000/profile/uid-5', () =>
        HttpResponse.json({ user_id: 'uid-5', phone: '+15555555555', name: 'Eve Staff', profile: null, roommate: null })
      ),
      http.get('http://localhost:8000/auth/trips', () =>
        HttpResponse.json({
          trips: [
            { ...OTP_TRIP_CURRENT, role: 'staff' },
            { trip_id: 'test-staff-3', title: 'Porto Staff Trip', destination: 'Porto', start_date: '2026-07-01', end_date: '2026-07-10', role: 'staff', is_current: false },
          ],
        })
      ),
      http.post('http://localhost:8000/auth/select-trip', () =>
        HttpResponse.json({
          status: 'trip_selected',
          user_id: 'uid-5',
          phone: '+15555555555',
          name: 'Eve Staff',
          role: 'staff',
          message: 'Login successful',
          access_token: 'tok-switched-2',
          active_trip: { trip_id: 'test-staff-3', title: 'Porto Staff Trip', destination: 'Porto', start_date: '2026-07-01', end_date: '2026-07-10', role: 'staff', is_current: false },
        })
      )
    );

    render(<App />);

    // The deep link puts the staff user directly into the traveler-preview
    // UI on the first mount.
    await screen.findByRole('heading', { name: 'My Profile' });
    expect(screen.queryByText('Staff shell')).not.toBeInTheDocument();
    expect(window.location.search).toBe('');

    // Switch to a different staff-role trip from the profile screen.
    await userEvent.click(await screen.findByRole('button', { name: /trocar de viagem/i }));
    await screen.findByText('Escolha sua viagem');
    await userEvent.click(screen.getByText('Porto Staff Trip').closest('button')!);

    // Landing on the new trip must show the staff UI — the deep link was
    // consumed on the first mount and must not reapply on this remount.
    await waitFor(() => {
      expect(screen.getByText('Staff shell')).toBeInTheDocument();
    });
    expect(screen.queryByRole('heading', { name: 'My Profile' })).not.toBeInTheDocument();
  });

  test('makes the app underneath non-interactive while the trip switcher overlay is open', async () => {
    localStorage.setItem(
      'parrot_user',
      JSON.stringify({ userId: 'uid-6', phone: '+15556666666', name: 'Fay Traveler', token: 'tok', role: 'traveler', tripId: 'test-001', activeTrip: null })
    );
    window.history.pushState({}, '', '/profile');

    server.use(
      http.get('http://localhost:8000/profile/uid-6', () =>
        HttpResponse.json({ user_id: 'uid-6', phone: '+15556666666', name: 'Fay Traveler', profile: null, roommate: null })
      ),
      http.get('http://localhost:8000/auth/trips', () =>
        HttpResponse.json({ trips: [OTP_TRIP_CURRENT, OTP_TRIP_FUTURE] })
      )
    );

    render(<App />);

    const switchButton = await screen.findByRole('button', { name: /trocar de viagem/i });
    expect(switchButton.closest('[aria-hidden]')).toBeNull();

    await userEvent.click(switchButton);
    await screen.findByText('Escolha sua viagem');

    // Walk up from the (still-mounted) button we clicked rather than
    // querying the whole document — the overlay itself contains decorative
    // `aria-hidden="true"` icons (e.g. the Parrot logo) that aren't the app
    // wrapper we're asserting on.
    const hiddenTree = switchButton.closest('[aria-hidden="true"]') as HTMLElement | null;
    expect(hiddenTree).not.toBeNull();
    expect(hiddenTree?.inert).toBe(true);
  });

  test('opens traveler profile deep links directly for staff when requested', async () => {
    localStorage.setItem(
      'parrot_user',
      JSON.stringify({ userId: 'uid-3', phone: '+15553333333', name: 'Carol Staff', token: 'tok', role: 'staff', tripId: 'test-001', activeTrip: null })
    );
    window.history.pushState({}, '', '/profile?section=pre-departure&view=traveler');

    server.use(
      http.get('http://localhost:8000/profile/uid-3', () =>
        HttpResponse.json({
          user_id: 'uid-3',
          wetravel_trip_uuid: 'test-001',
          phone: '+15553333333',
          name: 'Carol Staff',
          profile: {
            preferred_name: 'Carol',
            email: 'carol@example.com',
          },
          roommate: null,
        })
      )
    );

    render(<App />);

    await screen.findByText('My Profile');
    expect(screen.queryByText('Staff shell')).not.toBeInTheDocument();
    expect(screen.getByLabelText(/visa status/i)).toBeInTheDocument();
  });

  test('enters the traveler app straight after OTP when exactly one trip is eligible', async () => {
    window.history.pushState({}, '', '/');
    server.use(
      http.post('http://localhost:8000/auth/verify-otp', () =>
        HttpResponse.json({
          status: 'trip_selected',
          user_id: 'uid-otp-1',
          phone: '+15551234567',
          name: 'Alice',
          role: 'traveler',
          message: 'Login successful',
          access_token: 'tok-otp',
          active_trip: OTP_TRIP_CURRENT,
        })
      )
    );

    render(<App />);
    await goThroughPhoneAndCode();

    await waitFor(() => {
      expect(screen.getByText('Trip Progress')).toBeInTheDocument();
    });
  });

  test('shows the trip selector after OTP when multiple trips are eligible, then enters the app once one is picked', async () => {
    window.history.pushState({}, '', '/');
    server.use(
      http.post('http://localhost:8000/auth/verify-otp', () =>
        HttpResponse.json({
          status: 'selection_required',
          user_id: 'uid-otp-2',
          phone: '+15551234567',
          name: 'Alice',
          message: 'Trip selection required',
          selection_token: 'selection-tok',
          trips: [OTP_TRIP_CURRENT, OTP_TRIP_FUTURE],
        })
      ),
      http.post('http://localhost:8000/auth/select-trip', () =>
        HttpResponse.json({
          status: 'trip_selected',
          user_id: 'uid-otp-2',
          phone: '+15551234567',
          name: 'Alice',
          role: 'traveler',
          message: 'Login successful',
          access_token: 'tok-otp-2',
          active_trip: OTP_TRIP_CURRENT,
        })
      )
    );

    render(<App />);
    await goThroughPhoneAndCode();

    await screen.findByText('Escolha sua viagem');
    expect(screen.getByText('Lisbon Kickoff')).toBeInTheDocument();
    // Not logged in yet: still the selector, not the app.
    expect(screen.queryByText('Trip Progress')).not.toBeInTheDocument();

    await userEvent.click(screen.getByText('Rio Adventure').closest('button')!);

    await waitFor(() => {
      expect(screen.getByText('Trip Progress')).toBeInTheDocument();
    });
  });

  test('shows the no-trip explanatory screen after OTP when there are no eligible trips', async () => {
    window.history.pushState({}, '', '/');
    server.use(
      http.post('http://localhost:8000/auth/verify-otp', () =>
        HttpResponse.json({
          status: 'no_trips',
          user_id: 'uid-otp-3',
          phone: '+15551234567',
          name: 'Alice',
          message: 'No current or future trips available',
        })
      )
    );

    render(<App />);
    await goThroughPhoneAndCode();

    await screen.findByText('Você não tem viagens atuais ou futuras');
    expect(screen.queryByText('Trip Progress')).not.toBeInTheDocument();
  });
});
