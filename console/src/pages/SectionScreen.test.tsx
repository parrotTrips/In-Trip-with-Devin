import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
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

const FAQ_EDITAVEL = {
  key: 'faq', label: 'FAQ', readonly_note: null, editable: true,
  columns: [
    { key: 'question', label: 'Pergunta', required: true },
    { key: 'answer', label: 'Resposta', required: true },
  ],
  rows: [{ question: 'Preciso de visto?', answer: 'Depende.' }],
};

test('an editable section warns the change is immediate', async () => {
  mockSection(FAQ_EDITAVEL);

  renderSection('faq');

  expect(await screen.findByText(/aparecem no app dos viajantes assim que você salvar/i))
    .toBeInTheDocument();
  expect(screen.queryByText(/ainda não foi construída/i)).not.toBeInTheDocument();
});

test('adding, reordering and saving sends one PUT with the screen order', async () => {
  const fetchMock = vi.fn()
    .mockResolvedValueOnce({ ok: true, json: async () => FAQ_EDITAVEL })
    .mockResolvedValue({ ok: true, json: async () => ({ key: 'faq', count: 2 }) });
  vi.stubGlobal('fetch', fetchMock);

  renderSection('faq');

  await userEvent.click(await screen.findByRole('button', { name: 'Adicionar' }));
  await userEvent.type(screen.getByLabelText('Pergunta 2'), 'Segunda?');
  await userEvent.type(screen.getByLabelText('Resposta 2'), 'Sim.');
  await userEvent.click(screen.getAllByRole('button', { name: 'Subir' })[1]);
  await userEvent.click(screen.getByRole('button', { name: 'Salvar' }));

  await screen.findByText('Salvo');

  const puts = fetchMock.mock.calls.filter(c => c[1]?.method === 'PUT');
  expect(puts).toHaveLength(1);
  expect(JSON.parse(puts[0][1].body).items.map((i: { question: string }) => i.question))
    .toEqual(['Segunda?', 'Preciso de visto?']);
});

test('an empty required field blocks the request', async () => {
  const fetchMock = vi.fn()
    .mockResolvedValueOnce({ ok: true, json: async () => FAQ_EDITAVEL })
    .mockResolvedValue({ ok: true, json: async () => ({}) });
  vi.stubGlobal('fetch', fetchMock);

  renderSection('faq');

  await userEvent.click(await screen.findByRole('button', { name: 'Adicionar' }));
  await userEvent.click(screen.getByRole('button', { name: 'Salvar' }));

  expect(await screen.findByText(/Pergunta.*obrigatóri/i)).toBeInTheDocument();
  expect(fetchMock.mock.calls.filter(c => c[1]?.method === 'PUT')).toHaveLength(0);
});

test('removing a row drops it from what is saved', async () => {
  const fetchMock = vi.fn()
    .mockResolvedValueOnce({ ok: true, json: async () => FAQ_EDITAVEL })
    .mockResolvedValue({ ok: true, json: async () => ({ key: 'faq', count: 0 }) });
  vi.stubGlobal('fetch', fetchMock);

  renderSection('faq');

  await userEvent.click(await screen.findByRole('button', { name: 'Remover' }));
  await userEvent.click(screen.getByRole('button', { name: 'Salvar' }));

  await screen.findByText('Salvo');
  const put = fetchMock.mock.calls.find(c => c[1]?.method === 'PUT');
  expect(JSON.parse(put![1].body).items).toEqual([]);
});
