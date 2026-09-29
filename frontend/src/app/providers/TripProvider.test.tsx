import { act, render, screen } from '@testing-library/react';
import posthog from 'posthog-js';
import { vi } from 'vitest';

import { TripProvider } from './TripProvider';
import { useTripContext } from './trip-context';
import {
  getMyTrip,
  getMyTripPhases,
  getMyTripTravelers,
  type TripInfo,
  type TripPhase,
  type TripTraveler,
} from '../../features/trip/services/trip-api';

vi.mock('../../features/trip/services/trip-api', () => ({
  getMyTrip: vi.fn(),
  getMyTripPhases: vi.fn(),
  getMyTripTravelers: vi.fn(),
}));

vi.mock('posthog-js', () => ({
  default: { register: vi.fn(), unregister: vi.fn() },
}));

function deferred<T>() {
  let resolve!: (value: T) => void;
  const promise = new Promise<T>(res => { resolve = res; });
  return { promise, resolve };
}

function Probe() {
  const { tripInfo } = useTripContext();
  return <div data-testid="trip-title">{tripInfo?.title ?? 'none'}</div>;
}

function batch(id: string) {
  const trip = deferred<{ trip: TripInfo | null }>();
  const phases = deferred<{ wetravel_trip_uuid: string; phases: TripPhase[]; ideal_pace_phase_id: null }>();
  const travelers = deferred<{ travelers: TripTraveler[] }>();
  vi.mocked(getMyTrip).mockReturnValueOnce(trip.promise);
  vi.mocked(getMyTripPhases).mockReturnValueOnce(phases.promise);
  vi.mocked(getMyTripTravelers).mockReturnValueOnce(travelers.promise);
  return {
    resolve() {
      trip.resolve({ trip: { wetravel_trip_uuid: id, title: id, destination: id, start_date: '', end_date: '', url: null, service_agreement_url: null, trip_mode: 'pre-trip' } });
      phases.resolve({ wetravel_trip_uuid: id, phases: [], ideal_pace_phase_id: null });
      travelers.resolve({ travelers: [] });
    },
  };
}

describe('TripProvider stale request protection', () => {
  beforeEach(() => vi.clearAllMocks());

  test('a slow old trip cannot overwrite state or analytics from the new trip', async () => {
    const tripA = batch('trip-a');
    const { rerender } = render(<TripProvider key="trip-a"><Probe /></TripProvider>);
    const tripB = batch('trip-b');
    rerender(<TripProvider key="trip-b"><Probe /></TripProvider>);

    await act(async () => tripB.resolve());
    expect(screen.getByTestId('trip-title')).toHaveTextContent('trip-b');
    expect(posthog.register).toHaveBeenLastCalledWith({ viagem_id: 'trip-b', modo_viagem: 'pre-trip' });

    await act(async () => tripA.resolve());
    expect(screen.getByTestId('trip-title')).toHaveTextContent('trip-b');
    expect(posthog.register).not.toHaveBeenCalledWith({ viagem_id: 'trip-a', modo_viagem: 'pre-trip' });
  });

  test('does not register analytics when a request resolves after unmount', async () => {
    const tripA = batch('trip-a');
    const view = render(<TripProvider><Probe /></TripProvider>);
    view.unmount();

    await act(async () => tripA.resolve());
    expect(posthog.register).not.toHaveBeenCalled();
  });
});
