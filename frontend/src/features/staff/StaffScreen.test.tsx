import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { http, HttpResponse } from 'msw';

import { AuthProvider } from '../../app/providers/AuthProvider';
import { server } from '../../test/server';
import StaffScreen from './pages/StaffScreen';

describe('StaffScreen', () => {
  beforeEach(() => {
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
});
