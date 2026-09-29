import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { beforeEach, expect, test, vi } from 'vitest';

import TripLayout from './TripLayout';

const SECTIONS = {
  sections: [
    { key: 'fases', label: 'Fases pré-trip', group: 'conteudo',
      group_label: 'Conteúdo do app', count: 4, editable: true, readonly_note: null },
    { key: 'recomendacoes', label: 'Recomendações', group: 'conteudo',
      group_label: 'Conteúdo do app', count: 0, editable: false, readonly_note: null },
    { key: 'viajantes', label: 'Viajantes', group: 'pessoas',
      group_label: 'Pessoas', count: 43, editable: false,
      readonly_note: 'Viajantes vêm do WeTravel.' },
    { key: 'avisos', label: 'Avisos', group: 'durante',
      group_label: 'Durante a viagem', count: 0, editable: false, readonly_note: null },
    { key: 'feedbacks', label: 'Feedbacks', group: 'retorno',
      group_label: 'Retorno', count: 2, editable: false,
      readonly_note: 'Escrito pelos viajantes no app.' },
  ],
};

function mockFetch(bySuffix: Record<string, object>) {
  return vi.fn().mockImplementation((url: string) => {
    const match = Object.keys(bySuffix).find(suffix => String(url).endsWith(suffix));
    return Promise.resolve({
      ok: true,
      json: async () => (match ? bySuffix[match] : {}),
    });
  });
}

function renderAt(path: string) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        <Route path="/trips/:tripUuid" element={<TripLayout />}>
          <Route path=":sectionKey" element={<p>conteúdo da seção</p>} />
        </Route>
      </Routes>
    </MemoryRouter>
  );
}

beforeEach(() => vi.restoreAllMocks());

test('renders the four groups with their sections and counts', async () => {
  vi.stubGlobal('fetch', mockFetch({ '/sections': SECTIONS }));

  renderAt('/trips/T1/fases');

  expect(await screen.findByText('Conteúdo do app')).toBeInTheDocument();
  expect(screen.getByText('Pessoas')).toBeInTheDocument();
  expect(screen.getByText('Durante a viagem')).toBeInTheDocument();
  expect(screen.getByText('Retorno')).toBeInTheDocument();

  expect(screen.getByRole('link', { name: /Viajantes/ })).toHaveTextContent('43');
  expect(screen.getByRole('link', { name: /Recomendações/ })).toHaveTextContent('0');
});

test('navigating to a section changes the address', async () => {
  vi.stubGlobal('fetch', mockFetch({ '/sections': SECTIONS }));

  renderAt('/trips/T1/fases');
  await userEvent.click(await screen.findByRole('link', { name: /Recomendações/ }));

  expect(screen.getByRole('link', { name: /Recomendações/ })).toHaveAttribute(
    'href', '/trips/T1/recomendacoes'
  );
  expect(screen.getByText('conteúdo da seção')).toBeInTheDocument();
});
