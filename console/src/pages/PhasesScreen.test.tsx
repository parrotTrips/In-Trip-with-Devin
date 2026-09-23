import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { beforeEach, expect, test, vi } from 'vitest';

import PhasesScreen from './PhasesScreen';

function phase(overrides = {}) {
  return {
    id: 'p1', title: 'Documentos', subtitle: null, icon: null,
    short_description: '', detailed_description: null,
    sort_order: 0, is_visible: false, checklist: [], links: [],
    ...overrides,
  };
}

function renderAt(tripUuid: string) {
  return render(
    <MemoryRouter initialEntries={[`/trips/${tripUuid}/phases`]}>
      <Routes>
        <Route path="/trips/:tripUuid/phases" element={<PhasesScreen />} />
      </Routes>
    </MemoryRouter>
  );
}

beforeEach(() => vi.restoreAllMocks());

test('shows a draft phase as draft', async () => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
    ok: true, json: async () => ({ phases: [phase()] }),
  }));

  renderAt('T1');

  expect(await screen.findByText('Documentos')).toBeInTheDocument();
  expect(screen.getByText('Rascunho')).toBeInTheDocument();
});

test('publishing calls the API and shows the phase as published', async () => {
  let published = false;
  const fetchMock = vi.fn().mockImplementation((_url: string, options?: RequestInit) => {
    if (options?.method) {
      published = true;
      return Promise.resolve({ ok: true, json: async () => ({ id: 'p1', is_visible: true }) });
    }
    return Promise.resolve({
      ok: true, json: async () => ({ phases: [phase({ is_visible: published })] }),
    });
  });
  vi.stubGlobal('fetch', fetchMock);

  renderAt('T1');
  await screen.findByText('Documentos');
  await userEvent.click(screen.getByRole('button', { name: 'Publicar' }));

  expect(await screen.findByText('Publicada')).toBeInTheDocument();
  expect(fetchMock.mock.calls[1][0]).toContain('/console/phases/p1/publish');
});

test('moving a phase up sends the new order', async () => {
  const two = [phase(), phase({ id: 'p2', title: 'Bagagem', sort_order: 1 })];
  // GET sempre devolve a lista; só a mutação devolve o resultado dela — como no servidor.
  const fetchMock = vi.fn().mockImplementation((_url: string, options?: RequestInit) =>
    Promise.resolve({
      ok: true,
      json: async () => (options?.method ? { count: 2 } : { phases: two }),
    })
  );
  vi.stubGlobal('fetch', fetchMock);

  renderAt('T1');
  await screen.findByText('Bagagem');
  await userEvent.click(screen.getAllByRole('button', { name: 'Subir' })[1]);

  const orderCall = fetchMock.mock.calls.find(c => String(c[0]).endsWith('/phases/order'));
  expect(JSON.parse(orderCall![1].body).phase_ids).toEqual(['p2', 'p1']);
});
