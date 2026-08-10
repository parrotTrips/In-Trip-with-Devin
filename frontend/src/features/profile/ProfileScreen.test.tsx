import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { http, HttpResponse } from 'msw';
import { MemoryRouter } from 'react-router-dom';

import { AuthProvider } from '../../app/providers/AuthProvider';
import { server } from '../../test/server';
import ProfileScreen from './pages/ProfileScreen';

describe('ProfileScreen', () => {
  test('loads and saves the profile data', async () => {
    let savedPayload: Record<string, unknown> | null = null;

    localStorage.setItem(
      'parrot_user',
      JSON.stringify({ userId: 1, phone: '+15550000001', name: 'Alice' })
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
    const packageTransferLink = screen.getByRole('link', { name: /transfer or cancel your package/i });
    expect(packageTransferLink).toHaveAttribute(
      'href',
      'https://package-transfer-116789457910.southamerica-east1.run.app'
    );

    await userEvent.clear(preferredNameInput);
    await userEvent.type(preferredNameInput, 'Bea');
    await userEvent.click(screen.getByRole('button', { name: /save profile/i }));

    await waitFor(() => {
      expect(savedPayload).toMatchObject({
        preferred_name: 'Bea',
        email: 'alice@example.com',
      });
    });
  });
});
