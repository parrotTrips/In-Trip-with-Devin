import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { beforeEach, expect, test, vi } from 'vitest';

import RoteiroScreen from './RoteiroScreen';

const DIAS = {
  days: [
    {
      id: 'd1', title: 'Dia 1 — Chegada', sort_order: 0, is_visible: false,
      activities: [
        { id: 'a1', name: 'Aeroporto', activity_type: 'logistics', starts_at: null,
          duration_minutes: 60, short_description: '', practical_info: '', address: '',
          max_checkins: 1, amount_brl: null, sort_order: 0, checkin_count: 0, scan_count: 0 },
        { id: 'a2', name: 'Cristo Redentor', activity_type: 'included', starts_at: null,
          duration_minutes: 120, short_description: '', practical_info: '', address: '',
          max_checkins: 1, amount_brl: null, sort_order: 1, checkin_count: 3, scan_count: 12 },
      ],
    },
    { id: 'd2', title: 'Dia 2 — Praias', sort_order: 1, is_visible: false, activities: [] },
  ],
};

function mockDays(body: object = DIAS) {
  const fetchMock = vi.fn().mockResolvedValue({ ok: true, json: async () => body });
  vi.stubGlobal('fetch', fetchMock);
  return fetchMock;
}

function renderRoteiro() {
  return render(
    <MemoryRouter initialEntries={['/trips/T1/roteiro']}>
      <Routes>
        <Route path="/trips/:tripUuid/roteiro" element={<RoteiroScreen />} />
      </Routes>
    </MemoryRouter>
  );
}

beforeEach(() => vi.restoreAllMocks());

test('lists the days and shows the first day activities', async () => {
  mockDays();

  renderRoteiro();

  expect(await screen.findByRole('button', { name: /Dia 1 — Chegada/ })).toBeInTheDocument();
  expect(screen.getByRole('button', { name: /Dia 2 — Praias/ })).toBeInTheDocument();
  expect(screen.getByDisplayValue('Aeroporto')).toBeInTheDocument();
});

test('picking another day swaps the activities', async () => {
  mockDays();

  renderRoteiro();
  await userEvent.click(await screen.findByRole('button', { name: /Dia 2 — Praias/ }));

  expect(screen.queryByDisplayValue('Aeroporto')).not.toBeInTheDocument();
  expect(screen.getByText(/Nenhuma atividade neste dia/i)).toBeInTheDocument();
});

test('an activity with check-ins cannot be deleted and explains why', async () => {
  mockDays();

  renderRoteiro();
  await screen.findByDisplayValue('Cristo Redentor');

  const buttons = screen.getAllByRole('button', { name: 'Excluir' });
  expect(buttons[0]).toBeEnabled();    // Aeroporto, sem check-in
  expect(buttons[1]).toBeDisabled();   // Cristo, com 3 check-ins
  expect(screen.getByText(/3 check-in/)).toBeInTheDocument();
});

test('editing an activity sends a PATCH for that activity only', async () => {
  // GET sempre devolve a lista; só a mutação devolve o resultado dela — como no servidor.
  const fetchMock = vi.fn().mockImplementation((_url: string, options?: RequestInit) =>
    Promise.resolve({
      ok: true,
      json: async () => (options?.method ? { id: 'a1', updated: true } : DIAS),
    })
  );
  vi.stubGlobal('fetch', fetchMock);

  renderRoteiro();

  const name = await screen.findByDisplayValue('Aeroporto');
  await userEvent.clear(name);
  await userEvent.type(name, 'Transfer');
  await userEvent.click(screen.getAllByRole('button', { name: 'Salvar' })[0]);

  await screen.findByText('Salvo');

  const patch = fetchMock.mock.calls.find(c => c[1]?.method === 'PATCH');
  expect(String(patch![0])).toContain('/console/activities/a1');
  expect(JSON.parse(patch![1].body).name).toBe('Transfer');
});
