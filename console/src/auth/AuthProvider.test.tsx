import { render, screen } from '@testing-library/react';
import { beforeEach, expect, test } from 'vitest';

import type { ConsoleConfig } from '../config';
import { GOOGLE_CREDENTIAL_KEY } from './google-session';
import { AuthProvider } from './AuthProvider';
import { useAuth } from './auth-context';

const config: ConsoleConfig = {
  apiUrl: 'https://api.example.com',
  googleClientId: 'client.apps.googleusercontent.com',
  allowedEmailDomain: 'parrottrips.com',
  localBypass: false,
};

function fakeJwt() {
  const payload = btoa(JSON.stringify({
    sub: 'u1', email: 'person@parrottrips.com', exp: Math.floor(Date.now() / 1000) + 3600,
  })).replace(/\+/g, '-').replace(/\//g, '_').replace(/=/g, '');
  return `header.${payload}.signature`;
}

function Probe() {
  const { isLoggedIn, principal } = useAuth();
  return <p>{isLoggedIn ? `entrou:${principal?.email}` : 'deslogado'}</p>;
}

beforeEach(() => {
  localStorage.clear();
  sessionStorage.clear();
});

test('restores a valid Google session before children render', () => {
  sessionStorage.setItem(GOOGLE_CREDENTIAL_KEY, fakeJwt());
  render(<AuthProvider config={config}><Probe /></AuthProvider>);
  expect(screen.getByText('entrou:person@parrottrips.com')).toBeInTheDocument();
  expect(localStorage.length).toBe(0);
});

test('stays logged out without a credential', () => {
  render(<AuthProvider config={config}><Probe /></AuthProvider>);
  expect(screen.getByText('deslogado')).toBeInTheDocument();
});

test('local bypass logs in only when config already approved both guards', () => {
  render(<AuthProvider config={{ ...config, localBypass: true }}><Probe /></AuthProvider>);
  expect(screen.getByText('entrou:local@parrottrips.com')).toBeInTheDocument();
  expect(sessionStorage.length).toBe(0);
});
