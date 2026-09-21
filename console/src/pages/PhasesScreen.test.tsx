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
