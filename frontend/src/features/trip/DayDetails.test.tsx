import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { http, HttpResponse } from 'msw';
import { MemoryRouter, Route, Routes } from 'react-router-dom';

import { AuthProvider } from '../../app/providers/AuthProvider';
import { TripProvider } from '../../app/providers/TripProvider';
import { server } from '../../test/server';
import DayDetails from './pages/DayDetails';

const DAY_ID = 'cccccccc-0000-0000-0000-000000000001';
const TRIP_UUID = 'test-trip-001';
const USER_ID = 'dddddddd-0000-0000-0000-000000000001';

function setupHandlers() {
  server.use(
    http.get('http://localhost:8000/me/trip', () =>
      HttpResponse.json({ trip: { wetravel_trip_uuid: TRIP_UUID, title: 'Test Trip', destination: 'Test', start_date: '2026-02-27', end_date: '2026-03-08', url: null } })
    ),
    http.get('http://localhost:8000/me/trip/phases', () =>
      HttpResponse.json({ wetravel_trip_uuid: TRIP_UUID, phases: [] })
    ),
    http.get('http://localhost:8000/me/trip/travelers', () =>
      HttpResponse.json({ travelers: [] })
    ),
    http.get(`http://localhost:8000/me/trip/phases/${DAY_ID}`, () =>
      HttpResponse.json({
        id: DAY_ID,
        phase_type: 'in-trip',
        title: 'Day 1 — Feb 27',
        subtitle: 'Arrival in Rio',
        icon: 'plane-landing',
        short_description: 'Airport pickup, Hotel Check-in',
        detailed_description: null,
        sort_order: 4,
        starts_at: '2026-02-27T00:00:00Z',
        is_locked_by_default: false,
        checklist_items: [],
        links: [],
        activities: [
          {
            id: 'act-1',
            name: 'Airport Pickup',
            activity_type: 'logistics',
            starts_at: null,
            duration_minutes: null,
            short_description: 'Pickup from airport',
            practical_info: null,
            address: 'Hotel lobby, Rio de Janeiro',
            amount_brl: null,
            sort_order: 0,
          },
          {
            id: 'act-2',
            name: 'Sunset Sailing',
            activity_type: 'optional',
            starts_at: null,
            duration_minutes: null,
            short_description: 'Optional sailing experience',
            practical_info: 'Bring sunscreen.',
            address: null,
            amount_brl: 350,
            sort_order: 1,
          },
        ],
      })
    ),
  );
}

describe('DayDetails', () => {
  beforeEach(() => {
    localStorage.setItem(
      'parrot_user',
      JSON.stringify({ userId: USER_ID, phone: '+15550000001', name: 'Alice', token: 'tok', role: 'traveler' })
    );
    setupHandlers();
  });

  test('renderiza o itinerário e o álbum do grupo', async () => {
    render(
      <MemoryRouter initialEntries={[`/day/${DAY_ID}`]}>
        <AuthProvider>
          <TripProvider>
            <Routes>
              <Route path="/day/:dayId" element={<DayDetails />} />
            </Routes>
          </TripProvider>
        </AuthProvider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText("Today's Itinerary")).toBeInTheDocument();
    });
    expect(screen.getByText('Airport Pickup')).toBeInTheDocument();
    expect(screen.getByText('Hotel lobby, Rio de Janeiro')).toBeInTheDocument();
  });

  test('shows a Google Maps link for activities with an address', async () => {
    render(
      <MemoryRouter initialEntries={[`/day/${DAY_ID}`]}>
        <AuthProvider>
          <TripProvider>
            <Routes>
              <Route path="/day/:dayId" element={<DayDetails />} />
            </Routes>
          </TripProvider>
        </AuthProvider>
      </MemoryRouter>
    );

    expect(await screen.findByText('Airport Pickup')).toBeInTheDocument();

    const mapsLink = screen.getByRole('link', { name: /maps/i });
    expect(mapsLink).toHaveAttribute(
      'href',
      `https://maps.google.com/?q=${encodeURIComponent('Hotel lobby, Rio de Janeiro')}`
    );
  });

  test('does not show prices or booking buttons for optional activities', async () => {
    render(
      <MemoryRouter initialEntries={[`/day/${DAY_ID}`]}>
        <AuthProvider>
          <TripProvider>
            <Routes>
              <Route path="/day/:dayId" element={<DayDetails />} />
            </Routes>
          </TripProvider>
        </AuthProvider>
      </MemoryRouter>
    );

    expect(await screen.findByText('Sunset Sailing')).toBeInTheDocument();
    expect(screen.queryByText(/R\$ 350/i)).not.toBeInTheDocument();

    await userEvent.click(screen.getByText('Sunset Sailing'));

    expect(await screen.findByText('Bring sunscreen.')).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /book now/i })).not.toBeInTheDocument();
    expect(screen.queryByText(/R\$ 350/i)).not.toBeInTheDocument();
  });
});
