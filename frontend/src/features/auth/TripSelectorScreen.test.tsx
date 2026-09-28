import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { http, HttpResponse } from 'msw';
import type { ComponentProps } from 'react';
import { vi } from 'vitest';

import { AuthProvider } from '../../app/providers/AuthProvider';
import { useAuth, type TripChoice } from '../../app/providers/auth-context';
import { server } from '../../test/server';
import TripSelectorScreen from './pages/TripSelectorScreen';

const TRIP_CURRENT: TripChoice = {
  trip_id: 'trip-current',
  title: 'Rio Adventure',
  destination: 'Rio de Janeiro',
  start_date: '2026-01-10',
  end_date: '2026-01-20',
  role: 'traveler',
  is_current: true,
};

const TRIP_FUTURE_STAFF: TripChoice = {
  trip_id: 'trip-future',
  title: 'Lisbon Kickoff',
  destination: 'Lisbon',
  start_date: '2026-06-01',
  end_date: '2026-06-10',
  role: 'staff',
  is_current: false,
};

const TRIP_FUTURE_TRAVELER: TripChoice = {
  trip_id: 'trip-future-2',
  title: 'Andes Trek',
  destination: 'Cusco',
  start_date: '2026-09-01',
  end_date: '2026-09-12',
  role: 'traveler',
  is_current: false,
};

function AuthProbe() {
  const auth = useAuth();
  return (
    <div>
      <div data-testid="probe-logged-in">{String(auth.isLoggedIn)}</div>
      <div data-testid="probe-trip-id">{auth.user?.tripId ?? 'none'}</div>
      <div data-testid="probe-role">{auth.user?.role ?? 'none'}</div>
      <div data-testid="probe-pending-trips">
        {auth.pendingSelection ? auth.pendingSelection.trips.length : 'none'}
      </div>
      <button
        onClick={() =>
          auth.beginTripSelection({
            userId: 'user-1',
            phone: '+15551234567',
            name: 'Alice',
            selectionToken: 'selection-tok',
            trips: [TRIP_CURRENT],
          })
        }
      >
        seed-pending
      </button>
    </div>
  );
}

function renderSelector(props: Partial<ComponentProps<typeof TripSelectorScreen>> = {}) {
  localStorage.removeItem('parrot_user');
  return render(
    <AuthProvider>
      <AuthProbe />
      <TripSelectorScreen
        trips={[TRIP_CURRENT, TRIP_FUTURE_STAFF]}
        token="selection-tok"
        {...props}
      />
    </AuthProvider>
  );
}

function mockSelectTrip(handler: (tripId: string) => object | Promise<object>) {
  server.use(
    http.post('http://localhost:8000/auth/select-trip', async ({ request }) => {
      const body = (await request.json()) as { trip_id: string };
      const result = await handler(body.trip_id);
      return HttpResponse.json(result);
    })
  );
}

const TRIP_SELECTED_RESULT = {
  status: 'trip_selected' as const,
  user_id: 'user-1',
  phone: '+15551234567',
  name: 'Alice',
  role: 'traveler' as const,
  message: 'Login successful',
  access_token: 'tok-current',
  active_trip: TRIP_CURRENT,
};

describe('TripSelectorScreen', () => {
  test('renders trips in the given order (current first, then future) with destination and dates', () => {
    renderSelector({ trips: [TRIP_CURRENT, TRIP_FUTURE_STAFF, TRIP_FUTURE_TRAVELER] });

    const buttons = screen.getAllByRole('button').filter(btn =>
      /Rio Adventure|Lisbon Kickoff|Andes Trek/.test(btn.textContent ?? '')
    );
    expect(buttons.map(b => b.textContent)).toEqual([
      expect.stringContaining('Rio Adventure'),
      expect.stringContaining('Lisbon Kickoff'),
      expect.stringContaining('Andes Trek'),
    ]);

    expect(screen.getByText('Rio de Janeiro')).toBeInTheDocument();
    // pt-BR date formatting, not raw ISO.
    expect(screen.getByText('10 jan – 20 jan 2026')).toBeInTheDocument();
  });

  test('shows a Staff badge only for staff trips', () => {
    renderSelector({ trips: [TRIP_CURRENT, TRIP_FUTURE_STAFF] });

    const currentCard = screen.getByText('Rio Adventure').closest('button')!;
    const staffCard = screen.getByText('Lisbon Kickoff').closest('button')!;

    expect(within(currentCard).queryByText('Staff')).not.toBeInTheDocument();
    expect(within(staffCard).getByText('Staff')).toBeInTheDocument();
  });

  test('shows an Em andamento indicator only for the current trip', () => {
    renderSelector({ trips: [TRIP_CURRENT, TRIP_FUTURE_STAFF] });

    const currentCard = screen.getByText('Rio Adventure').closest('button')!;
    const futureCard = screen.getByText('Lisbon Kickoff').closest('button')!;

    expect(within(currentCard).getByText('Em andamento')).toBeInTheDocument();
    expect(within(futureCard).queryByText('Em andamento')).not.toBeInTheDocument();
  });

  test('marks the active session with "Viagem ativa", independently of Em andamento', () => {
    // trip-future is the active *session*, trip-current is the *current* (is_current) trip —
    // these are deliberately different trips so the two badges can't be confused.
    renderSelector({
      trips: [TRIP_CURRENT, TRIP_FUTURE_STAFF],
      activeTripId: 'trip-future',
    });

    const currentCard = screen.getByText('Rio Adventure').closest('button')!;
    const activeCard = screen.getByText('Lisbon Kickoff').closest('button')!;

    expect(within(currentCard).queryByText('Viagem ativa')).not.toBeInTheDocument();
    expect(within(currentCard).getByText('Em andamento')).toBeInTheDocument();

    expect(within(activeCard).getByText('Viagem ativa')).toBeInTheDocument();
    expect(within(activeCard).queryByText('Em andamento')).not.toBeInTheDocument();
  });

  test('shows an informational note when there is only one trip', () => {
    renderSelector({ trips: [TRIP_CURRENT] });

    expect(screen.getByText(/você só tem uma viagem disponível/i)).toBeInTheDocument();
  });

  test('shows an empty state when there are no trips to choose from', () => {
    renderSelector({ trips: [] });

    expect(screen.getByText(/nenhuma viagem disponível/i)).toBeInTheDocument();
  });

  test('disables further selection while a choice is being submitted, and fires exactly one request', async () => {
    let resolveSelect: (value: object) => void = () => {};
    let requestCount = 0;
    mockSelectTrip(
      () => {
        requestCount += 1;
        return new Promise(resolve => {
          resolveSelect = resolve;
        });
      }
    );

    const user = userEvent.setup();
    renderSelector({ trips: [TRIP_CURRENT, TRIP_FUTURE_STAFF] });

    await user.click(screen.getByText('Rio Adventure').closest('button')!);

    await waitFor(() => {
      expect(screen.getByText('Rio Adventure').closest('button')).toBeDisabled();
    });
    expect(screen.getByText('Lisbon Kickoff').closest('button')).toBeDisabled();

    // Clicking the second card while a selection is in flight must not fire a second request.
    await user.click(screen.getByText('Lisbon Kickoff').closest('button')!);

    resolveSelect(TRIP_SELECTED_RESULT);

    await waitFor(() => {
      expect(screen.getByTestId('probe-logged-in')).toHaveTextContent('true');
    });
    expect(screen.getByTestId('probe-trip-id')).toHaveTextContent('trip-current');
    expect(requestCount).toBe(1);
  });

  test('ignores a stale select-trip response after Sair is pressed during an in-flight selection', async () => {
    let resolveSelect: (value: object) => void = () => {};
    mockSelectTrip(
      () =>
        new Promise(resolve => {
          resolveSelect = resolve;
        })
    );

    const user = userEvent.setup();
    renderSelector({ trips: [TRIP_CURRENT, TRIP_FUTURE_STAFF] });

    await user.click(screen.getByText('Rio Adventure').closest('button')!);
    await waitFor(() => {
      expect(screen.getByText('Rio Adventure').closest('button')).toBeDisabled();
    });

    // Back out while the request is still in flight.
    await user.click(screen.getByRole('button', { name: 'Sair' }));

    // The (stale) response now arrives.
    resolveSelect(TRIP_SELECTED_RESULT);
    // Give the fetch/JSON promise chain a full tick to run to completion
    // (or, if unguarded, to incorrectly complete the session) before asserting.
    await new Promise(resolve => setTimeout(resolve, 20));

    expect(screen.getByTestId('probe-logged-in')).toHaveTextContent('false');
    expect(localStorage.getItem('parrot_user')).toBeNull();
  });

  test('selecting a trip completes the session with the returned role', async () => {
    mockSelectTrip(tripId => ({
      status: 'trip_selected',
      user_id: 'user-1',
      phone: '+15551234567',
      name: 'Alice',
      role: 'staff',
      message: 'Login successful',
      access_token: 'tok-staff',
      active_trip: { ...TRIP_FUTURE_STAFF, trip_id: tripId },
    }));

    const user = userEvent.setup();
    renderSelector({ trips: [TRIP_CURRENT, TRIP_FUTURE_STAFF] });

    await user.click(screen.getByText('Lisbon Kickoff').closest('button')!);

    await waitFor(() => {
      expect(screen.getByTestId('probe-logged-in')).toHaveTextContent('true');
    });
    expect(screen.getByTestId('probe-trip-id')).toHaveTextContent('trip-future');
    expect(screen.getByTestId('probe-role')).toHaveTextContent('staff');
  });

  test('keeps the API error visible (as an alert) on the selector when selection fails, and allows a retry', async () => {
    let attempt = 0;
    server.use(
      http.post('http://localhost:8000/auth/select-trip', async () => {
        attempt += 1;
        if (attempt === 1) {
          return HttpResponse.json({ detail: 'Trip is no longer available' }, { status: 409 });
        }
        return HttpResponse.json(TRIP_SELECTED_RESULT);
      })
    );

    const user = userEvent.setup();
    renderSelector({ trips: [TRIP_CURRENT, TRIP_FUTURE_STAFF] });

    await user.click(screen.getByText('Rio Adventure').closest('button')!);

    const alert = await screen.findByRole('alert');
    expect(alert).toHaveTextContent('Trip is no longer available');
    // The selector stays up (no navigation away, no crash) so the person can retry.
    expect(screen.getByText('Lisbon Kickoff')).toBeInTheDocument();
    expect(screen.getByTestId('probe-logged-in')).toHaveTextContent('false');

    await user.click(screen.getByText('Rio Adventure').closest('button')!);

    await waitFor(() => {
      expect(screen.getByTestId('probe-logged-in')).toHaveTextContent('true');
    });
  });

  test('renders a Cancelar action that calls onCancel when provided (Task 7 in-app switcher usage)', async () => {
    const onCancel = vi.fn();
    const user = userEvent.setup();
    renderSelector({ onCancel });

    await user.click(screen.getByRole('button', { name: 'Cancelar' }));

    expect(onCancel).toHaveBeenCalledTimes(1);
  });

  test('renders a Sair action that signs out and clears any pending selection when onCancel is not provided', async () => {
    const user = userEvent.setup();
    renderSelector();

    await user.click(screen.getByRole('button', { name: 'seed-pending' }));
    expect(screen.getByTestId('probe-pending-trips')).toHaveTextContent('1');

    await user.click(screen.getByRole('button', { name: 'Sair' }));

    expect(screen.getByTestId('probe-logged-in')).toHaveTextContent('false');
    expect(screen.getByTestId('probe-pending-trips')).toHaveTextContent('none');
  });
});
