import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { http, HttpResponse } from 'msw';
import { useEffect } from 'react';
import { afterEach, beforeEach, describe, expect, test } from 'vitest';

import { request } from '../../shared/api/client';
import { server } from '../../test/server';
import { AuthProvider } from './AuthProvider';
import { useAuth, type TripChoice } from './auth-context';

const TRIP_A: TripChoice = {
  trip_id: 'trip-a',
  title: 'Rio Adventure',
  destination: 'Rio de Janeiro',
  start_date: '2026-01-10',
  end_date: '2026-01-20',
  role: 'traveler',
  is_current: true,
};

const TRIP_B: TripChoice = {
  trip_id: 'trip-b',
  title: 'Lisbon Kickoff',
  destination: 'Lisbon',
  start_date: '2026-03-01',
  end_date: '2026-03-10',
  role: 'staff',
  is_current: false,
};

function Probe() {
  const auth = useAuth();

  return (
    <div>
      <div data-testid="logged-in">{String(auth.isLoggedIn)}</div>
      <div data-testid="trip-id">{auth.user?.tripId ?? 'none'}</div>
      <div data-testid="active-trip-title">{auth.user?.activeTrip?.title ?? 'none'}</div>
      <div data-testid="role">{auth.user?.role ?? 'none'}</div>
      <div data-testid="token">{auth.user?.token ?? 'none'}</div>
      <div data-testid="pending-trips">
        {auth.pendingSelection ? auth.pendingSelection.trips.length : 'none'}
      </div>
      <div data-testid="switcher-open">{String(auth.isTripSwitcherOpen)}</div>
      <div data-testid="no-trips">{String(auth.hasNoTrips)}</div>
      <button
        onClick={() =>
          auth.beginTripSelection({
            userId: 'user-1',
            phone: '+15550000001',
            name: 'Alice',
            selectionToken: 'selection-tok',
            trips: [TRIP_A, TRIP_B],
          })
        }
      >
        begin-selection
      </button>
      <button
        onClick={() => auth.completeTripSelection('user-1', '+15550000001', 'Alice', 'tok-a', TRIP_A)}
      >
        select-trip-a
      </button>
      <button
        onClick={() => auth.completeTripSelection('user-1', '+15550000001', 'Alice', 'tok-b', TRIP_B)}
      >
        select-trip-b
      </button>
      <button onClick={auth.openTripSwitcher}>open-switcher</button>
      <button onClick={auth.cancelTripSwitcher}>cancel-switcher</button>
      <button onClick={auth.logout}>logout</button>
      <button onClick={() => void request('/me/trip').catch(() => {})}>protected-request</button>
      <button onClick={() => void request('/profile/user-1').catch(() => {})}>profile-request</button>
      <button onClick={() => void request('/auth/select-trip').catch(() => {})}>select-request</button>
    </div>
  );
}

function renderProbe() {
  return render(
    <AuthProvider>
      <Probe />
    </AuthProvider>
  );
}

/**
 * Mimics TripProvider: a child that fetches through the shared API client
 * from its own mount/update effect, keyed on the current session token. Its
 * effect commits in the same React flush as the parent AuthProvider's
 * effects (children run first), so it only ever sees the right
 * `Authorization` header if the token reached localStorage *before* React
 * started committing at all — i.e. synchronously inside the action that
 * changed the session, not from a `useEffect` in AuthProvider itself.
 */
function ChildThatFetchesOnTokenChange() {
  const { user } = useAuth();

  useEffect(() => {
    if (!user) return;
    void request('/probe');
  }, [user]);

  return null;
}

describe('AuthProvider trip-scoped session state', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  afterEach(() => {
    localStorage.clear();
  });

  test('completeTripSelection stores a trip-scoped authenticated user', async () => {
    const user = userEvent.setup();
    renderProbe();

    await user.click(screen.getByRole('button', { name: 'select-trip-a' }));

    expect(screen.getByTestId('logged-in')).toHaveTextContent('true');
    expect(screen.getByTestId('trip-id')).toHaveTextContent('trip-a');
    expect(screen.getByTestId('active-trip-title')).toHaveTextContent('Rio Adventure');
    expect(screen.getByTestId('role')).toHaveTextContent('traveler');
    expect(screen.getByTestId('token')).toHaveTextContent('tok-a');

    const stored = JSON.parse(localStorage.getItem('parrot_user') ?? 'null');
    expect(stored).toMatchObject({
      userId: 'user-1',
      tripId: 'trip-a',
      token: 'tok-a',
      role: 'traveler',
      activeTrip: TRIP_A,
    });
  });

  test('beginTripSelection holds a pending selection session without logging in', async () => {
    const user = userEvent.setup();
    renderProbe();

    await user.click(screen.getByRole('button', { name: 'begin-selection' }));

    expect(screen.getByTestId('pending-trips')).toHaveTextContent('2');
    expect(screen.getByTestId('logged-in')).toHaveTextContent('false');
    expect(localStorage.getItem('parrot_user')).toBeNull();
  });

  test('completeTripSelection clears a pending selection once a trip is chosen', async () => {
    const user = userEvent.setup();
    renderProbe();

    await user.click(screen.getByRole('button', { name: 'begin-selection' }));
    expect(screen.getByTestId('pending-trips')).toHaveTextContent('2');

    await user.click(screen.getByRole('button', { name: 'select-trip-a' }));

    expect(screen.getByTestId('pending-trips')).toHaveTextContent('none');
    expect(screen.getByTestId('logged-in')).toHaveTextContent('true');
  });

  test('switching trips atomically replaces the session with the new trip', async () => {
    const user = userEvent.setup();
    renderProbe();

    await user.click(screen.getByRole('button', { name: 'select-trip-a' }));
    expect(screen.getByTestId('trip-id')).toHaveTextContent('trip-a');

    await user.click(screen.getByRole('button', { name: 'select-trip-b' }));

    expect(screen.getByTestId('trip-id')).toHaveTextContent('trip-b');
    expect(screen.getByTestId('active-trip-title')).toHaveTextContent('Lisbon Kickoff');
    expect(screen.getByTestId('role')).toHaveTextContent('staff');
    expect(screen.getByTestId('token')).toHaveTextContent('tok-b');

    const stored = JSON.parse(localStorage.getItem('parrot_user') ?? 'null');
    expect(stored).toMatchObject({
      tripId: 'trip-b',
      token: 'tok-b',
      role: 'staff',
      activeTrip: TRIP_B,
    });
    expect(stored.tripId).not.toBe('trip-a');
  });

  test('openTripSwitcher and cancelTripSwitcher toggle switcher visibility without changing the session', async () => {
    const user = userEvent.setup();
    renderProbe();

    await user.click(screen.getByRole('button', { name: 'select-trip-a' }));
    await user.click(screen.getByRole('button', { name: 'open-switcher' }));

    expect(screen.getByTestId('switcher-open')).toHaveTextContent('true');
    expect(screen.getByTestId('trip-id')).toHaveTextContent('trip-a');

    await user.click(screen.getByRole('button', { name: 'cancel-switcher' }));

    expect(screen.getByTestId('switcher-open')).toHaveTextContent('false');
    expect(screen.getByTestId('trip-id')).toHaveTextContent('trip-a');
    expect(screen.getByTestId('logged-in')).toHaveTextContent('true');
  });

  test('clears a legacy parrot_user entry with no tripId instead of trusting it', () => {
    localStorage.setItem(
      'parrot_user',
      JSON.stringify({ userId: 'legacy-1', phone: '+15550000001', name: 'Legacy', token: 'old-tok', role: 'traveler' })
    );

    renderProbe();

    expect(screen.getByTestId('logged-in')).toHaveTextContent('false');
    expect(localStorage.getItem('parrot_user')).toBeNull();
  });

  test('a child effect sees the new token immediately on first login and after a trip switch', async () => {
    const seenAuthHeaders: Array<string | null> = [];
    server.use(
      http.get('http://localhost:8000/probe', ({ request: req }) => {
        seenAuthHeaders.push(req.headers.get('Authorization'));
        return HttpResponse.json({ ok: true });
      })
    );

    const user = userEvent.setup();
    render(
      <AuthProvider>
        <Probe />
        <ChildThatFetchesOnTokenChange />
      </AuthProvider>
    );

    await user.click(screen.getByRole('button', { name: 'select-trip-a' }));
    await waitFor(() => expect(seenAuthHeaders).toHaveLength(1));
    expect(seenAuthHeaders[0]).toBe('Bearer tok-a');

    await user.click(screen.getByRole('button', { name: 'select-trip-b' }));
    await waitFor(() => expect(seenAuthHeaders).toHaveLength(2));
    expect(seenAuthHeaders[1]).toBe('Bearer tok-b');
  });

  test('logout clears the session, pending selection and switcher state', async () => {
    const user = userEvent.setup();
    renderProbe();

    await user.click(screen.getByRole('button', { name: 'select-trip-a' }));
    await user.click(screen.getByRole('button', { name: 'open-switcher' }));
    await user.click(screen.getByRole('button', { name: 'logout' }));

    expect(screen.getByTestId('logged-in')).toHaveTextContent('false');
    expect(screen.getByTestId('switcher-open')).toHaveTextContent('false');
    expect(screen.getByTestId('pending-trips')).toHaveTextContent('none');
    expect(localStorage.getItem('parrot_user')).toBeNull();
  });

  test('logs out when a protected app request returns 401', async () => {
    server.use(
      http.get('http://localhost:8000/me/trip', () =>
        HttpResponse.json({ detail: 'Unauthorized' }, { status: 401 })
      )
    );
    const user = userEvent.setup();
    renderProbe();
    await user.click(screen.getByRole('button', { name: 'select-trip-a' }));
    await user.click(screen.getByRole('button', { name: 'protected-request' }));

    await waitFor(() => expect(screen.getByTestId('logged-in')).toHaveTextContent('false'));
    expect(localStorage.getItem('parrot_user')).toBeNull();
  });

  test('refreshes memberships and opens the switcher when a /me membership is revoked', async () => {
    server.use(
      http.get('http://localhost:8000/me/trip', () =>
        HttpResponse.json({ detail: 'Trip membership required' }, { status: 403 })
      ),
      http.get('http://localhost:8000/auth/trips', () =>
        HttpResponse.json({ trips: [TRIP_B] })
      )
    );
    const user = userEvent.setup();
    renderProbe();
    await user.click(screen.getByRole('button', { name: 'select-trip-a' }));
    await user.click(screen.getByRole('button', { name: 'protected-request' }));

    await waitFor(() => expect(screen.getByTestId('switcher-open')).toHaveTextContent('true'));
    expect(screen.getByTestId('logged-in')).toHaveTextContent('true');
  });

  test('enters no-trips state when revoked membership refresh returns no eligible trips', async () => {
    server.use(
      http.get('http://localhost:8000/me/trip', () =>
        HttpResponse.json({ detail: 'Trip membership required' }, { status: 403 })
      ),
      http.get('http://localhost:8000/auth/trips', () => HttpResponse.json({ trips: [] }))
    );
    const user = userEvent.setup();
    renderProbe();
    await user.click(screen.getByRole('button', { name: 'select-trip-a' }));
    await user.click(screen.getByRole('button', { name: 'protected-request' }));

    await waitFor(() => expect(screen.getByTestId('no-trips')).toHaveTextContent('true'));
    expect(screen.getByTestId('logged-in')).toHaveTextContent('false');
  });

  test('recovers a revoked membership reported by a protected /profile endpoint', async () => {
    server.use(
      http.get('http://localhost:8000/profile/user-1', () =>
        HttpResponse.json({ detail: 'Trip membership required' }, { status: 403 })
      ),
      http.get('http://localhost:8000/auth/trips', () =>
        HttpResponse.json({ trips: [TRIP_B] })
      )
    );
    const user = userEvent.setup();
    renderProbe();
    await user.click(screen.getByRole('button', { name: 'select-trip-a' }));
    await user.click(screen.getByRole('button', { name: 'profile-request' }));

    await waitFor(() => expect(screen.getByTestId('switcher-open')).toHaveTextContent('true'));
    expect(screen.getByTestId('logged-in')).toHaveTextContent('true');
  });

  test('does not recover the session for an unrelated 403 or /auth/select-trip failure', async () => {
    server.use(
      http.get('http://localhost:8000/me/trip', () =>
        HttpResponse.json({ detail: 'Validation failed' }, { status: 403 })
      ),
      http.get('http://localhost:8000/auth/select-trip', () =>
        HttpResponse.json({ detail: 'Trip not available' }, { status: 403 })
      )
    );
    const user = userEvent.setup();
    renderProbe();
    await user.click(screen.getByRole('button', { name: 'select-trip-a' }));
    await user.click(screen.getByRole('button', { name: 'protected-request' }));
    await user.click(screen.getByRole('button', { name: 'select-request' }));

    expect(screen.getByTestId('logged-in')).toHaveTextContent('true');
    expect(screen.getByTestId('switcher-open')).toHaveTextContent('false');
  });
});
