import { render, screen, waitFor } from '@testing-library/react';
import { http, HttpResponse } from 'msw';
import { MemoryRouter, Route, Routes } from 'react-router-dom';

import { AuthProvider } from '../../../app/providers/AuthProvider';
import { TripProvider } from '../../../app/providers/TripProvider';
import { server } from '../../../test/server';
import QrCodeScreen from './QrCodeScreen';

describe('QrCodeScreen', () => {
  beforeEach(() => {
    localStorage.setItem(
      'parrot_user',
      JSON.stringify({
        userId: 'traveler-001',
        phone: '+15550000001',
        name: 'Alice Traveler',
        token: 'tok',
        role: 'traveler',
      })
    );

    server.use(
      http.get('http://localhost:8000/me/trip', () =>
        HttpResponse.json({
          trip: {
            wetravel_trip_uuid: 'test-trip-001',
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
          wetravel_trip_uuid: 'test-trip-001',
          phases: [],
          ideal_pace_phase_id: null,
        })
      ),
      http.get('http://localhost:8000/me/trip/travelers', () =>
        HttpResponse.json({ travelers: [] })
      ),
      http.get('http://localhost:8000/me/qr-code', () =>
        HttpResponse.json({
          trip_uuid: 'test-trip-001',
          trip_traveler_id: 'trip-traveler-001',
          qr_payload: 'parrot-trip-checkin:test-trip-001:trip-traveler-001',
        })
      )
    );
  });

  test('shows the traveler qr code in its own tab screen', async () => {
    render(
      <MemoryRouter initialEntries={['/qr-code']}>
        <AuthProvider>
          <TripProvider>
            <Routes>
              <Route path="/qr-code" element={<QrCodeScreen />} />
            </Routes>
          </TripProvider>
        </AuthProvider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: 'My QR Code' })).toBeInTheDocument();
    });
    expect(screen.getByLabelText('Traveler check-in QR code')).toBeInTheDocument();
    expect(screen.getByText('Alice Traveler')).toBeInTheDocument();
  });
});
