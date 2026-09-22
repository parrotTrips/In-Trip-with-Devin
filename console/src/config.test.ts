import { expect, test } from 'vitest';

import { validateConfig } from './config';

const validEnv = {
  VITE_API_URL: 'https://api.example.com',
  VITE_GOOGLE_CLIENT_ID: '123-example.apps.googleusercontent.com',
  VITE_ALLOWED_EMAIL_DOMAIN: 'parrottrips.com',
  VITE_ENABLE_CONSOLE_LOCAL: 'false',
};

test('accepts complete production configuration', () => {
  expect(validateConfig(validEnv, false).ok).toBe(true);
});

test.each(['VITE_API_URL', 'VITE_GOOGLE_CLIENT_ID', 'VITE_ALLOWED_EMAIL_DOMAIN'])(
  'blocks production when %s is missing',
  key => expect(validateConfig({ ...validEnv, [key]: '' }, false).ok).toBe(false),
);

test('rejects malformed API URL and Google client ID', () => {
  expect(validateConfig({ ...validEnv, VITE_API_URL: 'not-a-url' }, false).ok).toBe(false);
  expect(validateConfig({ ...validEnv, VITE_GOOGLE_CLIENT_ID: 'wrong' }, false).ok).toBe(false);
});

test('local bypass requires both Vite development mode and its explicit flag', () => {
  const env = { ...validEnv, VITE_GOOGLE_CLIENT_ID: '', VITE_ENABLE_CONSOLE_LOCAL: 'true' };
  expect(validateConfig(env, true)).toMatchObject({ ok: true, value: { localBypass: true } });
  expect(validateConfig(env, false).ok).toBe(false);
});
