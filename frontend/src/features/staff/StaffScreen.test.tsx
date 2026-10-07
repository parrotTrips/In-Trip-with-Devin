import { act, render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { http, HttpResponse } from 'msw';
import { vi } from 'vitest';

import App from '../../app/App';
import { AuthProvider } from '../../app/providers/AuthProvider';
import { server } from '../../test/server';
import type { TripChoice } from '../auth/services/auth-api';
import StaffScreen from './pages/StaffScreen';

let qrSuccess: ((decodedText: string) => void) | null = null;
const scannerStart = vi.fn((_cameraConfig, _scannerConfig, onSuccess) => {
  qrSuccess = onSuccess;
  return Promise.resolve();
});
const scannerStop = vi.fn(() => Promise.resolve());
const scannerClear = vi.fn();

vi.mock('html5-qrcode', () => ({
  Html5Qrcode: vi.fn().mockImplementation(() => ({
    start: scannerStart,
    stop: scannerStop,
    clear: scannerClear,
  })),
}));

const STAFF_TRIP_ONE: TripChoice = {
  trip_id: 'trip-staff-1',
  title: 'Staff Trip One',
  destination: 'Rio de Janeiro',
  start_date: null,
  end_date: null,
  role: 'staff',
  is_current: true,
};

const STAFF_TRIP_TWO: TripChoice = {
  trip_id: 'trip-staff-2',
  title: 'Staff Trip Two',
  destination: 'Sao Paulo',
  start_date: null,
  end_date: null,
  role: 'staff',
  is_current: false,
};

const TRAVELER_TRIP: TripChoice = {
  trip_id: 'trip-traveler-1',
  title: 'Traveler Trip',
  destination: 'Lisbon',
  start_date: '2026-06-01',
  end_date: '2026-06-10',
  role: 'traveler',
  is_current: false,
};

function setUpStaffSwitcherAppHandlers() {
  server.use(
    http.get('http://localhost:8000/me/staff/trip', ({ request }) => {
      const isSecondStaffTrip = request.headers.get('authorization') === 'Bearer tok-staff-2';
      return HttpResponse.json({
        wetravel_trip_uuid: isSecondStaffTrip ? 'trip-staff-2' : 'trip-staff-1',
        title: isSecondStaffTrip ? 'Staff Trip Two' : 'Staff Trip One',
        start_date: null,
        end_date: null,
        days: [],
      });
    }),
    http.get('http://localhost:8000/me/staff/trip/contacts', ({ request }) => {
      const isSecondStaffTrip = request.headers.get('authorization') === 'Bearer tok-staff-2';
      return HttpResponse.json({
        wetravel_trip_uuid: isSecondStaffTrip ? 'trip-staff-2' : 'trip-staff-1',
        contacts: [],
      });
    }),
    http.get('http://localhost:8000/me/trip', () =>
      HttpResponse.json({
        trip: {
          wetravel_trip_uuid: 'trip-staff-1',
          title: 'Staff Trip One (traveler view)',
          destination: 'Rio de Janeiro',
          start_date: '2026-02-27',
          end_date: '2026-03-08',
          url: null,
          service_agreement_url: null,
        },
      })
    ),
    http.get('http://localhost:8000/me/trip/phases', () =>
      HttpResponse.json({
        wetravel_trip_uuid: 'trip-staff-1',
        phases: [
          { id: 'ph-1', phase_type: 'pre-trip', title: 'Visa', subtitle: null, icon: 'passport', short_description: 'Visa', detailed_description: null, sort_order: 0, starts_at: null, is_locked_by_default: false, checklist_items: [], links: [] },
        ],
        ideal_pace_phase_id: null,
      })
    ),
    http.get('http://localhost:8000/me/trip/travelers', () => HttpResponse.json({ travelers: [] })),
    http.get('http://localhost:8000/me/announcements', () =>
      HttpResponse.json({ announcements: [], unread_count: 0 })
    ),
    http.get('http://localhost:8000/profile/staff-1', () =>
      HttpResponse.json({
        user_id: 'staff-1',
        phone: '+5511888000001',
        name: 'Marcelo Staff',
        profile: null,
        roommate: null,
      })
    ),
    http.get('http://localhost:8000/me/qr-code', () =>
      HttpResponse.json({
        trip_uuid: 'trip-staff-1',
        trip_traveler_id: 'trip-traveler-staff-1',
        qr_payload: 'parrot-trip-checkin:trip-staff-1:trip-traveler-staff-1',
      })
    )
  );
}

function setUpStaffSwitcherSession() {
  localStorage.setItem(
    'parrot_user',
    JSON.stringify({
      userId: 'staff-1',
      phone: '+5511888000001',
      name: 'Marcelo Staff',
      token: 'tok',
      role: 'staff',
      tripId: 'trip-staff-1',
      activeTrip: STAFF_TRIP_ONE,
      canSwitchTrips: true,
    })
  );
}

function traveler(id: string, name: string, count: number, max: number, last: string | null = null) {
  return { id, name, qr_payload: `qr-${id}`, checkin_count: count, max_checkins: max, last_checked_in_at: last };
}

function serveActivityTravelers(travelers: ReturnType<typeof traveler>[]) {
  server.use(
    http.get('http://localhost:8000/me/staff/activities/:activityId/travelers', () =>
      HttpResponse.json({ travelers })
    )
  );
}

function renderStaff() {
  return render(
    <AuthProvider>
      <StaffScreen onSwitchToTravelerView={() => {}} />
    </AuthProvider>
  );
}

async function openActivity(user: ReturnType<typeof userEvent.setup>) {
  await user.click(await screen.findByText('Airport Transfer'));
  await screen.findByRole('heading', { name: 'Airport Transfer' });
}

describe('StaffScreen', () => {
  beforeEach(() => {
    qrSuccess = null;
    scannerStart.mockClear();
    scannerStop.mockClear();
    scannerClear.mockClear();
    localStorage.setItem(
      'parrot_user',
      JSON.stringify({ userId: 'staff-1', phone: '+5511888000001', name: 'Marcelo Staff', token: 'tok', role: 'staff', tripId: 'trip-staff-1', activeTrip: STAFF_TRIP_ONE, canSwitchTrips: true })
    );
    server.use(
      http.get('http://localhost:8000/me/staff/trip', () =>
        HttpResponse.json({
          wetravel_trip_uuid: 'TEST-2026-FULL',
          title: 'Test Trip',
          start_date: '2026-07-01',
          end_date: '2026-07-07',
          days: [
            {
              id: 'day-1',
              title: 'Day 1 — Arrival',
              subtitle: 'Arrival',
              icon: 'plane-landing',
              sort_order: 0,
              starts_at: null,
              activities: [
                {
                  id: 'activity-1',
                  name: 'Airport Transfer',
                  activity_type: 'logistics',
                  starts_at: null,
                  duration_minutes: null,
                  short_description: 'Airport pickup',
                  practical_info: null,
                  amount_brl: null,
                  sort_order: 0,
                  max_checkins: 1,
                  checkin_steps: [],
                  absent_travelers: ['Ana Silva'],
                  traveler_count: 12,
                  staff_tasks: [
                    {
                      id: 'task-1',
                      title: 'Coordenar van 1',
                      description: 'Receber viajantes no aeroporto',
                      sort_order: 1,
                    },
                  ],
                },
              ],
            },
          ],
        })
      ),
      http.get('http://localhost:8000/me/staff/trip/contacts', () =>
        HttpResponse.json({ wetravel_trip_uuid: 'TEST-2026-FULL', contacts: [] })
      )
    );
    serveActivityTravelers([traveler('t-ana', 'Ana Silva', 0, 1)]);
  });

  test('opens a dedicated page for the activity with its tasks and travelers', async () => {
    const user = userEvent.setup();
    renderStaff();

    await user.click(await screen.findByText('Day 1 — Arrival'));
    expect(screen.getByText('0 / 12 scanned')).toBeInTheDocument();
    await openActivity(user);

    expect(screen.getByRole('heading', { name: 'Airport Transfer' })).toBeInTheDocument();
    expect(screen.getByText('My tasks')).toBeInTheDocument();
    expect(screen.getByText('Coordenar van 1')).toBeInTheDocument();
    expect(await screen.findByText('Ana Silva')).toBeInTheDocument();
    expect(scannerStart).not.toHaveBeenCalled();

    await user.click(screen.getByRole('button', { name: /back to itinerary/i }));
    expect(screen.queryByRole('heading', { name: 'Airport Transfer' })).not.toBeInTheDocument();
  });

  test('shows each traveler once with status and progress, with filters and search', async () => {
    const user = userEvent.setup();
    serveActivityTravelers([
      traveler('t-ana', 'Ana Silva', 0, 2),
      traveler('t-bruno', 'Bruno Costa', 1, 2, '2026-07-01T12:05:00Z'),
      traveler('t-carla', 'Carla Dias', 2, 2, '2026-07-01T15:40:00Z'),
    ]);
    renderStaff();
    await user.click(await screen.findByText('Day 1 — Arrival'));
    await openActivity(user);

    const ana = (await screen.findByText('Ana Silva')).closest('li') as HTMLElement;
    expect(ana).toHaveTextContent('Not arrived');
    expect(ana).toHaveTextContent('0 of 2 check-ins');
    const bruno = screen.getByText('Bruno Costa').closest('li') as HTMLElement;
    expect(bruno).toHaveTextContent('In progress');
    expect(bruno).toHaveTextContent('1 of 2 check-ins');
    expect(bruno).toHaveTextContent('Next: check-in 2 of 2');
    const carla = screen.getByText('Carla Dias').closest('li') as HTMLElement;
    expect(carla).toHaveTextContent('Done');
    expect(within(carla).getByRole('button', { name: /check in carla dias/i })).toBeDisabled();
    expect(screen.getAllByText('Ana Silva')).toHaveLength(1);

    await user.click(screen.getByRole('button', { name: /^done \(1\)$/i }));
    expect(screen.queryByText('Ana Silva')).not.toBeInTheDocument();
    expect(screen.getByText('Carla Dias')).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: /^all \(3\)$/i }));
    await user.type(screen.getByPlaceholderText(/search traveler/i), 'bru');
    expect(screen.queryByText('Carla Dias')).not.toBeInTheDocument();
    expect(screen.getByText('Bruno Costa')).toBeInTheDocument();
  });

  test('checks a traveler in by name without opening the camera', async () => {
    const user = userEvent.setup();
    let scannedPayload: string | null = null;
    let travelersCalls = 0;
    server.use(
      http.get('http://localhost:8000/me/staff/activities/:activityId/travelers', () => {
        travelersCalls += 1;
        return HttpResponse.json({
          travelers: [traveler('t-ana', 'Ana Silva', travelersCalls > 1 ? 1 : 0, 1)],
        });
      }),
      http.post('http://localhost:8000/me/staff/activities/:activityId/checkins/preview', () =>
        HttpResponse.json({ status: 'ready_to_check_in', traveler_name: 'Ana Silva', scan_number: 1, max_checkins: 1 })
      ),
      http.post('http://localhost:8000/me/staff/activities/:activityId/checkins/scan', async ({ request }) => {
        scannedPayload = ((await request.json()) as { qr_payload: string }).qr_payload;
        return HttpResponse.json({ status: 'checked_in', traveler_name: 'Ana Silva', scan_number: 1, max_checkins: 1 });
      })
    );
    renderStaff();
    await user.click(await screen.findByText('Day 1 — Arrival'));
    await openActivity(user);

    await user.click(await screen.findByRole('button', { name: /check in ana silva/i }));
    expect(scannedPayload).toBeNull();
    await user.click(await screen.findByRole('button', { name: /confirm check-in/i }));

    await waitFor(() => expect(scannedPayload).toBe('qr-t-ana'));
    expect(await screen.findByText(/ana silva — check-in 1 of 1/i)).toBeInTheDocument();
    await waitFor(() => {
      const row = screen.getByText('Ana Silva', { selector: 'li p' }).closest('li') as HTMLElement;
      expect(row).toHaveTextContent('Done');
    });
    expect(scannerStart).not.toHaveBeenCalled();
  });

  test('scans with the camera only when asked and confirms before check-in', async () => {
    const user = userEvent.setup();
    let previewCalls = 0;
    let checkinPayload: string | null = null;
    server.use(
      http.post('http://localhost:8000/me/staff/activities/:activityId/checkins/preview', () => {
        previewCalls += 1;
        return HttpResponse.json({ status: 'ready_to_check_in', traveler_name: 'Ana Silva', scan_number: 1, max_checkins: 1 });
      }),
      http.post('http://localhost:8000/me/staff/activities/:activityId/checkins/scan', async ({ request }) => {
        checkinPayload = ((await request.json()) as { qr_payload: string }).qr_payload;
        return HttpResponse.json({ status: 'checked_in', traveler_name: 'Ana Silva', scan_number: 1, max_checkins: 1 });
      })
    );
    renderStaff();
    await user.click(await screen.findByText('Day 1 — Arrival'));
    await openActivity(user);

    await user.click(screen.getByRole('button', { name: /scan with camera/i }));
    await waitFor(() => expect(scannerStart).toHaveBeenCalled());

    act(() => { qrSuccess?.('qr-token-123'); });
    await screen.findByRole('button', { name: /confirm check-in/i });
    expect(checkinPayload).toBeNull();
    await user.click(screen.getByRole('button', { name: /confirm check-in/i }));
    await waitFor(() => expect(checkinPayload).toBe('qr-token-123'));
    await screen.findByText(/check-in 1 of 1/i);

    // The camera keeps seeing the same QR: it must not start a new check-in.
    act(() => { qrSuccess?.('qr-token-123'); });
    await new Promise(resolve => setTimeout(resolve, 50));
    expect(previewCalls).toBe(1);
  });

  test('explains when the next check-in step is not available yet', async () => {
    const user = userEvent.setup();
    server.use(
      http.post('http://localhost:8000/me/staff/activities/:activityId/checkins/preview', () =>
        HttpResponse.json({
          status: 'recently_checked_in', traveler_name: 'Ana Silva',
          scan_number: 1, max_checkins: 2, retry_after_seconds: 42,
        })
      )
    );
    renderStaff();
    await user.click(await screen.findByText('Day 1 — Arrival'));
    await openActivity(user);

    await user.click(await screen.findByRole('button', { name: /check in ana silva/i }));

    expect(await screen.findByText(/ana silva was just checked in/i)).toBeInTheDocument();
    expect(screen.getByText(/next check-in available in 42 s/i)).toBeInTheDocument();
  });

  test('shows who already checked the traveler in', async () => {
    const user = userEvent.setup();
    server.use(
      http.post('http://localhost:8000/me/staff/activities/:activityId/checkins/preview', () =>
        HttpResponse.json({
          status: 'already_checked_in', traveler_name: 'Ana Silva',
          scanned_by_name: 'Marcelo Staff', checked_in_at: '2026-07-01T14:30:00Z', max_checkins: 1,
        })
      )
    );
    renderStaff();
    await user.click(await screen.findByText('Day 1 — Arrival'));
    await openActivity(user);

    await user.click(await screen.findByRole('button', { name: /check in ana silva/i }));

    expect(await screen.findByText(/ana silva already completed all/i)).toBeInTheDocument();
    expect(screen.getByText(/Marcelo Staff/)).toBeInTheDocument();
  });

  test('clears the previous result when a later scan fails', async () => {
    const user = userEvent.setup();
    let previewCalls = 0;
    server.use(
      http.post('http://localhost:8000/me/staff/activities/:activityId/checkins/preview', () => {
        previewCalls += 1;
        return previewCalls === 1
          ? HttpResponse.json({ status: 'ready_to_check_in', traveler_name: 'Ana Silva', scan_number: 1, max_checkins: 1 })
          : HttpResponse.json({ detail: 'Invalid QR payload' }, { status: 400 });
      }),
      http.post('http://localhost:8000/me/staff/activities/:activityId/checkins/scan', () =>
        HttpResponse.json({ status: 'checked_in', traveler_name: 'Ana Silva', scan_number: 1, max_checkins: 1 })
      )
    );
    renderStaff();
    await user.click(await screen.findByText('Day 1 — Arrival'));
    await openActivity(user);
    await user.click(screen.getByRole('button', { name: /scan with camera/i }));
    await waitFor(() => expect(scannerStart).toHaveBeenCalled());

    act(() => { qrSuccess?.('qr-token-123'); });
    await user.click(await screen.findByRole('button', { name: /confirm check-in/i }));
    await screen.findByText(/check-in 1 of 1/i);

    act(() => { qrSuccess?.('bad-token'); });

    expect(await screen.findByText(/invalid qr payload/i)).toBeInTheDocument();
    expect(screen.queryByText(/check-in 1 of 1/i)).not.toBeInTheDocument();
  });

  test('lists where each traveler is in the journey with their last check-in', async () => {
    const user = userEvent.setup();
    server.use(
      http.get('http://localhost:8000/me/staff/travelers', () =>
        HttpResponse.json({
          trip_mode: 'in-trip',
          travelers: [
            {
              id: 'tt-1',
              name: 'Ana Silva',
              phone: '+5511999000001',
              current_phase: { id: 'day-2', title: 'Day 2', subtitle: 'Paraty', phase_type: 'in-trip' },
              pending_pre_trip: 2,
              last_checkin: { activity_name: 'Boat tour', day_title: 'Day 2', checked_in_at: '2026-07-02T13:00:00Z' },
            },
            {
              id: 'tt-2',
              name: 'Bruno Costa',
              phone: '+5511999000002',
              current_phase: { id: 'day-2', title: 'Day 2', subtitle: 'Paraty', phase_type: 'in-trip' },
              pending_pre_trip: 0,
              last_checkin: null,
            },
          ],
        })
      )
    );
    render(
      <AuthProvider>
        <StaffScreen onSwitchToTravelerView={() => {}} />
      </AuthProvider>
    );

    await user.click(screen.getByRole('button', { name: /travelers/i }));

    const ana = (await screen.findByText('Ana Silva')).closest('li') as HTMLElement;
    expect(ana).toHaveTextContent('Day 2 — Paraty');
    expect(ana).toHaveTextContent('2 pending pre-trip');
    expect(ana).toHaveTextContent(/Last check-in: Boat tour · Day 2/);
    const bruno = screen.getByText('Bruno Costa').closest('li') as HTMLElement;
    expect(bruno).toHaveTextContent('No check-ins yet');
    expect(bruno).not.toHaveTextContent(/pending/i);

    await user.type(screen.getByPlaceholderText(/search traveler/i), 'bru');
    expect(screen.queryByText('Ana Silva')).not.toBeInTheDocument();
    expect(screen.getByText('Bruno Costa')).toBeInTheDocument();
  });

  test('does not show a global QR Scan tab', async () => {
    render(
      <AuthProvider>
        <StaffScreen onSwitchToTravelerView={() => {}} />
      </AuthProvider>
    );

    await screen.findByText('Day 1 — Arrival');

    expect(screen.queryByRole('button', { name: /qr scan/i })).not.toBeInTheDocument();
  });

  test('offers Trocar de viagem in the staff header', async () => {
    render(
      <AuthProvider>
        <StaffScreen onSwitchToTravelerView={() => {}} />
      </AuthProvider>
    );

    expect(await screen.findByRole('button', { name: /trocar de viagem/i })).toBeInTheDocument();
  });

  test('hides Trocar de viagem in the staff header when only one trip is eligible', async () => {
    const stored = JSON.parse(localStorage.getItem('parrot_user')!);
    localStorage.setItem('parrot_user', JSON.stringify({ ...stored, canSwitchTrips: false }));

    render(
      <AuthProvider>
        <StaffScreen onSwitchToTravelerView={() => {}} />
      </AuthProvider>
    );

    await screen.findByText(/hi, marcelo/i);
    expect(screen.queryByRole('button', { name: /trocar de viagem/i })).not.toBeInTheDocument();
  });

  test('selecting a traveler-role trip leaves staff UI and enters traveler UI', async () => {
    setUpStaffSwitcherSession();
    window.history.pushState({}, '', '/');
    setUpStaffSwitcherAppHandlers();
    server.use(
      http.get('http://localhost:8000/auth/trips', () =>
        HttpResponse.json({ trips: [STAFF_TRIP_ONE, TRAVELER_TRIP] })
      ),
      http.post('http://localhost:8000/auth/select-trip', () =>
        HttpResponse.json({
          status: 'trip_selected',
          user_id: 'staff-1',
          phone: '+5511888000001',
          name: 'Marcelo Staff',
          role: 'traveler',
          message: 'Login successful',
          access_token: 'tok-traveler',
          active_trip: TRAVELER_TRIP,
        })
      )
    );

    render(<App />);

    await userEvent.click(await screen.findByRole('button', { name: /trocar de viagem/i }));
    await screen.findByText('Escolha sua viagem');
    await userEvent.click(screen.getByText('Traveler Trip').closest('button')!);

    await waitFor(() => {
      expect(screen.getByText('Trip Progress')).toBeInTheDocument();
    });
    expect(screen.queryByText('Hi, Marcelo 👋')).not.toBeInTheDocument();
  });

  test('recovers a revoked staff role by reselecting the same trip as traveler', async () => {
    setUpStaffSwitcherSession();
    window.history.pushState({}, '', '/');
    setUpStaffSwitcherAppHandlers();
    const sameTripAsTraveler: TripChoice = { ...STAFF_TRIP_ONE, role: 'traveler' };
    server.use(
      http.get('http://localhost:8000/me/staff/trip', () =>
        HttpResponse.json({ detail: 'Staff access required for this trip' }, { status: 403 })
      ),
      http.get('http://localhost:8000/me/staff/trip/contacts', () =>
        HttpResponse.json({ detail: 'Staff access required for this trip' }, { status: 403 })
      ),
      http.get('http://localhost:8000/auth/trips', () =>
        HttpResponse.json({ trips: [sameTripAsTraveler] })
      ),
      http.post('http://localhost:8000/auth/select-trip', () =>
        HttpResponse.json({
          status: 'trip_selected',
          user_id: 'staff-1',
          phone: '+5511888000001',
          name: 'Marcelo Staff',
          role: 'traveler',
          message: 'Login successful',
          access_token: 'tok-traveler-same-trip',
          active_trip: sameTripAsTraveler,
          can_switch_trips: false,
        })
      )
    );

    render(<App />);

    await waitFor(() => expect(screen.getByText('Trip Progress')).toBeInTheDocument());
    expect(screen.queryByText('Hi, Marcelo 👋')).not.toBeInTheDocument();
    expect(JSON.parse(localStorage.getItem('parrot_user')!)).toMatchObject({
      role: 'traveler',
      tripId: 'trip-staff-1',
      token: 'tok-traveler-same-trip',
    });
  });

  test('selecting a staff-role trip keeps the staff UI', async () => {
    setUpStaffSwitcherSession();
    window.history.pushState({}, '', '/');
    setUpStaffSwitcherAppHandlers();
    server.use(
      http.get('http://localhost:8000/auth/trips', () =>
        HttpResponse.json({ trips: [STAFF_TRIP_ONE, STAFF_TRIP_TWO] })
      ),
      http.post('http://localhost:8000/auth/select-trip', () =>
        HttpResponse.json({
          status: 'trip_selected',
          user_id: 'staff-1',
          phone: '+5511888000001',
          name: 'Marcelo Staff',
          role: 'staff',
          message: 'Login successful',
          access_token: 'tok-staff-2',
          active_trip: STAFF_TRIP_TWO,
        })
      )
    );

    render(<App />);

    await screen.findByText('Staff Trip One');
    await userEvent.click(await screen.findByRole('button', { name: /trocar de viagem/i }));
    await screen.findByText('Escolha sua viagem');
    await userEvent.click(screen.getByText('Staff Trip Two').closest('button')!);

    await waitFor(() => {
      expect(screen.getByText('Staff Trip Two')).toBeInTheDocument();
    });
    expect(screen.getByText('Hi, Marcelo 👋')).toBeInTheDocument();
  });

  test('resets a staff traveler preview when switching to a different staff trip', async () => {
    setUpStaffSwitcherSession();
    window.history.pushState({}, '', '/');
    setUpStaffSwitcherAppHandlers();
    server.use(
      http.get('http://localhost:8000/auth/trips', () =>
        HttpResponse.json({ trips: [STAFF_TRIP_ONE, STAFF_TRIP_TWO] })
      ),
      http.post('http://localhost:8000/auth/select-trip', () =>
        HttpResponse.json({
          status: 'trip_selected',
          user_id: 'staff-1',
          phone: '+5511888000001',
          name: 'Marcelo Staff',
          role: 'staff',
          message: 'Login successful',
          access_token: 'tok-staff-2',
          active_trip: STAFF_TRIP_TWO,
        })
      )
    );

    render(<App />);

    // Preview the traveler view on the current staff trip first.
    await userEvent.click(await screen.findByRole('button', { name: /traveler view/i }));
    await screen.findByText('Trip Progress');

    // Switch trips while previewing as traveler — the profile screen still
    // offers Trocar de viagem.
    await userEvent.click(screen.getByText('My Profile', { selector: 'span' }).closest('button')!);
    await screen.findByRole('heading', { name: 'My Profile' });
    await userEvent.click(await screen.findByRole('button', { name: /trocar de viagem/i }));
    await screen.findByText('Escolha sua viagem');
    await userEvent.click(screen.getByText('Staff Trip Two').closest('button')!);

    // Landing on a different staff-role trip must show the staff UI, not a
    // carried-over traveler preview.
    await waitFor(() => {
      expect(screen.getByText('Hi, Marcelo 👋')).toBeInTheDocument();
    });
    expect(screen.queryByText('Trip Progress')).not.toBeInTheDocument();
  });
});
