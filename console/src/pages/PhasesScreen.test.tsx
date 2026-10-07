import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { beforeEach, expect, test, vi } from 'vitest';

import PhasesScreen from './PhasesScreen';

function phase(overrides = {}) {
  return {
    id: 'p1', title: 'Documentos', subtitle: null, icon: null,
    short_description: 'Descrição', detailed_description: null,
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
  const fetchMock = vi.fn()
    .mockResolvedValueOnce({ ok: true, json: async () => ({ phases: [phase()] }) })
    .mockResolvedValueOnce({ ok: true, json: async () => ({ id: 'p1', is_visible: true }) })
    .mockResolvedValueOnce({
      ok: true, json: async () => ({ phases: [phase({ is_visible: true })] }),
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
  const fetchMock = vi.fn()
    .mockResolvedValueOnce({ ok: true, json: async () => ({ phases: two }) })
    .mockResolvedValueOnce({ ok: true, json: async () => ({ count: 2 }) })
    .mockResolvedValueOnce({ ok: true, json: async () => ({ phases: [two[1], two[0]] }) });
  vi.stubGlobal('fetch', fetchMock);

  renderAt('T1');
  await screen.findByText('Bagagem');
  await userEvent.click(screen.getAllByRole('button', { name: 'Subir' })[1]);

  const orderCall = fetchMock.mock.calls.find(c => String(c[0]).endsWith('/phases/order'));
  expect(JSON.parse(orderCall![1].body).phase_ids).toEqual(['p2', 'p1']);
});

test('published phases cannot be edited, reordered or deleted', async () => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
    ok: true, json: async () => ({ phases: [phase({ is_visible: true })] }),
  }));

  renderAt('T1');
  await screen.findByText('Publicada');

  expect(screen.queryByRole('link', { name: 'Documentos' })).not.toBeInTheDocument();
  expect(screen.getByRole('button', { name: 'Subir' })).toBeDisabled();
  expect(screen.queryByRole('button', { name: 'Excluir' })).not.toBeInTheDocument();
  expect(screen.getByText(/Despublique todas as fases/)).toBeInTheDocument();
});

test('creating a phase requires title and short description', async () => {
  const fetchMock = vi.fn()
    .mockResolvedValueOnce({ ok: true, json: async () => ({ phases: [] }) })
    .mockResolvedValueOnce({ ok: true, json: async () => ({ id: 'p1', is_visible: false }) })
    .mockResolvedValueOnce({ ok: true, json: async () => ({ phases: [phase()] }) });
  vi.stubGlobal('fetch', fetchMock);
  renderAt('T1');
  await screen.findByText('Fases');

  await userEvent.click(screen.getByRole('button', { name: 'Nova fase' }));
  expect(screen.getByRole('button', { name: 'Criar fase' })).toBeDisabled();
  await userEvent.type(screen.getByLabelText('Título da fase'), 'Documentos');
  await userEvent.type(screen.getByLabelText('Descrição curta da fase'), 'Prepare tudo');
  await userEvent.click(screen.getByRole('button', { name: 'Criar fase' }));

  const createCall = fetchMock.mock.calls.find(call => call[1]?.method === 'POST');
  expect(JSON.parse(createCall![1].body)).toEqual({
    title: 'Documentos', short_description: 'Prepare tudo',
  });
});

test('deletion requires typing the exact draft title', async () => {
  const fetchMock = vi.fn()
    .mockResolvedValueOnce({ ok: true, json: async () => ({ phases: [phase()] }) })
    .mockResolvedValueOnce({ ok: true, json: async () => ({ deleted: true }) })
    .mockResolvedValueOnce({ ok: true, json: async () => ({ phases: [] }) });
  vi.stubGlobal('fetch', fetchMock);
  renderAt('T1');
  await screen.findByText('Documentos');

  await userEvent.click(screen.getByRole('button', { name: 'Excluir' }));
  expect(screen.getByRole('dialog')).toBeInTheDocument();
  const confirm = screen.getByRole('button', { name: 'Confirmar exclusão' });
  expect(confirm).toBeDisabled();
  await userEvent.type(screen.getByLabelText('Digite o título da fase'), 'Documentos');
  await userEvent.click(confirm);

  expect(fetchMock.mock.calls.some(call => call[1]?.method === 'DELETE')).toBe(true);
});

test('cancelling deletion does not call the API', async () => {
  const fetchMock = vi.fn().mockResolvedValueOnce({
    ok: true, json: async () => ({ phases: [phase()] }),
  });
  vi.stubGlobal('fetch', fetchMock);
  renderAt('T1');
  await screen.findByText('Documentos');

  await userEvent.click(screen.getByRole('button', { name: 'Excluir' }));
  await userEvent.type(screen.getByLabelText('Digite o título da fase'), 'Documentos');
  await userEvent.click(screen.getByRole('button', { name: 'Cancelar' }));

  expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
  expect(fetchMock).toHaveBeenCalledTimes(1);
});

test('phase titles open the editor route', async () => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
    ok: true, json: async () => ({ phases: [phase()] }),
  }));

  renderAt('T1');

  expect(await screen.findByRole('link', { name: 'Documentos' }))
    .toHaveAttribute('href', '/trips/T1/fases/p1');
});

function renderWrapUp(tripUuid: string) {
  return render(
    <MemoryRouter initialEntries={[`/trips/${tripUuid}/wrap-up`]}>
      <Routes>
        <Route path="/trips/:tripUuid/wrap-up" element={<PhasesScreen phaseType="post-trip" />} />
      </Routes>
    </MemoryRouter>
  );
}

test('creates the Trip Wrap-up from the default template', async () => {
  const wrapUp = phase({ id: 'w1', title: 'Trip Wrap-up' });
  const fetchMock = vi.fn()
    .mockResolvedValueOnce({ ok: true, json: async () => ({ phases: [] }) })
    .mockResolvedValueOnce({ ok: true, json: async () => ({ id: 'w1', is_visible: false }) })
    .mockResolvedValueOnce({ ok: true, json: async () => ({ phases: [wrapUp] }) });
  vi.stubGlobal('fetch', fetchMock);

  renderWrapUp('T1');

  expect(await screen.findByRole('heading', { name: 'Trip Wrap-up' })).toBeInTheDocument();
  expect(fetchMock.mock.calls[0][0]).toContain('/console/trips/T1/phases?phase_type=post-trip');
  await userEvent.click(screen.getByRole('button', { name: /criar com modelo padrão/i }));

  expect(fetchMock.mock.calls[1][0]).toContain('/console/trips/T1/wrap-up');
  expect(await screen.findByRole('link', { name: 'Trip Wrap-up' }))
    .toHaveAttribute('href', '/trips/T1/fases/w1?type=post-trip');
  expect(screen.queryByRole('button', { name: /criar com modelo padrão/i })).not.toBeInTheDocument();
});
