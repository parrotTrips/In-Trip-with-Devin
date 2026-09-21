import { render, screen } from '@testing-library/react';
import { afterEach, beforeEach, expect, test, vi } from 'vitest';

import { AuthProvider } from './AuthProvider';
import { useAuth } from './auth-context';

function Probe() {
  const { isLoggedIn, user } = useAuth();
  return <p>{isLoggedIn ? `entrou:${user?.role}` : 'deslogado'}</p>;
}

beforeEach(() => {
  localStorage.clear();
  vi.unstubAllEnvs();
});

afterEach(() => {
  localStorage.clear();
  vi.unstubAllEnvs();
});

test('stays logged out when the dev flag is absent', () => {
  render(<AuthProvider><Probe /></AuthProvider>);
  expect(screen.getByText('deslogado')).toBeInTheDocument();
});

test('auto-logs in as admin when the dev flag is set', () => {
  vi.stubEnv('VITE_DEV_AUTO_LOGIN', 'true');
  vi.stubEnv('VITE_DEV_TOKEN', 'dev-token');

  render(<AuthProvider><Probe /></AuthProvider>);

  expect(screen.getByText('entrou:admin')).toBeInTheDocument();
});

test('a stored user wins over the dev flag', () => {
  vi.stubEnv('VITE_DEV_AUTO_LOGIN', 'true');
  vi.stubEnv('VITE_DEV_TOKEN', 'dev-token');
  localStorage.setItem('parrot_console_user', JSON.stringify({
    userId: 'real', phone: '+5511000000000', name: 'Real', token: 'real-token', role: 'admin',
  }));

  render(<AuthProvider><Probe /></AuthProvider>);

  expect(screen.getByText('entrou:admin')).toBeInTheDocument();
  expect(JSON.parse(localStorage.getItem('parrot_console_user')!).token).toBe('real-token');
});
