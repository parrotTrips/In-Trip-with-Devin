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
    const preferredNameInput = await screen.findByLabelText('Preferred Name');
    expect(preferredNameInput).toHaveValue('Alice');

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
