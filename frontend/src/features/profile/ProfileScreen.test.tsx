import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { http, HttpResponse } from 'msw';
import { MemoryRouter } from 'react-router-dom';

import App from '../../app/App';
import { AuthProvider } from '../../app/providers/AuthProvider';
import { TripContext } from '../../app/providers/trip-context';
import { server } from '../../test/server';
import type { TripChoice } from '../auth/services/auth-api';
import ProfileScreen from './pages/ProfileScreen';

const SWITCH_TRIP_CURRENT: TripChoice = {
  trip_id: 'trip-001',
  title: 'Trip One',
  destination: 'Rio de Janeiro',
  start_date: '2026-02-27',
  end_date: '2026-03-08',
  role: 'traveler',
  is_current: true,
};

const SWITCH_TRIP_OTHER: TripChoice = {
  trip_id: 'trip-002',
  title: 'Trip Two',
  destination: 'Lisbon',
  start_date: '2026-06-01',
  end_date: '2026-06-10',
  role: 'traveler',
  is_current: false,
};

function setUpSwitcherSession() {
  localStorage.setItem(
    'parrot_user',
    JSON.stringify({
      userId: 'traveler-1',
      phone: '+15550000001',
      name: 'Alice',
      token: 'tok',
      role: 'traveler',
      tripId: 'trip-001',
      activeTrip: SWITCH_TRIP_CURRENT,
    })
  );
}

function setUpSwitcherAppHandlers() {
  server.use(
    http.get('http://localhost:8000/me/trip', () =>
      HttpResponse.json({
        trip: {
          wetravel_trip_uuid: 'trip-001',
          title: 'Trip One',
          destination: 'Rio de Janeiro',
          start_date: '2026-02-27',
          end_date: '2026-03-08',
          url: null,
          service_agreement_url: null,
          trip_mode: 'in-trip',
        },
      })
    ),
    http.get('http://localhost:8000/me/trip/phases', () =>
      HttpResponse.json({ wetravel_trip_uuid: 'trip-001', phases: [], ideal_pace_phase_id: null })
    ),
    http.get('http://localhost:8000/me/trip/travelers', () => HttpResponse.json({ travelers: [] })),
    http.get('http://localhost:8000/me/announcements', () =>
      HttpResponse.json({ announcements: [], unread_count: 0 })
    ),
    http.get('http://localhost:8000/profile/traveler-1', () =>
      HttpResponse.json({
        user_id: 'traveler-1',
        phone: '+15550000001',
        name: 'Alice',
        profile: { preferred_name: 'Alice', email: 'alice@example.com' },
        roommate: null,
      })
    ),
    http.get('http://localhost:8000/me/qr-code', () =>
      HttpResponse.json({
        trip_uuid: 'trip-001',
        trip_traveler_id: 'trip-traveler-001',
        qr_payload: 'parrot-trip-checkin:trip-001:trip-traveler-001',
      })
    )
  );
}

describe('ProfileScreen', () => {
  test('loads and saves the profile data', async () => {
    let savedPayload: Record<string, unknown> | null = null;

    localStorage.setItem(
      'parrot_user',
      JSON.stringify({ userId: 1, phone: '+15550000001', name: 'Alice', token: 'tok', role: 'traveler', tripId: 'trip-001', activeTrip: null })
    );

    server.use(
      http.get('http://localhost:8000/profile/1', () =>
        HttpResponse.json({
          user_id: 1,
          phone: '+15550000001',
          name: 'Alice',
          profile: {
            preferred_name: 'Alice',
            email: 'alice@example.com',
          },
          roommate: null,
        })
      ),
      http.get('http://localhost:8000/trip/ross26/travelers', () =>
        HttpResponse.json({ trip_id: 'ross26', travelers: [] })
      ),
      http.get('http://localhost:8000/me/qr-code', () =>
        HttpResponse.json({
          trip_uuid: 'test-trip-001',
          trip_traveler_id: 'trip-traveler-001',
          qr_payload: 'parrot-trip-checkin:test-trip-001:trip-traveler-001',
        })
      ),
      http.put('http://localhost:8000/profile/1', async ({ request }) => {
        savedPayload = (await request.json()) as Record<string, unknown>;
        return HttpResponse.json({ message: 'Profile updated' });
      })
    );

    render(
      <MemoryRouter>
        <AuthProvider>
          <ProfileScreen />
        </AuthProvider>
      </MemoryRouter>
    );

    await screen.findByText('My Profile');
    await userEvent.click(screen.getByRole('button', { name: /registration details/i }));
    const packagesButton = screen.getByRole('button', { name: /packages/i });
    expect(packagesButton).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /service agreement/i })).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /esim/i })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /roommate/i })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /flight information/i })).not.toBeInTheDocument();
    const preferredNameInput = await screen.findByLabelText('Preferred Name');
    expect(preferredNameInput).toHaveValue('Alice');

    await userEvent.click(packagesButton);
    const managePaymentsLink = screen.getByRole('link', { name: /manage my payments/i });
    expect(managePaymentsLink).toHaveAttribute('href', 'https://www.wetravel.com/');
    const packageTransferLink = screen.getByRole('link', { name: /transfer or cancel your package/i });
    expect(packageTransferLink).toHaveAttribute(
      'href',
      'https://package-transfer-116789457910.southamerica-east1.run.app'
    );

    await userEvent.clear(preferredNameInput);
    await userEvent.type(preferredNameInput, 'Bea');
    expect(screen.queryByRole('button', { name: /save profile/i })).not.toBeInTheDocument();
    await userEvent.click(screen.getByRole('button', { name: /save changes/i }));

    await waitFor(() => {
      expect(savedPayload).toMatchObject({
        preferred_name: 'Bea',
        email: 'alice@example.com',
      });
    });
  });

  test('saves pre departure information without duplicating registration fields', async () => {
    let savedPayload: Record<string, unknown> | null = null;

    localStorage.setItem(
      'parrot_user',
      JSON.stringify({ userId: 1, phone: '+15550000001', name: 'Alice', token: 'tok', role: 'traveler', tripId: 'trip-001', activeTrip: null })
    );

    server.use(
      http.get('http://localhost:8000/profile/1', () =>
        HttpResponse.json({
          user_id: 1,
          phone: '+15550000001',
          name: 'Alice',
          profile: {
            preferred_name: 'Alice',
            email: 'alice@example.com',
            visa_status: 'Not yet, I already started my visa process but don\'t have one yet',
          },
          roommate: null,
        })
      ),
      http.get('http://localhost:8000/me/qr-code', () =>
        HttpResponse.json({
          trip_uuid: 'test-trip-001',
          trip_traveler_id: 'trip-traveler-001',
          qr_payload: 'parrot-trip-checkin:test-trip-001:trip-traveler-001',
        })
      ),
      http.put('http://localhost:8000/profile/1', async ({ request }) => {
        savedPayload = (await request.json()) as Record<string, unknown>;
        return HttpResponse.json({ message: 'Profile updated' });
      })
    );

    render(
      <MemoryRouter>
        <AuthProvider>
          <ProfileScreen />
        </AuthProvider>
      </MemoryRouter>
    );

    await screen.findByText('My Profile');
    await userEvent.click(screen.getByRole('button', { name: /pre departure information/i }));
    const preDepartureContainer = screen
      .getByRole('button', { name: /pre departure information/i })
      .closest('.bg-white') as HTMLElement;

    expect(within(preDepartureContainer).queryByLabelText(/passport number/i)).not.toBeInTheDocument();
    expect(within(preDepartureContainer).queryByLabelText(/dietary restrictions/i)).not.toBeInTheDocument();
    expect(within(preDepartureContainer).queryByLabelText(/^email$/i)).not.toBeInTheDocument();

    await userEvent.selectOptions(
      within(preDepartureContainer).getByLabelText(/visa status/i),
      'I am not sure and I need orientation about it'
    );
    expect(within(preDepartureContainer).getByTestId('arrival-date-time-grid')).toHaveClass('grid-cols-1', 'sm:grid-cols-2');
    expect(within(preDepartureContainer).getByTestId('departure-date-time-grid')).toHaveClass('grid-cols-1', 'sm:grid-cols-2');

    await userEvent.type(within(preDepartureContainer).getByLabelText(/arrival date/i), '10/03/2026');
    await userEvent.type(within(preDepartureContainer).getByLabelText(/arrival time/i), '2:30 PM');
    await userEvent.type(within(preDepartureContainer).getByLabelText(/arrival airport and flight/i), 'GRU, AA 1234');
    await userEvent.type(within(preDepartureContainer).getByLabelText(/departure date/i), '10/12/2026');
    await userEvent.type(within(preDepartureContainer).getByLabelText(/departure time/i), '9:45 PM');
    await userEvent.type(within(preDepartureContainer).getByLabelText(/departure airport and flight/i), 'GIG, LA 4567');
    await userEvent.selectOptions(
      within(preDepartureContainer).getByLabelText(/checked bags/i),
      '1 checked bag is all I need'
    );
    await userEvent.selectOptions(
      within(preDepartureContainer).getByLabelText(/Need help with early arrival or longer stay/i),
      'No, thanks'
    );
    await userEvent.selectOptions(
      within(preDepartureContainer).getByLabelText(/Early Check-in Preference/i),
      "I’ll arrive after the check-in time."
    );
    await userEvent.selectOptions(
      within(preDepartureContainer).getByLabelText(/travel insurance status/i),
      'Already hired one'
    );
    await userEvent.selectOptions(
      within(preDepartureContainer).getByLabelText(/Medical Coverage in Brazil/i),
      'Yes'
    );
    await userEvent.type(within(preDepartureContainer).getByLabelText(/insurance provider/i), 'SafetyWing');
    await userEvent.type(within(preDepartureContainer).getByLabelText(/policy number/i), 'POL-123');
    await userEvent.selectOptions(
      within(preDepartureContainer).getByLabelText(/Do you know who you will share the room with/i),
      'I am staying in an individual room'
    );
    await userEvent.selectOptions(
      within(preDepartureContainer).getByLabelText(/Room Configuration/i),
      'One double bed (for two people)'
    );
    await userEvent.type(within(preDepartureContainer).getByLabelText(/emergency contact/i), 'Maria +5511999999999');

    expect(within(preDepartureContainer).getByText(/Hotels usually have a 2 PM check-in time/i)).toBeInTheDocument();
    expect(within(preDepartureContainer).getByText(/We will be posting moments of the trip in our Instagram account/i)).toBeInTheDocument();
    expect(within(preDepartureContainer).getByText(/Some hotels ask for this info on the check in/i)).toBeInTheDocument();
    expect(within(preDepartureContainer).queryByLabelText(/Trip Mood/i)).not.toBeInTheDocument();
    expect(within(preDepartureContainer).queryByLabelText(/Social Topic/i)).not.toBeInTheDocument();
    expect(within(preDepartureContainer).queryByLabelText(/Always Up For/i)).not.toBeInTheDocument();

    await userEvent.click(screen.getByRole('button', { name: /save changes/i }));

    await waitFor(() => {
      expect(savedPayload).toMatchObject({
        email: 'alice@example.com',
        visa_status: 'I am not sure and I need orientation about it',
        arrival_date: '2026-10-03',
        arrival_time: '14:30',
        arrival_flight: 'GRU, AA 1234',
        departure_date: '2026-10-12',
        departure_time: '21:45',
        departure_flight: 'GIG, LA 4567',
        checked_bags: '1 checked bag is all I need',
        extended_stay_help: 'No, thanks',
        early_check_in_preference: "I’ll arrive after the check-in time.",
        travel_insurance_status: 'Already hired one',
        travel_insurance_brazil_medical_coverage: 'Yes',
        travel_insurance_provider: 'SafetyWing',
        travel_insurance_policy_number: 'POL-123',
        roommate_status: 'I am staying in an individual room',
        room_configuration: 'One double bed (for two people)',
        emergency_contact: 'Maria +5511999999999',
      });
    });
  });

  test('opens pre departure information from a section deep link', async () => {
    localStorage.setItem(
      'parrot_user',
      JSON.stringify({ userId: 1, phone: '+15550000001', name: 'Alice', token: 'tok', role: 'traveler', tripId: 'trip-001', activeTrip: null })
    );

    server.use(
      http.get('http://localhost:8000/profile/1', () =>
        HttpResponse.json({
          user_id: 1,
          phone: '+15550000001',
          name: 'Alice',
          profile: {
            preferred_name: 'Alice',
            email: 'alice@example.com',
          },
          roommate: null,
        })
      ),
      http.get('http://localhost:8000/me/qr-code', () =>
        HttpResponse.json({
          trip_uuid: 'test-trip-001',
          trip_traveler_id: 'trip-traveler-001',
          qr_payload: 'parrot-trip-checkin:test-trip-001:trip-traveler-001',
        })
      )
    );

    render(
      <MemoryRouter initialEntries={['/profile?section=pre-departure']}>
        <AuthProvider>
          <ProfileScreen />
        </AuthProvider>
      </MemoryRouter>
    );

    await screen.findByText('My Profile');

    const preDepartureContainer = screen
      .getByRole('button', { name: /pre departure information/i })
      .closest('.bg-white') as HTMLElement;
    expect(within(preDepartureContainer).getByLabelText(/visa status/i)).toBeInTheDocument();
  });

  test('requires visible pre departure fields and selects roommate from trip travelers', async () => {
    let savedPayload: Record<string, unknown> | null = null;

    localStorage.setItem(
      'parrot_user',
      JSON.stringify({ userId: 'traveler-1', phone: '+15550000001', name: 'Alice', token: 'tok', role: 'traveler', tripId: 'trip-001', activeTrip: null })
    );

    server.use(
      http.get('http://localhost:8000/profile/traveler-1', () =>
        HttpResponse.json({
          user_id: 'traveler-1',
          phone: '+15550000001',
          name: 'Alice',
          profile: {
            preferred_name: 'Alice',
            email: 'alice@example.com',
          },
          roommate: null,
        })
      ),
      http.get('http://localhost:8000/me/qr-code', () =>
        HttpResponse.json({
          trip_uuid: 'test-trip-001',
          trip_traveler_id: 'trip-traveler-001',
          qr_payload: 'parrot-trip-checkin:test-trip-001:trip-traveler-001',
        })
      ),
      http.put('http://localhost:8000/profile/traveler-1', async ({ request }) => {
        savedPayload = (await request.json()) as Record<string, unknown>;
        return HttpResponse.json({ message: 'Profile updated' });
      })
    );

    render(
      <MemoryRouter>
        <AuthProvider>
          <TripContext.Provider
            value={{
              tripInfo: null,
              phases: [],
              travelers: [
                { id: 'traveler-1', name: 'Alice', phone: '+15550000001', current_phase_id: null },
                { id: 'traveler-3', name: 'Zoe Rivera', phone: '+15550000003', current_phase_id: null },
                { id: 'traveler-2', name: 'Bea Santos', phone: '+15550000002', current_phase_id: null },
                { id: 'traveler-4', name: 'Ana Baker', phone: '+15550000004', current_phase_id: null },
              ],
              idealPacePhaseId: null,
              loading: false,
              error: null,
              refetch: () => {},
            }}
          >
            <ProfileScreen />
          </TripContext.Provider>
        </AuthProvider>
      </MemoryRouter>
    );

    await screen.findByText('My Profile');
    await userEvent.click(screen.getByRole('button', { name: /pre departure information/i }));
    const preDepartureContainer = screen
      .getByRole('button', { name: /pre departure information/i })
      .closest('.bg-white') as HTMLElement;

    await userEvent.click(screen.getByRole('button', { name: /save changes/i }));
    expect(await within(preDepartureContainer).findByText(/Visa Status is required/i)).toBeInTheDocument();
    expect(savedPayload).toBeNull();

    await userEvent.selectOptions(
      within(preDepartureContainer).getByLabelText(/visa status/i),
      'Yes, I already have a visa / I can enter Brazil without a visa'
    );
    await userEvent.type(within(preDepartureContainer).getByLabelText(/arrival date/i), '10/03/2026');
    await userEvent.type(within(preDepartureContainer).getByLabelText(/arrival airport and flight/i), 'GRU, AA 1234');
    await userEvent.type(within(preDepartureContainer).getByLabelText(/departure date/i), '10/12/2026');
    await userEvent.type(within(preDepartureContainer).getByLabelText(/departure airport and flight/i), 'GIG, LA 4567');
    await userEvent.selectOptions(within(preDepartureContainer).getByLabelText(/checked bags/i), 'No checked bags, I travel light');
    await userEvent.selectOptions(within(preDepartureContainer).getByLabelText(/travel insurance status/i), 'Already hired one');
    await userEvent.selectOptions(within(preDepartureContainer).getByLabelText(/medical coverage in Brazil/i), 'Yes');
    await userEvent.type(within(preDepartureContainer).getByLabelText(/insurance provider/i), 'SafetyWing');
    await userEvent.type(within(preDepartureContainer).getByLabelText(/policy number/i), 'POL-123');
    await userEvent.selectOptions(within(preDepartureContainer).getByLabelText(/do you know who you will share the room with/i), 'Yes');
    const roommateInput = within(preDepartureContainer).getByLabelText(/requested roommate/i);
    await userEvent.click(roommateInput);
    const roommateList = within(preDepartureContainer).getByRole('listbox', { name: /requested roommate suggestions/i });
    expect(within(roommateList).getAllByRole('option').map(option => option.textContent)).toEqual([
      'Ana Baker',
      'Bea Santos',
      'Zoe Rivera',
    ]);
    await userEvent.type(roommateInput, 'bea');
    await userEvent.click(within(roommateList).getByRole('option', { name: 'Bea Santos' }));
    expect(within(preDepartureContainer).queryByLabelText(/roommate gender preference/i)).not.toBeInTheDocument();
    await userEvent.selectOptions(within(preDepartureContainer).getByLabelText(/room configuration/i), 'Two twin beds (one single bed each)');
    await userEvent.selectOptions(within(preDepartureContainer).getByLabelText(/need help with early arrival or longer stay/i), 'No, thanks');
    await userEvent.selectOptions(within(preDepartureContainer).getByLabelText(/early check-in preference/i), "I’ll arrive after the check-in time.");
    await userEvent.type(within(preDepartureContainer).getByLabelText(/emergency contact/i), 'Maria +5511999999999');

    await userEvent.click(screen.getByRole('button', { name: /save changes/i }));

    await waitFor(() => {
      expect(savedPayload).toMatchObject({
        roommate_status: 'Yes',
        roommate_user_id: 'traveler-2',
      });
      expect(savedPayload).not.toHaveProperty('roommate_email');
      expect(savedPayload).not.toHaveProperty('trip_mood');
      expect(savedPayload).not.toHaveProperty('social_topic');
      expect(savedPayload).not.toHaveProperty('always_up_for');
    });

    await userEvent.selectOptions(within(preDepartureContainer).getByLabelText(/do you know who you will share the room with/i), 'No, please match me with someone.');
    expect(within(preDepartureContainer).queryByLabelText(/requested roommate/i)).not.toBeInTheDocument();
    expect(within(preDepartureContainer).getByLabelText(/roommate gender preference/i)).toBeInTheDocument();
  });

  test('offers Trocar de viagem, refreshes memberships fresh, and opens the selector without OTP', async () => {
    let tripsRequests = 0;
    let lastAuthHeader: string | null = null;
    setUpSwitcherSession();
    window.history.pushState({}, '', '/profile');
    setUpSwitcherAppHandlers();
    server.use(
      http.get('http://localhost:8000/auth/trips', ({ request }) => {
        tripsRequests += 1;
        lastAuthHeader = request.headers.get('authorization');
        return HttpResponse.json({ trips: [SWITCH_TRIP_CURRENT, SWITCH_TRIP_OTHER] });
      })
    );

    render(<App />);

    const switchButton = await screen.findByRole('button', { name: /trocar de viagem/i });
    await userEvent.click(switchButton);

    await screen.findByText('Escolha sua viagem');
    expect(tripsRequests).toBe(1);
    expect(lastAuthHeader).toBe('Bearer tok');
    expect(screen.getByText('Trip Two')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /cancelar/i })).toBeInTheDocument();
    // No OTP step is shown — the switcher opens directly from the profile.
    expect(screen.queryByPlaceholderText('Phone number')).not.toBeInTheDocument();
    expect(screen.queryByText('Verification Code')).not.toBeInTheDocument();
  });

  test('cancelling the switcher returns to the exact previous session untouched', async () => {
    setUpSwitcherSession();
    window.history.pushState({}, '', '/profile');
    setUpSwitcherAppHandlers();
    server.use(
      http.get('http://localhost:8000/auth/trips', () =>
        HttpResponse.json({ trips: [SWITCH_TRIP_CURRENT, SWITCH_TRIP_OTHER] })
      )
    );

    render(<App />);

    await userEvent.click(await screen.findByRole('button', { name: /trocar de viagem/i }));
    await screen.findByText('Escolha sua viagem');

    await userEvent.click(screen.getByRole('button', { name: /cancelar/i }));

    expect(screen.queryByText('Escolha sua viagem')).not.toBeInTheDocument();
    await screen.findByRole('heading', { name: 'My Profile' });
    expect(JSON.parse(localStorage.getItem('parrot_user')!)).toMatchObject({
      userId: 'traveler-1',
      token: 'tok',
      tripId: 'trip-001',
    });
  });

  test('keeps the current session if selecting a new trip fails', async () => {
    setUpSwitcherSession();
    window.history.pushState({}, '', '/profile');
    setUpSwitcherAppHandlers();
    server.use(
      http.get('http://localhost:8000/auth/trips', () =>
        HttpResponse.json({ trips: [SWITCH_TRIP_CURRENT, SWITCH_TRIP_OTHER] })
      ),
      http.post('http://localhost:8000/auth/select-trip', () =>
        HttpResponse.json({ detail: 'Trip no longer available' }, { status: 409 })
      )
    );

    render(<App />);

    await userEvent.click(await screen.findByRole('button', { name: /trocar de viagem/i }));
    await screen.findByText('Escolha sua viagem');

    await userEvent.click(screen.getByText('Trip Two').closest('button')!);

    await screen.findByRole('alert');
    expect(screen.getByText('Escolha sua viagem')).toBeInTheDocument();
    expect(JSON.parse(localStorage.getItem('parrot_user')!)).toMatchObject({
      userId: 'traveler-1',
      token: 'tok',
      tripId: 'trip-001',
    });
  });

  test('offers a Cancelar option while the switcher is still loading trips', async () => {
    setUpSwitcherSession();
    window.history.pushState({}, '', '/profile');
    setUpSwitcherAppHandlers();
    let resolveTrips: (() => void) | undefined;
    server.use(
      http.get(
        'http://localhost:8000/auth/trips',
        () =>
          new Promise<Response>(resolve => {
            resolveTrips = () =>
              resolve(HttpResponse.json({ trips: [SWITCH_TRIP_CURRENT, SWITCH_TRIP_OTHER] }));
          })
      )
    );

    render(<App />);

    await userEvent.click(await screen.findByRole('button', { name: /trocar de viagem/i }));

    expect(await screen.findByRole('status', { name: /carregando viagens/i })).toBeInTheDocument();
    await userEvent.click(screen.getByRole('button', { name: /cancelar/i }));

    await screen.findByRole('heading', { name: 'My Profile' });
    expect(screen.queryByRole('status', { name: /carregando viagens/i })).not.toBeInTheDocument();

    // Let the in-flight request settle so it doesn't leak into another test.
    resolveTrips?.();
  });
});
