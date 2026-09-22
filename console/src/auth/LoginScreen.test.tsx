import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, expect, test, vi } from 'vitest';

import type { ConsoleConfig } from '../config';
import { GOOGLE_CREDENTIAL_KEY } from './google-session';
import { AuthProvider } from './AuthProvider';
import LoginScreen from './LoginScreen';

const credential = (() => {
  const payload = btoa(JSON.stringify({
    sub: 'u1', email: 'person@parrottrips.com', exp: Math.floor(Date.now() / 1000) + 3600,
  })).replace(/\+/g, '-').replace(/\//g, '_').replace(/=/g, '');
  return `header.${payload}.signature`;
})();

vi.mock('@react-oauth/google', () => ({
  GoogleLogin: ({ onSuccess, hosted_domain }: {
    onSuccess: (response: { credential: string }) => void;
    hosted_domain: string;
  }) => (
    <button data-domain={hosted_domain} onClick={() => onSuccess({ credential })}>
      Entrar com Google
    </button>
  ),
  googleLogout: vi.fn(),
}));

const config: ConsoleConfig = {
  apiUrl: 'https://api.example.com',
  googleClientId: 'client.apps.googleusercontent.com',
  allowedEmailDomain: 'parrottrips.com',
  localBypass: false,
};

beforeEach(() => {
  localStorage.clear();
  sessionStorage.clear();
});

test('uses Google login with the corporate domain hint and stores the credential', async () => {
  render(<AuthProvider config={config}><LoginScreen /></AuthProvider>);

  const button = screen.getByRole('button', { name: 'Entrar com Google' });
  expect(button).toHaveAttribute('data-domain', 'parrottrips.com');
  await userEvent.click(button);

  expect(await screen.findByText(/Bem-vindo/)).toBeInTheDocument();
  expect(sessionStorage.getItem(GOOGLE_CREDENTIAL_KEY)).toBe(credential);
  expect(localStorage.length).toBe(0);
});
