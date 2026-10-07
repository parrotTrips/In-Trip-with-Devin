import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { http, HttpResponse } from 'msw';
import { MemoryRouter, Route, Routes } from 'react-router-dom';

import { AuthProvider } from '../../app/providers/AuthProvider';
import { TripProvider } from '../../app/providers/TripProvider';
import { server } from '../../test/server';
import PhaseDetails from './pages/PhaseDetails';

const PHASE_ID = 'aaaaaaaa-0000-0000-0000-000000000001';
const TRIP_UUID = 'test-trip-001';
const USER_ID = 'bbbbbbbb-0000-0000-0000-000000000001';

function setupHandlers() {
  server.use(
    http.get('http://localhost:8000/me/trip', () =>
      HttpResponse.json({ trip: { wetravel_trip_uuid: TRIP_UUID, title: 'Test Trip', destination: 'Test', start_date: '2026-02-27', end_date: '2026-03-08', url: null } })
    ),
    http.get('http://localhost:8000/me/trip/phases', () =>
      HttpResponse.json({ wetravel_trip_uuid: TRIP_UUID, phases: [] })
    ),
    http.get('http://localhost:8000/me/trip/travelers', () =>
      HttpResponse.json({ travelers: [{ id: USER_ID, name: 'Alice', phone: '+15550000001', current_phase_id: PHASE_ID }] })
    ),
    http.get(`http://localhost:8000/me/trip/phases/${PHASE_ID}`, () =>
      HttpResponse.json({
        id: PHASE_ID,
        phase_type: 'pre-trip',
        title: 'Visa',
        subtitle: 'Entry Requirements',
        icon: 'passport',
        short_description: 'Visa requirements',
        detailed_description: 'Details about visa',
        sort_order: 0,
        starts_at: null,
        is_locked_by_default: false,
        checklist_items: [
          { id: 'item-1', label: 'Check visa requirements', sort_order: 0, is_required: true },
        ],
        links: [],
        activities: [],
      })
    ),
    http.get(`http://localhost:8000/checklist/${TRIP_UUID}/${USER_ID}`, () =>
      HttpResponse.json({ trip_id: TRIP_UUID, user_id: USER_ID, progress: { [PHASE_ID]: checklistProgress } })
    ),
    http.get(`http://localhost:8000/phases/${TRIP_UUID}/${USER_ID}`, () =>
      HttpResponse.json({ trip_id: TRIP_UUID, user_id: USER_ID, completions: {} })
    ),
    http.post('http://localhost:8000/checklist/update', () => HttpResponse.json({ message: 'ok' })),
  );
}

let checklistProgress: Record<string, boolean> = { 'item-1': true };

function renderPhase() {
  render(
    <MemoryRouter initialEntries={[`/phase/${PHASE_ID}`]}>
      <AuthProvider>
        <TripProvider>
          <Routes>
            <Route path="/phase/:phaseId" element={<PhaseDetails />} />
          </Routes>
        </TripProvider>
      </AuthProvider>
    </MemoryRouter>
  );
}

describe('PhaseDetails', () => {
  beforeEach(() => {
    localStorage.setItem(
      'parrot_user',
      JSON.stringify({ userId: USER_ID, phone: '+15550000001', name: 'Alice', token: 'tok', role: 'traveler', tripId: TRIP_UUID, activeTrip: null })
    );
    checklistProgress = { 'item-1': true };
    setupHandlers();
  });

  test('carrega e exibe a fase com checklist', async () => {
    render(
      <MemoryRouter initialEntries={[`/phase/${PHASE_ID}`]}>
        <AuthProvider>
          <TripProvider>
            <Routes>
              <Route path="/phase/:phaseId" element={<PhaseDetails />} />
            </Routes>
          </TripProvider>
        </AuthProvider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Checklist')).toBeInTheDocument();
    });
    expect(screen.getByText('Check visa requirements')).toBeInTheDocument();
  });

  test('links to the FAQ at the end of the phase', async () => {
    renderPhase();

    expect(await screen.findByRole('link', { name: /questions\? see the faq/i }))
      .toHaveAttribute('href', '/information?section=faq');
  });

  test('treats the phase as completed once every required checklist item is done', async () => {
    checklistProgress = {};
    renderPhase();

    const item = await screen.findByText('Check visa requirements');
    // Wait for the trip context, which the checklist update needs.
    await screen.findByText(/1 traveler on this phase/i);
    expect(screen.getByRole('button', { name: /mark as completed/i })).toBeInTheDocument();

    await userEvent.click(item);

    expect(await screen.findByText(/completed!/i)).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /mark as completed/i })).not.toBeInTheDocument();
  });
});
