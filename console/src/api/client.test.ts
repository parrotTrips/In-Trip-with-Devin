import { beforeEach, expect, test, vi } from 'vitest';

import { acceptCredential, currentCredential } from '../auth/google-session';
import { ApiError, request } from './client';

function encode(value: object) {
  return btoa(JSON.stringify(value)).replace(/\+/g, '-').replace(/\//g, '_').replace(/=/g, '');
}

function token(sub: string) {
  return `${encode({ alg: 'none' })}.${encode({
    sub, email: 'person@parrottrips.com', exp: Math.floor(Date.now() / 1000) + 3600,
  })}.signature`;
}

function response(status: number, body: object = {}) {
  return {
    ok: status >= 200 && status < 300,
    status,
    statusText: String(status),
    json: async () => body,
  };
}

beforeEach(() => {
  sessionStorage.clear();
  localStorage.clear();
  vi.restoreAllMocks();
  vi.stubEnv('VITE_API_URL', 'https://api.example.com');
  vi.stubEnv('VITE_ALLOWED_EMAIL_DOMAIN', 'parrottrips.com');
  vi.stubEnv('VITE_ENABLE_CONSOLE_LOCAL', 'true');
});

test('adds the current Google credential as Bearer', async () => {
  const credential = token('current');
  acceptCredential(credential, 'parrottrips.com');
  const fetchMock = vi.fn().mockResolvedValue(response(200, { ok: true }));
  vi.stubGlobal('fetch', fetchMock);

  await request('/console/trips');

  expect(fetchMock.mock.calls[0][0]).toBe('https://api.example.com/console/trips');
  expect(fetchMock.mock.calls[0][1].headers.Authorization).toBe(`Bearer ${credential}`);
});

test('401 clears the credential used by that request', async () => {
  const credential = token('old');
  acceptCredential(credential, 'parrottrips.com');
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue(response(401, { detail: 'Unauthorized' })));

  await expect(request('/console/trips')).rejects.toMatchObject({ status: 401 });
  expect(currentCredential()).toBeNull();
});

test('a delayed 401 cannot clear a newer credential', async () => {
  const oldCredential = token('old');
  const newCredential = token('new');
  acceptCredential(oldCredential, 'parrottrips.com');
  let resolveRequest!: (value: object) => void;
  vi.stubGlobal('fetch', vi.fn(() => new Promise(resolve => { resolveRequest = resolve; })));

  const pending = request('/console/trips');
  acceptCredential(newCredential, 'parrottrips.com');
  resolveRequest(response(401, { detail: 'Unauthorized' }));

  await expect(pending).rejects.toMatchObject({ status: 401 });
  expect(currentCredential()).toBe(newCredential);
});

test.each([
  [403, 'Conta Google sem acesso ao console.'],
  [503, 'Autenticação do console não configurada.'],
])('%s preserves the session and exposes a useful message', async (status, message) => {
  const credential = token('current');
  acceptCredential(credential, 'parrottrips.com');
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue(response(status, { detail: 'server detail' })));

  await expect(request('/console/trips')).rejects.toMatchObject({ status, message });
  expect(currentCredential()).toBe(credential);
});

test('network errors are sanitized', async () => {
  vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new Error('secret internal network detail')));
  let caught: unknown;
  try {
    await request('/console/trips');
  } catch (error) {
    caught = error;
  }
  expect(caught).toBeInstanceOf(ApiError);
  expect((caught as Error).message).toBe('Não foi possível conectar à API.');
});
