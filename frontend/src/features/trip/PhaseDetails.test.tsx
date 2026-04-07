import { render, screen, waitFor } from '@testing-library/react';
import { http, HttpResponse } from 'msw';
import { MemoryRouter, Route, Routes } from 'react-router-dom';

import { AuthProvider } from '../../app/providers/AuthProvider';
import { server } from '../../test/server';
import PhaseDetails from './pages/PhaseDetails';

describe('PhaseDetails', () => {
  test('loads checklist progress for the phase', async () => {
    let checklistRequested = false;

    localStorage.setItem(
      'parrot_user',
      JSON.stringify({ userId: 1, phone: '+15550000001', name: 'Alice' })
    );

    server.use(
      http.get('http://localhost:8000/checklist/ross26/1', () => {
        checklistRequested = true;
        return HttpResponse.json({
          trip_id: 'ross26',
          user_id: 1,
          progress: { visa: { 'visa-1': true } },
        });
      })
    );

    render(
      <MemoryRouter initialEntries={['/phase/visa']}>
        <AuthProvider>
          <Routes>
            <Route path="/phase/:phaseId" element={<PhaseDetails />} />
          </Routes>
        </AuthProvider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(checklistRequested).toBe(true);
    });
    expect(screen.getByText('Checklist')).toBeInTheDocument();
  });
});
