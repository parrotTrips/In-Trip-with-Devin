import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, expect, test, vi } from 'vitest';

import TripsScreen from './TripsScreen';

beforeEach(() => {
  vi.restoreAllMocks();
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
    ok: true,
    json: async () => ({
      trips: [{
        trip_uuid: 'T1', title: 'Viagem Um',
        start_date: '2027-07-01', end_date: '2027-07-10',
      }],
    }),
  }));
});

test('lists trips returned by the API', async () => {
  render(<MemoryRouter><TripsScreen /></MemoryRouter>);
  expect(await screen.findByText('Viagem Um')).toBeInTheDocument();
});

test('copies the pre-departure link to the clipboard', async () => {
  const writeText = vi.fn().mockResolvedValue(undefined);
  vi.stubGlobal('navigator', { ...navigator, clipboard: { writeText } });

  render(<MemoryRouter><TripsScreen /></MemoryRouter>);
  await screen.findByText('Viagem Um');
  await userEvent.click(screen.getByRole('button', { name: 'Copiar link de pré-embarque' }));

  expect(writeText).toHaveBeenCalledWith(
    'https://parrot-trips.netlify.app/profile?section=pre-departure'
  );
});
