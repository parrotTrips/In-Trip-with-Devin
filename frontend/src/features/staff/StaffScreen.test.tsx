import { act, render, screen, waitFor } from '@testing-library/react';
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
    })
  );
}

describe('StaffScreen', () => {
  beforeEach(() => {
    qrSuccess = null;
    scannerStart.mockClear();
    scannerStop.mockClear();
    scannerClear.mockClear();
    localStorage.setItem(
      'parrot_user',
      JSON.stringify({ userId: 'staff-1', phone: '+5511888000001', name: 'Marcelo Staff', token: 'tok', role: 'staff' })
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
  });

  test('shows current staff tasks inside expanded activity', async () => {
    const user = userEvent.setup();
    render(
      <AuthProvider>
        <StaffScreen onSwitchToTravelerView={() => {}} />
      </AuthProvider>
    );

    await user.click(await screen.findByText('Day 1 — Arrival'));
    await user.click(await screen.findByText('Airport Transfer'));

    await waitFor(() => {
      expect(screen.getByText('My tasks')).toBeInTheDocument();
    });
    expect(screen.getByText('Coordenar van 1')).toBeInTheDocument();
    expect(screen.getByText('Receber viajantes no aeroporto')).toBeInTheDocument();
  });

  test('shows activity check-in counter and scanner entry inside expanded activity', async () => {
    const user = userEvent.setup();
    render(
      <AuthProvider>
        <StaffScreen onSwitchToTravelerView={() => {}} />
      </AuthProvider>
    );

    await user.click(await screen.findByText('Day 1 — Arrival'));

    expect(screen.getByText('0 / 12 scanned')).toBeInTheDocument();

    await user.click(screen.getByText('Airport Transfer'));

    expect(screen.getByRole('button', { name: /^scan$/i })).toBeInTheDocument();
  });

  test('opens camera scanner inside the activity and waits for staff confirmation before check-in', async () => {
    const user = userEvent.setup();
    let scannedActivityId: string | null = null;
    let scannedPayload: string | null = null;
    let checkinPayload: string | null = null;

    server.use(
      http.post('http://localhost:8000/me/staff/activities/:activityId/checkins/preview', async ({ params, request }) => {
        scannedActivityId = String(params.activityId);
        const body = await request.json() as { qr_payload: string };
        scannedPayload = body.qr_payload;
        return HttpResponse.json({
          status: 'ready_to_check_in',
          traveler_name: 'Ana Silva',
          scan_number: 1,
          max_checkins: 1,
        });
      }),
      http.post('http://localhost:8000/me/staff/activities/:activityId/checkins/scan', async ({ params, request }) => {
        expect(String(params.activityId)).toBe('activity-1');
        const body = await request.json() as { qr_payload: string };
        checkinPayload = body.qr_payload;
        return HttpResponse.json({ status: 'checked_in', traveler_name: 'Ana Silva', scan_number: 1, max_checkins: 1 });
      })
    );

    render(
      <AuthProvider>
        <StaffScreen onSwitchToTravelerView={() => {}} />
      </AuthProvider>
    );

    await user.click(await screen.findByText('Day 1 — Arrival'));
    await user.click(screen.getByText('Airport Transfer'));
    await user.click(screen.getByRole('button', { name: /^scan$/i }));

    const scannerHeading = await screen.findByText(/camera scanner/i);
    expect(scannerHeading.compareDocumentPosition(screen.getByText(/step 1/i))).toBe(Node.DOCUMENT_POSITION_FOLLOWING);
    await waitFor(() => {
      expect(scannerStart).toHaveBeenCalled();
    });

    act(() => {
      qrSuccess?.('qr-token-123');
    });

    await waitFor(() => {
      expect(screen.getByText(/ana silva/i)).toBeInTheDocument();
    });
    expect(scannedActivityId).toBe('activity-1');
    expect(scannedPayload).toBe('qr-token-123');
    expect(checkinPayload).toBeNull();

    await user.click(screen.getByRole('button', { name: /confirm check-in/i }));

    await waitFor(() => {
      expect(screen.getByText(/scan 1 of 1/i)).toBeInTheDocument();
      expect(checkinPayload).toBe('qr-token-123');
    });
  });

  test('shows duplicate check-in message with scanner metadata', async () => {
    const user = userEvent.setup();

    server.use(
      http.post('http://localhost:8000/me/staff/activities/:activityId/checkins/preview', () =>
        HttpResponse.json({
          status: 'already_checked_in',
          traveler_name: 'Ana Silva',
          scanned_by_name: 'Marcelo Staff',
          checked_in_at: '2026-07-01T14:30:00Z',
        })
      )
    );

    render(
      <AuthProvider>
        <StaffScreen onSwitchToTravelerView={() => {}} />
      </AuthProvider>
    );

    await user.click(await screen.findByText('Day 1 — Arrival'));
    await user.click(screen.getByText('Airport Transfer'));
    await user.click(screen.getByRole('button', { name: /^scan$/i }));

    await waitFor(() => {
      expect(scannerStart).toHaveBeenCalled();
    });
    act(() => {
      qrSuccess?.('qr-token-123');
    });

    await waitFor(() => {
      expect(screen.getByText(/ana silva already completed all/i)).toBeInTheDocument();
    });
    expect(screen.getByText(/Marcelo Staff/)).toBeInTheDocument();
    expect(screen.getByText('0 / 12 scanned')).toBeInTheDocument();
  });

  test('clears previous scan result when a later scan fails', async () => {
    const user = userEvent.setup();
    let requestCount = 0;

    server.use(
      http.post('http://localhost:8000/me/staff/activities/:activityId/checkins/preview', () => {
        requestCount += 1;
        if (requestCount === 1) {
          return HttpResponse.json({
            status: 'ready_to_check_in',
            traveler_name: 'Ana Silva',
            scan_number: 1,
            max_checkins: 1,
          });
        }

        return HttpResponse.json({ detail: 'Invalid QR payload' }, { status: 400 });
      }),
      http.post('http://localhost:8000/me/staff/activities/:activityId/checkins/scan', () =>
        HttpResponse.json({ status: 'checked_in', traveler_name: 'Ana Silva', scan_number: 1, max_checkins: 1 })
      )
    );

    render(
      <AuthProvider>
        <StaffScreen onSwitchToTravelerView={() => {}} />
      </AuthProvider>
    );

    await user.click(await screen.findByText('Day 1 — Arrival'));
    await user.click(screen.getByText('Airport Transfer'));
    await user.click(screen.getByRole('button', { name: /^scan$/i }));

    await waitFor(() => {
      expect(scannerStart).toHaveBeenCalled();
    });
    act(() => {
      qrSuccess?.('qr-token-123');
    });
    await screen.findByText(/ready for scan 1 of 1/i);
    await user.click(screen.getByRole('button', { name: /confirm check-in/i }));
    await screen.findByText(/scan 1 of 1/i);

    act(() => {
      qrSuccess?.('bad-token');
    });

    await waitFor(() => {
      expect(screen.getByText(/invalid qr payload/i)).toBeInTheDocument();
    });
    expect(screen.queryByText(/scan 1 of 1/i)).not.toBeInTheDocument();
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

  test('can select a traveler by name and confirm check-in', async () => {
    const user = userEvent.setup();
    let previewPayload: string | null = null;
    let scannedPayload: string | null = null;

    server.use(
      http.get('http://localhost:8000/me/staff/activities/:activityId/travelers', () =>
        HttpResponse.json({ travelers: [{ id: 'traveler-1', name: 'Ana Silva', qr_payload: 'manual-token-123' }] })
      ),
      http.post('http://localhost:8000/me/staff/activities/:activityId/checkins/preview', async ({ request }) => {
        const body = await request.json() as { qr_payload: string };
        previewPayload = body.qr_payload;
        return HttpResponse.json({
          status: 'ready_to_check_in',
          traveler_name: 'Ana Silva',
          scan_number: 1,
          max_checkins: 1,
        });
      }),
      http.post('http://localhost:8000/me/staff/activities/:activityId/checkins/scan', async ({ request }) => {
        const body = await request.json() as { qr_payload: string };
        scannedPayload = body.qr_payload;
        return HttpResponse.json({ status: 'checked_in', traveler_name: 'Ana Silva', scan_number: 1, max_checkins: 1 });
      })
    );

    render(
      <AuthProvider>
        <StaffScreen onSwitchToTravelerView={() => {}} />
      </AuthProvider>
    );

    await user.click(await screen.findByText('Day 1 — Arrival'));
    await user.click(screen.getByText('Airport Transfer'));
    await user.click(screen.getByRole('button', { name: /^scan$/i }));
    await user.click(await screen.findByRole('button', { name: /select by name/i }));
    await user.click(await screen.findByRole('button', { name: /ana silva select/i }));

    await waitFor(() => {
      expect(previewPayload).toBe('manual-token-123');
    });
    expect(scannedPayload).toBeNull();

    await user.click(screen.getByRole('button', { name: /confirm check-in/i }));

    await waitFor(() => {
      expect(screen.getByText(/scan 1 of 1/i)).toBeInTheDocument();
    });
    expect(scannedPayload).toBe('manual-token-123');
  });

  test('offers Trocar de viagem in the staff header', async () => {
    render(
      <AuthProvider>
        <StaffScreen onSwitchToTravelerView={() => {}} />
      </AuthProvider>
    );

    expect(await screen.findByRole('button', { name: /trocar de viagem/i })).toBeInTheDocument();
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
