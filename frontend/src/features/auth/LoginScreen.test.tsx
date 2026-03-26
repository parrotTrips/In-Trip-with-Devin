import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { http, HttpResponse } from 'msw';

import { AuthProvider } from '../../app/providers/AuthProvider';
import { server } from '../../test/server';
import LoginScreen from './pages/LoginScreen';

describe('LoginScreen', () => {
  test('submits the full phone number when requesting an OTP', async () => {
    let requestedPhone = '';

    server.use(
      http.post('http://localhost:8000/auth/request-otp', async ({ request }) => {
        const body = await request.json();
        requestedPhone = String((body as { phone: string }).phone);
        return HttpResponse.json({ message: 'OTP sent successfully' });
      })
    );

    localStorage.removeItem('parrot_user');
    render(
      <AuthProvider>
        <LoginScreen />
      </AuthProvider>
    );

    await userEvent.type(screen.getByPlaceholderText('Phone number'), '5551234567');
    await userEvent.click(screen.getByRole('button', { name: /send whatsapp code/i }));

    await waitFor(() => {
      expect(requestedPhone).toBe('+15551234567');
    });
    expect(screen.getByText('Verification Code')).toBeInTheDocument();
  });
});
