import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, expect, test, vi } from 'vitest';

import { AuthProvider } from '../auth/AuthProvider';
import TripsScreen from './TripsScreen';

/** Datas relativas a hoje, para o teste não envelhecer.
 *
 * Formatada em horário local de propósito: toISOString() converte para UTC e,
 * à noite num fuso negativo, devolveria o dia seguinte.
 */
function emDias(dias: number): string {
  const date = new Date();
  date.setDate(date.getDate() + dias);
  const pad = (n: number) => String(n).padStart(2, '0');
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`;
}

const TRIPS = {
  trips: [
    {
      trip_uuid: 'T1', title: 'Viagem Interna Parrot', destination: 'Rio de Janeiro',
      start_date: emDias(13), end_date: emDias(20), traveler_count: 26, mode: 'pre-trip',
    },
    {
      trip_uuid: 'T2', title: 'Wharton Brazil Trek', destination: 'Rio de Janeiro',
      start_date: emDias(120), end_date: emDias(127), traveler_count: 43, mode: null,
    },
    {
      trip_uuid: 'T3', title: 'Viagem Acontecendo', destination: 'Bahia',
      start_date: emDias(-2), end_date: emDias(3), traveler_count: 10, mode: 'in-trip',
    },
  ],
};

function mockTrips(body: object = TRIPS) {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true, json: async () => body }));
}

function renderScreen() {
  return render(
    <MemoryRouter>
      <AuthProvider><TripsScreen /></AuthProvider>
    </MemoryRouter>
  );
}

beforeEach(() => {
  localStorage.clear();
  vi.restoreAllMocks();
  vi.stubEnv('VITE_DEV_AUTO_LOGIN', '');
});

test('groups trips by how soon they start', async () => {
  mockTrips();

  renderScreen();

  expect(await screen.findByText('Acontecendo agora')).toBeInTheDocument();
  expect(screen.getByText('Próximas')).toBeInTheDocument();
  expect(screen.getByText('Mais adiante')).toBeInTheDocument();
});

test('shows destination, travellers and how many days until departure', async () => {
  mockTrips();

  renderScreen();

  const titulo = await screen.findByText('Viagem Interna Parrot');
  // A linha inteira da viagem, para não confundir com outra também no Rio.
  const linha = titulo.closest('a')!;

  expect(linha).toHaveTextContent('Rio de Janeiro');
  expect(linha).toHaveTextContent('26 viajantes');
  expect(linha).toHaveTextContent('em 13 dias');
});

test('an empty group is not rendered', async () => {
  mockTrips({ trips: [TRIPS.trips[1]] });

  renderScreen();

  expect(await screen.findByText('Mais adiante')).toBeInTheDocument();
  expect(screen.queryByText('Acontecendo agora')).not.toBeInTheDocument();
  expect(screen.queryByText('Próximas')).not.toBeInTheDocument();
});

test('the pre-departure link is visible and copiable', async () => {
  const writeText = vi.fn().mockResolvedValue(undefined);
  vi.stubGlobal('navigator', { ...navigator, clipboard: { writeText } });
  mockTrips();

  renderScreen();

  const link = 'https://parrot-trips.netlify.app/profile?section=pre-departure';
  expect(await screen.findByDisplayValue(link)).toBeInTheDocument();
  expect(screen.getByRole('link', { name: /Abrir/ })).toHaveAttribute('href', link);

  await userEvent.click(screen.getByRole('button', { name: 'Copiar' }));
  expect(writeText).toHaveBeenCalledWith(link);
});

test('signing out clears the session', async () => {
  localStorage.setItem('parrot_console_user', JSON.stringify({
    userId: 'u1', phone: '+5511999999999', name: 'Admin', token: 'tok', role: 'admin',
  }));
  mockTrips();

  renderScreen();
  await userEvent.click(await screen.findByRole('button', { name: 'Sair' }));

  expect(localStorage.getItem('parrot_console_user')).toBeNull();
});
