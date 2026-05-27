import { useCallback, useEffect, useState, type ReactNode } from 'react';
import { getMyTrip, getMyTripPhases, getMyTripTravelers, type TripInfo, type TripPhase, type TripTraveler } from '../../features/trip/services/trip-api';
import { TripContext } from './trip-context';

export function TripProvider({ children }: { children: ReactNode }) {
  const [tripInfo, setTripInfo] = useState<TripInfo | null>(null);
  const [phases, setPhases] = useState<TripPhase[]>([]);
  const [travelers, setTravelers] = useState<TripTraveler[]>([]);
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
      setTravelers(travelersResult.travelers);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Erro ao carregar dados da viagem');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchAll();
  }, [fetchAll]);

  return (
    <TripContext.Provider value={{ tripInfo, phases, travelers, loading, error, refetch: fetchAll }}>
      {children}
    </TripContext.Provider>
  );
}
