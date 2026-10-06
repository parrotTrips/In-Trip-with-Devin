import { createContext, useContext } from 'react';
import type { TripInfo, TripPhase, TripTraveler } from '../../features/trip/services/trip-api';

export interface TripContextType {
  tripInfo: TripInfo | null;
  phases: TripPhase[];
  travelers: TripTraveler[];
  idealPacePhaseId: string | null;
  completedPhaseIds: string[];
  loading: boolean;
  error: string | null;
  refetch: () => void;
}

export const TripContext = createContext<TripContextType>({
  tripInfo: null,
  phases: [],
  travelers: [],
  idealPacePhaseId: null,
  completedPhaseIds: [],
  loading: false,
  error: null,
  refetch: () => {},
});

export function useTripContext() {
  return useContext(TripContext);
}
