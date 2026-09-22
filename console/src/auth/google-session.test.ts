import { beforeEach, expect, test } from 'vitest';

import {
  GOOGLE_CREDENTIAL_KEY,
  acceptCredential,
  clearCredentialIfCurrent,
  currentCredential,
  restoreCredential,
} from './google-session';

function encode(value: object) {
  return btoa(JSON.stringify(value)).replace(/\+/g, '-').replace(/\//g, '_').replace(/=/g, '');
}

function fakeJwt(payload: object) {
  return `${encode({ alg: 'none' })}.${encode(payload)}.`;
}

function validToken(overrides: object = {}) {
  return fakeJwt({
    sub: 'google-user', email: 'person@parrottrips.com',
    exp: Math.floor(Date.now() / 1000) + 3600, ...overrides,
  });
}

beforeEach(() => {
  localStorage.clear();
  sessionStorage.clear();
});

test('accepts and restores a valid credential from sessionStorage only', () => {
  const token = validToken();
  expect(acceptCredential(token, 'parrottrips.com')?.email).toBe('person@parrottrips.com');
  expect(sessionStorage.getItem(GOOGLE_CREDENTIAL_KEY)).toBe(token);
  expect(localStorage.length).toBe(0);
  expect(restoreCredential('parrottrips.com')?.sub).toBe('google-user');
});

test.each([
  ['malformed', 'not-a-jwt'],
  ['expired', validToken({ exp: Math.floor(Date.now() / 1000) - 1 })],
  ['wrong domain', validToken({ email: 'person@example.com' })],
  ['missing sub', validToken({ sub: '' })],
])('rejects %s credentials', (_label, token) => {
  sessionStorage.setItem(GOOGLE_CREDENTIAL_KEY, token);
  expect(restoreCredential('parrottrips.com')).toBeNull();
  expect(sessionStorage.getItem(GOOGLE_CREDENTIAL_KEY)).toBeNull();
});

test('an old request cannot clear a newer credential', () => {
  const oldToken = validToken({ sub: 'old' });
  const newToken = validToken({ sub: 'new' });
  acceptCredential(oldToken, 'parrottrips.com');
  acceptCredential(newToken, 'parrottrips.com');

  expect(clearCredentialIfCurrent(oldToken)).toBe(false);
  expect(currentCredential()).toBe(newToken);
  expect(clearCredentialIfCurrent(newToken)).toBe(true);
  expect(currentCredential()).toBeNull();
});
