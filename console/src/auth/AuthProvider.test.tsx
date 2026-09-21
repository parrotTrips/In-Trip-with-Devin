import { render, screen } from '@testing-library/react';
import { useEffect } from 'react';
import { afterEach, beforeEach, expect, test, vi } from 'vitest';

import { request } from '../api/client';
import { AuthProvider } from './AuthProvider';
import { useAuth } from './auth-context';

function Probe() {
  const { isLoggedIn, user } = useAuth();
  return <p>{isLoggedIn ? `entrou:${user?.role}` : 'deslogado'}</p>;
}

beforeEach(() => {
  localStorage.clear();
  vi.unstubAllEnvs();
  // The local .env sets VITE_DEV_AUTO_LOGIN; pin it off so tests do not
  // depend on the developer's machine.
  vi.stubEnv('VITE_DEV_AUTO_LOGIN', '');
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

test('the dev token replaces a stale one left in localStorage', () => {
  vi.stubEnv('VITE_DEV_AUTO_LOGIN', 'true');
  vi.stubEnv('VITE_DEV_TOKEN', 'dev-token');
  localStorage.setItem('parrot_console_user', JSON.stringify({
    userId: 'old', phone: '+5511000000000', name: 'Antigo', token: 'stale-token', role: 'admin',
  }));

  render(<AuthProvider><Probe /></AuthProvider>);

  expect(JSON.parse(localStorage.getItem('parrot_console_user')!).token).toBe('dev-token');
});

test('a stored user is kept when the dev flag is off', () => {
  localStorage.setItem('parrot_console_user', JSON.stringify({
    userId: 'real', phone: '+5511000000000', name: 'Real', token: 'real-token', role: 'admin',
  }));

  render(<AuthProvider><Probe /></AuthProvider>);

  expect(screen.getByText('entrou:admin')).toBeInTheDocument();
  expect(JSON.parse(localStorage.getItem('parrot_console_user')!).token).toBe('real-token');
});

test('the dev auto-login token reaches the HTTP client', async () => {
  vi.stubEnv('VITE_DEV_AUTO_LOGIN', 'true');
  vi.stubEnv('VITE_DEV_TOKEN', 'dev-token');
  const fetchMock = vi.fn().mockResolvedValue({ ok: true, json: async () => ({}) });
  vi.stubGlobal('fetch', fetchMock);

  render(<AuthProvider><Probe /></AuthProvider>);
  await request('/console/trips');

  expect(fetchMock.mock.calls[0][1].headers.Authorization).toBe('Bearer dev-token');
});

test('a child fetching on mount already has the token', async () => {
  vi.stubEnv('VITE_DEV_AUTO_LOGIN', 'true');
  vi.stubEnv('VITE_DEV_TOKEN', 'dev-token');
  const fetchMock = vi.fn().mockResolvedValue({ ok: true, json: async () => ({}) });
  vi.stubGlobal('fetch', fetchMock);

  // Mirrors TripsScreen: a child that fires a request from its own effect.
  // Child effects run before the parent's, which is what broke in the browser.
  function FetchesOnMount() {
    useEffect(() => { void request('/console/trips'); }, []);
    return <p>filho</p>;
  }

  render(<AuthProvider><FetchesOnMount /></AuthProvider>);
  await screen.findByText('filho');

  expect(fetchMock).toHaveBeenCalled();
  expect(fetchMock.mock.calls[0][1].headers.Authorization).toBe('Bearer dev-token');
});
