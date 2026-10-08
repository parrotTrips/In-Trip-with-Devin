import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { http, HttpResponse } from 'msw';
import { MemoryRouter } from 'react-router-dom';
import { vi } from 'vitest';

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

function renderInformationScreen(tripUuid: string, path = '/information') {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <TripContext.Provider
        value={{
          tripInfo: tripInfoFor(tripUuid),
          phases: [],
          travelers: [],
          idealPacePhaseId: null,
          completedPhaseIds: [],
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
  const cancellationPolicyRequest = vi.fn();

  beforeEach(() => {
    cancellationPolicyRequest.mockClear();
    server.use(
      http.get('http://localhost:8000/me/team', () => HttpResponse.json({ team: [] })),
      http.get('http://localhost:8000/me/emergency-contacts', () => HttpResponse.json({ emergency_contacts: [] })),
      http.get('http://localhost:8000/me/recommendations', () => HttpResponse.json({ recommendations: [] })),
      http.get('http://localhost:8000/me/faq', () => HttpResponse.json({ faq: [] })),
      http.get('http://localhost:8000/me/cancellation-policy', () => {
        cancellationPolicyRequest();
        return HttpResponse.json({ cancellation_policy: [] });
      })
    );
  });

  test('lets travelers send app feedback inside the app', async () => {
    let savedPayload: unknown = null;
    server.use(
      http.post('http://localhost:8000/me/app-feedback', async ({ request }) => {
        savedPayload = await request.json();
        return HttpResponse.json({
          id: 'feedback-1',
          feedback: 'The app made the trip easier.',
          created_at: '2026-08-16T12:00:00Z',
        });
      })
    );

    renderInformationScreen('OTHER-TRIP');

    const feedbackButton = await screen.findByRole('button', { name: /feedback/i });
    await userEvent.click(feedbackButton);

    expect(screen.getByText(/Tell us what worked well in the app/i)).toBeInTheDocument();

    const feedbackField = screen.getByRole('textbox', { name: /app feedback/i });
    expect(feedbackField).toHaveValue('');
    expect(screen.queryByRole('link', { name: /enviar feedback/i })).not.toBeInTheDocument();

    const sendButton = screen.getByRole('button', { name: /send feedback/i });
    expect(sendButton).toBeDisabled();

    await userEvent.type(feedbackField, 'The app made the trip easier.');
    expect(sendButton).toBeEnabled();
    await userEvent.click(sendButton);

    expect(savedPayload).toEqual({ feedback: 'The app made the trip easier.' });
    expect(await screen.findByText(/feedback sent/i)).toBeInTheDocument();
    expect(feedbackField).toHaveValue('');
  });

  test('opens the FAQ section when linked from the journey', async () => {
    server.use(
      http.get('http://localhost:8000/me/faq', () => HttpResponse.json({
        faq: [{ id: 'f1', question: 'Do I need a visa?', answer: 'Check the visa phase.', sort_order: 0 }],
      }))
    );
    const scrollIntoView = vi.fn();
    window.HTMLElement.prototype.scrollIntoView = scrollIntoView;

    renderInformationScreen('OTHER-TRIP', '/information?section=faq');

    expect(await screen.findByText('Do I need a visa?')).toBeInTheDocument();
    expect(screen.queryByText('No team members yet')).not.toBeInTheDocument();
    expect(scrollIntoView).toHaveBeenCalled();
    Reflect.deleteProperty(window.HTMLElement.prototype, 'scrollIntoView');
  });

  test('links local recommendations directly to the dedicated recommendations page', async () => {
    renderInformationScreen('OTHER-TRIP');

    const recommendationsLink = await screen.findByRole('link', { name: /local recommendations/i });
    expect(recommendationsLink).toHaveAttribute('href', '/recommendations');
    expect(screen.queryByRole('button', { name: /local recommendations/i })).not.toBeInTheDocument();
  });

  test('does not list or load the cancellation policy after it moves to My Profile', async () => {
    renderInformationScreen('OTHER-TRIP');

    await screen.findByRole('button', { name: /feedback/i });
    expect(screen.queryByRole('button', { name: /cancellation policy/i })).not.toBeInTheDocument();
    expect(cancellationPolicyRequest).not.toHaveBeenCalled();
  });
});
