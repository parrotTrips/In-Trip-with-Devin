import { useState } from 'react';
import { Calendar, Loader2, LogOut, MapPin, X } from 'lucide-react';

import ParrotLogoIcon from '../../../shared/components/ParrotLogoIcon';
import { useAuth } from '../../../app/providers/auth-context';
import { selectTrip, type TripChoice } from '../services/auth-api';

export interface TripSelectorScreenProps {
  /** The eligible trips to choose from, in the order the backend returned them. */
  trips: TripChoice[];
  /** The selection or session token to call `POST /auth/select-trip` with. */
  token: string;
  /**
   * The trip the current session is scoped to, if any — used to mark it
   * "Viagem atual" in the list. Left unset (or `null`) for the first,
   * post-OTP selection, where there is no active trip yet.
   */
  activeTripId?: string | null;
  /**
   * Reused by Task 7's in-app switcher: when given, renders a "Cancelar"
   * action instead of "Sair" and calls this instead of signing out. The
   * initial post-OTP selection (this task) omits it.
   */
  onCancel?: () => void;
}

function formatDateRange(start: string | null, end: string | null) {
  if (start && end) return `${start} – ${end}`;
  return start ?? end ?? null;
}

export default function TripSelectorScreen({ trips, token, activeTripId = null, onCancel }: TripSelectorScreenProps) {
  const { completeTripSelection, logout } = useAuth();
  const [selectingId, setSelectingId] = useState<string | null>(null);
  const [error, setError] = useState('');

  const isBusy = selectingId !== null;

  const handleSelect = async (tripId: string) => {
    if (isBusy) return;
    setSelectingId(tripId);
    setError('');
    try {
      const result = await selectTrip(token, tripId);
      completeTripSelection(result.user_id, result.phone, result.name, result.access_token, result.active_trip);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to select trip');
      setSelectingId(null);
    }
  };

  return (
    <div className="min-h-dvh bg-gradient-to-b from-emerald-700 via-emerald-600 to-teal-700 flex flex-col">
      <div className="absolute top-0 left-0 right-0 h-96 overflow-hidden pointer-events-none">
        <div className="absolute top-10 -left-10 w-40 h-40 bg-emerald-500/30 rounded-full blur-3xl" />
        <div className="absolute top-20 right-0 w-32 h-32 bg-teal-400/30 rounded-full blur-3xl" />
      </div>

      <div className="relative flex-1 flex flex-col items-center justify-center px-4 py-8 safe-top safe-bottom">
        <div className="text-center mb-6">
          <ParrotLogoIcon size={56} className="mx-auto mb-3" color="#ffffff" />
          <h1 className="text-xl font-bold text-white font-[Fredoka]">Escolha sua viagem</h1>
        </div>

        <div className="w-full max-w-sm bg-white rounded-3xl shadow-2xl p-5">
          {trips.length === 0 ? (
            <p className="text-sm text-gray-500 text-center py-6">Nenhuma viagem disponível.</p>
          ) : (
            <>
              {trips.length === 1 && (
                <p className="text-xs text-gray-500 text-center mb-3">
                  Você só tem uma viagem disponível.
                </p>
              )}
              <ul className="space-y-2">
                {trips.map(trip => {
                  const isActive = trip.trip_id === activeTripId;
                  const isSelectingThis = selectingId === trip.trip_id;
                  const dateRange = formatDateRange(trip.start_date, trip.end_date);

                  return (
                    <li key={trip.trip_id}>
                      <button
                        type="button"
                        onClick={() => handleSelect(trip.trip_id)}
                        disabled={isBusy}
                        aria-busy={isSelectingThis}
                        className="w-full text-left p-4 rounded-2xl border-2 border-gray-100 hover:border-emerald-300 disabled:opacity-50 disabled:hover:border-gray-100 transition-all flex items-center justify-between gap-3"
                      >
                        <div className="min-w-0">
                          <div className="flex items-center gap-2 flex-wrap">
                            <span className="font-semibold text-gray-800 text-sm truncate">{trip.title}</span>
                            {trip.role === 'staff' && (
                              <span className="text-[10px] font-bold uppercase tracking-wide text-emerald-700 bg-emerald-100 px-2 py-0.5 rounded-full">
                                Staff
                              </span>
                            )}
                            {isActive && (
                              <span className="text-[10px] font-bold uppercase tracking-wide text-gray-500 bg-gray-100 px-2 py-0.5 rounded-full">
                                Viagem atual
                              </span>
                            )}
                          </div>
                          {trip.destination && (
                            <p className="text-xs text-gray-500 flex items-center gap-1 mt-1">
                              <MapPin size={12} className="shrink-0" />
                              <span className="truncate">{trip.destination}</span>
                            </p>
                          )}
                          {dateRange && (
                            <p className="text-xs text-gray-400 flex items-center gap-1 mt-0.5">
                              <Calendar size={12} className="shrink-0" />
                              {dateRange}
                            </p>
                          )}
                        </div>
                        {isSelectingThis && (
                          <Loader2 size={18} className="animate-spin text-emerald-600 shrink-0" />
                        )}
                      </button>
                    </li>
                  );
                })}
              </ul>
            </>
          )}

          {error && <p className="text-red-500 text-xs text-center mt-4">{error}</p>}

          <button
            type="button"
            onClick={onCancel ?? logout}
            className="w-full mt-5 py-3 text-sm text-gray-500 hover:text-emerald-600 transition-colors flex items-center justify-center gap-2"
          >
            {onCancel ? <X size={16} /> : <LogOut size={16} />}
            {onCancel ? 'Cancelar' : 'Sair'}
          </button>
        </div>
      </div>
    </div>
  );
}
