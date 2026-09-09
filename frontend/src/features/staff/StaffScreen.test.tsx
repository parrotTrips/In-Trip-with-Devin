import { act, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { http, HttpResponse } from 'msw';
import { vi } from 'vitest';

import { AuthProvider } from '../../app/providers/AuthProvider';
import { server } from '../../test/server';
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
});
