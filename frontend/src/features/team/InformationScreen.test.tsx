import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { http, HttpResponse } from 'msw';
import { MemoryRouter } from 'react-router-dom';

import { TripContext } from '../../app/providers/trip-context';
import { server } from '../../test/server';
import type { TripInfo } from '../trip/services/trip-api';
import InformationScreen from './pages/InformationScreen';

function tripInfoFor(tripUuid: string): TripInfo {
  return {
    wetravel_trip_uuid: tripUuid,
    title: 'Viagem de Teste',
    destination: 'Brasil',
    start_date: '2026-07-01',
    end_date: '2026-07-05',
    url: null,
    service_agreement_url: null,
    trip_mode: 'pre-trip',
  };
}

function renderInformationScreen(tripUuid: string) {
  return render(
    <MemoryRouter>
      <TripContext.Provider
        value={{
          tripInfo: tripInfoFor(tripUuid),
          phases: [],
          travelers: [],
          idealPacePhaseId: null,
          loading: false,
          error: null,
          refetch: () => {},
        }}
      >
        <InformationScreen />
      </TripContext.Provider>
    </MemoryRouter>
  );
}

describe('InformationScreen', () => {
  beforeEach(() => {
    server.use(
      http.get('http://localhost:8000/me/team', () => HttpResponse.json({ team: [] })),
      http.get('http://localhost:8000/me/emergency-contacts', () => HttpResponse.json({ emergency_contacts: [] })),
      http.get('http://localhost:8000/me/recommendations', () => HttpResponse.json({ recommendations: [] })),
      http.get('http://localhost:8000/me/faq', () => HttpResponse.json({ faq: [] })),
      http.get('http://localhost:8000/me/cancellation-policy', () => HttpResponse.json({ cancellation_policy: [] }))
    );
  });

  test('shows the app feedback form link for the test trip', async () => {
    renderInformationScreen('TEST-2026-FULL');

    const feedbackButton = await screen.findByRole('button', { name: /feedback/i });
    await userEvent.click(feedbackButton);

    const feedbackLink = screen.getByRole('link', { name: /enviar feedback/i });
    expect(feedbackLink).toHaveAttribute(
      'href',
      'https://docs.google.com/forms/d/e/1FAIpQLScp8ytsEyAKioMH86yWrqDANVCAS-NIM0Je075N-a4bhNk1iA/viewform?usp=publish-editor'
    );
  });

  test('hides the app feedback form link for other trips', async () => {
    renderInformationScreen('OTHER-TRIP');

    await screen.findByRole('button', { name: /parrot team/i });

    expect(screen.queryByRole('button', { name: /feedback/i })).not.toBeInTheDocument();
  });

  test('links local recommendations to the dedicated recommendations page', async () => {
    renderInformationScreen('OTHER-TRIP');

    const recommendationsButton = await screen.findByRole('button', { name: /local recommendations/i });
    await userEvent.click(recommendationsButton);

    expect(screen.getByRole('link', { name: /open recommendations/i })).toHaveAttribute('href', '/recommendations');
  });
});
