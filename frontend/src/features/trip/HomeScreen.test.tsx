import { render, screen } from '@testing-library/react';
import { http, HttpResponse } from 'msw';
import { MemoryRouter, Route, Routes } from 'react-router-dom';

import { AuthProvider } from '../../app/providers/AuthProvider';
import { TripProvider } from '../../app/providers/TripProvider';
import { server } from '../../test/server';
import HomeScreen from './pages/HomeScreen';

const TRIP_UUID = 'test-trip-001';
const USER_ID = 'traveler-001';

function setupHandlers() {
  server.use(
    http.get('http://localhost:8000/me/trip', () =>
      HttpResponse.json({
        trip: {
          wetravel_trip_uuid: TRIP_UUID,
          title: 'Peru Adventure',
          destination: 'Peru',
          start_date: '2026-02-27',
          end_date: '2026-03-08',
          url: null,
          service_agreement_url: null,
          trip_mode: 'pre-trip',
        },
      })
    ),
    http.get('http://localhost:8000/me/trip/phases', () =>
      HttpResponse.json({
        wetravel_trip_uuid: TRIP_UUID,
        phases: [
          {
            id: 'phase-001',
            phase_type: 'pre-trip',
            title: 'Passport',
            subtitle: null,
            icon: 'passport',
            short_description: 'Passport details',
            detailed_description: null,
            sort_order: 0,
            starts_at: null,
            is_locked_by_default: false,
            checklist_items: [],
            links: [],
          },
        ],
        ideal_pace_phase_id: null,
      })
    ),
    http.get('http://localhost:8000/me/trip/travelers', () =>
      HttpResponse.json({
        travelers: [
          {
            id: USER_ID,
            name: 'Alice Traveler',
            phone: '+15550000001',
            current_phase_id: 'phase-001',
          },
        ],
      })
    ),
  );
}

describe('HomeScreen', () => {
  beforeEach(() => {
    localStorage.setItem(
      'parrot_user',
      JSON.stringify({
        userId: USER_ID,
        phone: '+15550000001',
        name: 'Alice Traveler',
        token: 'tok',
        role: 'traveler',
      })
    );
    setupHandlers();
  });

  test('shows the traveler home without the QR code section', async () => {
    render(
      <MemoryRouter initialEntries={['/']}>
        <AuthProvider>
          <TripProvider>
            <Routes>
              <Route path="/" element={<HomeScreen />} />
            </Routes>
          </TripProvider>
        </AuthProvider>
      </MemoryRouter>
    );

    expect((await screen.findAllByText('Peru Adventure')).length).toBeGreaterThan(0);
    expect(screen.queryByRole('heading', { name: 'My QR Code' })).not.toBeInTheDocument();
  });
});
