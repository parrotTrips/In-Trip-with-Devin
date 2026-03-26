import { render, screen } from '@testing-library/react';
import { http, HttpResponse } from 'msw';
import { MemoryRouter, Route, Routes } from 'react-router-dom';

import { AuthProvider } from '../../app/providers/AuthProvider';
import { server } from '../../test/server';
import DayDetails from './pages/DayDetails';

describe('DayDetails', () => {
  test('loads public comments for the selected trip day', async () => {
    localStorage.setItem(
      'parrot_user',
      JSON.stringify({ userId: 1, phone: '+15550000001', name: 'Alice' })
    );

    server.use(
      http.get('http://localhost:8000/comments/ross26/day1', () =>
        HttpResponse.json({
          trip_id: 'ross26',
          phase_id: 'day1',
          comments: [
            {
              id: 1,
              user_id: 1,
              user_name: 'Alice',
              text: 'Amazing first day',
              created_at: '2026-02-27T22:00:00+00:00',
              is_private: false,
            },
          ],
        })
      )
    );

    render(
      <MemoryRouter initialEntries={['/day/day1']}>
        <AuthProvider>
          <Routes>
            <Route path="/day/:dayId" element={<DayDetails />} />
          </Routes>
        </AuthProvider>
      </MemoryRouter>
    );

    expect(await screen.findByText('Amazing first day')).toBeInTheDocument();
  });
});
