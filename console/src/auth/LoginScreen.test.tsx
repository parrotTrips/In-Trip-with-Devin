import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, expect, test, vi } from 'vitest';

import { AuthProvider } from './AuthProvider';
import LoginScreen from './LoginScreen';

beforeEach(() => {
  localStorage.clear();
  vi.restoreAllMocks();
  // The local .env sets VITE_DEV_AUTO_LOGIN; pin it off so tests do not
  // depend on the developer's machine.
  vi.stubEnv('VITE_DEV_AUTO_LOGIN', '');
});

afterEach(() => {
  localStorage.clear();
});

function mockFetchSequence(responses: object[]) {
  const fetchMock = vi.fn();
  responses.forEach(body => {
    fetchMock.mockResolvedValueOnce({
      ok: true,
      json: async () => body,
    });
  });
  vi.stubGlobal('fetch', fetchMock);
  return fetchMock;
}

test('an admin logging in is stored', async () => {
  mockFetchSequence([
    { message: 'sent' },
    {
      user_id: 'u1', phone: '+5511999999999', name: 'Admin',
      role: 'admin', message: 'ok', access_token: 'tok',
    },
  ]);

  render(<AuthProvider><LoginScreen /></AuthProvider>);

  await userEvent.type(screen.getByLabelText('Telefone'), '5511999999999');
  await userEvent.click(screen.getByRole('button', { name: 'Enviar código' }));
  await userEvent.type(await screen.findByLabelText('Código'), '123456');
  await userEvent.click(screen.getByRole('button', { name: 'Entrar' }));

  await screen.findByText(/Bem-vindo/);
  expect(JSON.parse(localStorage.getItem('parrot_console_user')!).role).toBe('admin');
});

test('a non-admin is refused and nothing is stored', async () => {
  mockFetchSequence([
    { message: 'sent' },
    {
      user_id: 'u2', phone: '+5511888888888', name: 'Viajante',
      role: 'traveler', message: 'ok', access_token: 'tok',
    },
  ]);

  render(<AuthProvider><LoginScreen /></AuthProvider>);

  await userEvent.type(screen.getByLabelText('Telefone'), '5511888888888');
  await userEvent.click(screen.getByRole('button', { name: 'Enviar código' }));
  await userEvent.type(await screen.findByLabelText('Código'), '123456');
  await userEvent.click(screen.getByRole('button', { name: 'Entrar' }));

  expect(await screen.findByText('Esta conta não tem acesso ao console.')).toBeInTheDocument();
  expect(localStorage.getItem('parrot_console_user')).toBeNull();
});
