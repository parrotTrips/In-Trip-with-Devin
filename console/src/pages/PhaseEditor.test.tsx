import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { beforeEach, expect, test, vi } from 'vitest';

import PhaseEditor from './PhaseEditor';

const phase = {
  id: 'p1', title: 'Documentos', subtitle: null, icon: null,
  short_description: 'curta', detailed_description: null,
  sort_order: 0, is_visible: false, starts_at: null, ends_at: null,
  checklist: [
    { id: 'c1', label: 'Passaporte', is_required: true, sort_order: 0 },
    { id: 'c2', label: 'Visto', is_required: false, sort_order: 1 },
  ],
  links: [],
};

function renderEditor() {
  return render(
    <MemoryRouter initialEntries={['/trips/T1/phases/p1']}>
      <Routes>
        <Route path="/trips/:tripUuid/phases/:phaseId" element={<PhaseEditor />} />
      </Routes>
    </MemoryRouter>
  );
}

beforeEach(() => vi.restoreAllMocks());

test('saving uses one atomic request with fields and children in screen order', async () => {
  const fetchMock = vi.fn()
    .mockResolvedValueOnce({ ok: true, json: async () => ({ phases: [phase] }) })
    .mockResolvedValueOnce({ ok: true, json: async () => ({ updated: true }) });
  vi.stubGlobal('fetch', fetchMock);
  renderEditor();

  const title = await screen.findByLabelText('Título');
  await userEvent.clear(title);
  await userEvent.type(title, 'Novo título');
  await userEvent.click(screen.getAllByRole('button', { name: 'Subir' })[1]);
  await userEvent.type(screen.getByLabelText('Início'), '2027-07-01T09:00');
  await userEvent.type(screen.getByLabelText('Fim'), '2027-07-02T18:00');
  await userEvent.click(screen.getByRole('button', { name: 'Salvar' }));

  expect(await screen.findByText('Salvo')).toBeInTheDocument();
  const writes = fetchMock.mock.calls.filter(call => call[1]?.method);
  expect(writes).toHaveLength(1);
  expect(String(writes[0][0])).toContain('/console/phases/p1/content');
  const body = JSON.parse(writes[0][1].body);
  expect(body.title).toBe('Novo título');
  expect(body.checklist.map((item: { label: string }) => item.label))
    .toEqual(['Visto', 'Passaporte']);
  expect(body.starts_at).toBe('2027-07-01T09:00');
  expect(body.ends_at).toBe('2027-07-02T18:00');
});

test('published phase is read-only', async () => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
    ok: true, json: async () => ({ phases: [{ ...phase, is_visible: true }] }),
  }));
  renderEditor();

  expect(await screen.findByText(/Despublique a fase para editar/)).toBeInTheDocument();
  expect(screen.getByLabelText('Título')).toBeDisabled();
  expect(screen.getByRole('button', { name: 'Salvar' })).toBeDisabled();
});

test('invalid URL and inverted dates are rejected before a request', async () => {
  const withLink = {
    ...phase,
    links: [{ id: 'l1', label: 'Arquivo', url: '', sort_order: 0 }],
  };
  const fetchMock = vi.fn().mockResolvedValueOnce({
    ok: true, json: async () => ({ phases: [withLink] }),
  });
  vi.stubGlobal('fetch', fetchMock);
  renderEditor();
  await screen.findByLabelText('Título');

  await userEvent.type(screen.getByLabelText('Link 1 url'), 'ftp://example.com');
  await userEvent.type(screen.getByLabelText('Início'), '2027-07-02T10:00');
  await userEvent.type(screen.getByLabelText('Fim'), '2027-07-01T10:00');
  await userEvent.click(screen.getByRole('button', { name: 'Salvar' }));

  expect(await screen.findByText(/URL válida com http/)).toBeInTheDocument();
  expect(fetchMock).toHaveBeenCalledTimes(1);
});

test('failed save keeps the typed data and shows the error', async () => {
  const fetchMock = vi.fn()
    .mockResolvedValueOnce({ ok: true, json: async () => ({ phases: [phase] }) })
    .mockResolvedValueOnce({
      ok: false, status: 500, statusText: '500', json: async () => ({ detail: 'Falha controlada' }),
    });
  vi.stubGlobal('fetch', fetchMock);
  renderEditor();

  const title = await screen.findByLabelText('Título');
  await userEvent.clear(title);
  await userEvent.type(title, 'Ainda aqui');
  await userEvent.click(screen.getByRole('button', { name: 'Salvar' }));

  expect(await screen.findByText('Falha controlada')).toBeInTheDocument();
  expect(screen.getByLabelText('Título')).toHaveValue('Ainda aqui');
});

test('disables editing controls while save is pending', async () => {
  let finishSave!: (response: object) => void;
  const pendingSave = new Promise<object>(resolve => { finishSave = resolve; });
  const fetchMock = vi.fn()
    .mockResolvedValueOnce({ ok: true, json: async () => ({ phases: [phase] }) })
    .mockReturnValueOnce(pendingSave);
  vi.stubGlobal('fetch', fetchMock);
  renderEditor();

  await screen.findByLabelText('Título');
  await userEvent.click(screen.getByRole('button', { name: 'Salvar' }));

  expect(screen.getByRole('button', { name: 'Salvando…' })).toBeDisabled();
  expect(screen.getByLabelText('Título')).toBeDisabled();

  finishSave({ ok: true, json: async () => ({ updated: true }) });
  expect(await screen.findByText('Salvo')).toBeInTheDocument();
});
