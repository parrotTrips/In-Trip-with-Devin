import { useCallback, useEffect, useState, type ReactNode } from 'react';
import posthog from 'posthog-js';
import { getMyTrip, getMyTripPhases, getMyTripTravelers, type TripInfo, type TripPhase, type TripTraveler } from '../../features/trip/services/trip-api';
import { TripContext } from './trip-context';

function clearTripAnalyticsContext() {
  posthog.unregister('viagem_id');
  posthog.unregister('modo_viagem');
}

export function TripProvider({ children }: { children: ReactNode }) {
  const [tripInfo, setTripInfo] = useState<TripInfo | null>(null);
  const [phases, setPhases] = useState<TripPhase[]>([]);
  const [travelers, setTravelers] = useState<TripTraveler[]>([]);
  const [idealPacePhaseId, setIdealPacePhaseId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchAll = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [tripResult, phasesResult, travelersResult] = await Promise.all([
        getMyTrip(),
        getMyTripPhases(),
        getMyTripTravelers(),
      ]);
      setTripInfo(tripResult.trip);
      setPhases(phasesResult.phases);
      setIdealPacePhaseId(phasesResult.ideal_pace_phase_id ?? null);
      setTravelers(travelersResult.travelers);
      clearTripAnalyticsContext();
      if (tripResult.trip) {
        posthog.register({ viagem_id: tripResult.trip.wetravel_trip_uuid, modo_viagem: tripResult.trip.trip_mode });
      }
    } catch (e) {
      setTripInfo(null);
      clearTripAnalyticsContext();
      setError(e instanceof Error ? e.message : 'Erro ao carregar dados da viagem');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchAll();
    return clearTripAnalyticsContext;
  }, [fetchAll]);

  return (
    <TripContext.Provider value={{ tripInfo, phases, travelers, idealPacePhaseId, loading, error, refetch: fetchAll }}>
      {children}
    </TripContext.Provider>
  );
}
