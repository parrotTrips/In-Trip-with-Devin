import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { beforeEach, expect, test, vi } from 'vitest';

import PhaseEditor from './PhaseEditor';

const phase = {
  id: 'p1', title: 'Documentos', subtitle: null, icon: null,
  short_description: 'curta', detailed_description: null,
  sort_order: 0, is_visible: false,
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

test('saving sends title and checklist in screen order', async () => {
  const fetchMock = vi.fn()
    .mockResolvedValueOnce({ ok: true, json: async () => ({ phases: [phase] }) })
    .mockResolvedValue({ ok: true, json: async () => ({ ok: true }) });
  vi.stubGlobal('fetch', fetchMock);

  renderEditor();

  const title = await screen.findByLabelText('Título');
  await userEvent.clear(title);
  await userEvent.type(title, 'Novo título');

  // sobe "Visto" para a primeira posição
  await userEvent.click(screen.getAllByRole('button', { name: 'Subir' })[1]);
  await userEvent.click(screen.getByRole('button', { name: 'Salvar' }));

  await screen.findByText('Salvo');

  const patchCall = fetchMock.mock.calls.find(c => c[1]?.method === 'PATCH');
  expect(JSON.parse(patchCall![1].body).title).toBe('Novo título');

  const checklistCall = fetchMock.mock.calls.find(c => String(c[0]).endsWith('/checklist'));
  expect(JSON.parse(checklistCall![1].body).items.map((i: { label: string }) => i.label))
    .toEqual(['Visto', 'Passaporte']);
});
