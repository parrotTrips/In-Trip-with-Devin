import { render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { beforeEach, expect, test, vi } from 'vitest';

import SectionScreen from './SectionScreen';

function mockSection(body: object) {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true, json: async () => body }));
}

function renderSection(key: string) {
  return render(
    <MemoryRouter initialEntries={[`/trips/T1/${key}`]}>
      <Routes>
        <Route path="/trips/:tripUuid/:sectionKey" element={<SectionScreen />} />
      </Routes>
    </MemoryRouter>
  );
}

beforeEach(() => vi.restoreAllMocks());

test('renders the rows of a section as a table', async () => {
  mockSection({
    key: 'recomendacoes', label: 'Recomendações', readonly_note: null,
    rows: [
      { name: 'Aprazível', category: 'restaurante', neighborhood: 'Santa Teresa', address: 'Rua X' },
      { name: 'Bar Urca', category: 'bar', neighborhood: 'Urca', address: 'Rua Y' },
    ],
  });

  renderSection('recomendacoes');

  expect(await screen.findByText('Aprazível')).toBeInTheDocument();
  expect(screen.getByText('Bar Urca')).toBeInTheDocument();
  expect(screen.getByText('Santa Teresa')).toBeInTheDocument();
});

test('an empty section says nothing is registered yet', async () => {
  mockSection({ key: 'faq', label: 'FAQ', readonly_note: null, rows: [] });

  renderSection('faq');

  expect(await screen.findByText(/Nada cadastrado ainda/i)).toBeInTheDocument();
});

test('shows the read-only banner explaining editing is not built yet', async () => {
  mockSection({ key: 'faq', label: 'FAQ', readonly_note: null, rows: [] });

  renderSection('faq');

  expect(await screen.findByText(/edição desta seção ainda não foi construída/i))
    .toBeInTheDocument();
});

test('a section with its own reason shows that reason instead', async () => {
  mockSection({
    key: 'viajantes', label: 'Viajantes',
    readonly_note: 'Viajantes vêm do WeTravel.',
    rows: [{ full_name: 'Ana', phone: '+5511999999999', email: 'ana@x.com', profile_completed: true }],
  });

  renderSection('viajantes');

  expect(await screen.findByText(/Viajantes vêm do WeTravel/)).toBeInTheDocument();
  expect(screen.queryByText(/ainda não foi construída/i)).not.toBeInTheDocument();
});

test('booleans render as sim or não, not as true or false', async () => {
  mockSection({
    key: 'viajantes', label: 'Viajantes', readonly_note: null,
    rows: [
      { full_name: 'Ana', profile_completed: true },
      { full_name: 'Beto', profile_completed: false },
    ],
  });

  renderSection('viajantes');

  expect(await screen.findByText('Sim')).toBeInTheDocument();
  expect(screen.getByText('Não')).toBeInTheDocument();
  expect(screen.queryByText('true')).not.toBeInTheDocument();
});
