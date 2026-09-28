import { useEffect, useRef, useState } from 'react';
import { Calendar, Loader2, LogOut, MapPin, X } from 'lucide-react';

import ParrotLogoIcon from '../../../shared/components/ParrotLogoIcon';
import { useAuth } from '../../../app/providers/auth-context';
import { ApiError } from '../../../shared/api/client';
import { selectTrip, type TripChoice } from '../services/auth-api';

/**
 * Known raw English messages the backend sends for `POST /auth/select-trip`,
 * mapped to pt-BR — this screen is otherwise entirely in Portuguese. Any
 * other/unrecognized detail is shown as-is rather than replaced with a vague
 * generic message, so a real (if untranslated) backend error is never hidden.
 */
const PT_BR_ERROR_MESSAGES: Record<string, string> = {
  Unauthorized: 'Sua sessão expirou. Faça login novamente.',
  'Trip not available': 'Essa viagem não está mais disponível para você.',
};

function toDisplayMessage(err: unknown): string {
  if (err instanceof Error && err.message) {
    return PT_BR_ERROR_MESSAGES[err.message] ?? err.message;
  }
  return 'Não foi possível selecionar a viagem. Tente novamente.';
}

export interface TripSelectorScreenProps {
  /** The eligible trips to choose from, in the order the backend returned them. */
  trips: TripChoice[];
  /** The selection or session token to call `POST /auth/select-trip` with. */
  token: string;
  /**
   * The trip the current session is scoped to, if any — used to mark it
   * "Viagem ativa" in the list. Left unset (or `null`) for the first,
   * post-OTP selection, where there is no active session yet. Distinct from
   * a trip's own `is_current` ("Em andamento"): this marks *which* trip the
   * session token is scoped to, not whether that trip is happening now.
   */
  activeTripId?: string | null;
  /**
   * Reused by Task 7's in-app switcher: when given, renders a "Cancelar"
   * action instead of "Sair" and calls this instead of signing out. The
   * initial post-OTP selection (this task) omits it.
   */
  onCancel?: () => void;
}

const PT_MONTHS_ABBR = ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez'];

function parseIsoDate(value: string) {
  const match = value.match(/^(\d{4})-(\d{2})-(\d{2})$/);
  if (!match) return null;
  const [, year, month, day] = match;
  const monthIndex = Number(month) - 1;
  if (monthIndex < 0 || monthIndex > 11) return null;
  return { day: String(Number(day)), month: PT_MONTHS_ABBR[monthIndex], year };
}

/** Formats a trip's date range in pt-BR (e.g. "10 jan – 20 jan 2026"), tolerating missing or malformed dates. */
function formatDateRange(start: string | null, end: string | null) {
  const startParts = start ? parseIsoDate(start) : null;
  const endParts = end ? parseIsoDate(end) : null;

  if (startParts && endParts) {
    return startParts.year === endParts.year
      ? `${startParts.day} ${startParts.month} – ${endParts.day} ${endParts.month} ${endParts.year}`
      : `${startParts.day} ${startParts.month} ${startParts.year} – ${endParts.day} ${endParts.month} ${endParts.year}`;
  }
  if (startParts) return `${startParts.day} ${startParts.month} ${startParts.year}`;
  if (endParts) return `${endParts.day} ${endParts.month} ${endParts.year}`;
  return null;
}

export default function TripSelectorScreen({ trips, token, activeTripId = null, onCancel }: TripSelectorScreenProps) {
  const { completeTripSelection, logout } = useAuth();
  const [selectingId, setSelectingId] = useState<string | null>(null);
  const [error, setError] = useState('');

  const isBusy = selectingId !== null;

  // Guards against a select-trip response that resolves *after* the person
  // has already backed out (Sair/Cancelar) or this screen has unmounted —
  // without this, a late response would still call completeTripSelection
  // and silently (re)establish a session the person just signed out of.
  const isLiveRef = useRef(true);
  useEffect(() => {
    isLiveRef.current = true;
    return () => {
      isLiveRef.current = false;
    };
  }, []);

  const handleSelect = async (tripId: string) => {
    if (isBusy) return;
    setSelectingId(tripId);
    setError('');
    try {
      const result = await selectTrip(token, tripId);
      if (!isLiveRef.current) return;
      completeTripSelection(result.user_id, result.phone, result.name, result.access_token, result.active_trip);
    } catch (err) {
      if (!isLiveRef.current) return;
      const status = err instanceof ApiError ? err.status : null;
      if (!onCancel && status === 401) {
        // Initial post-OTP selection (no active session to recover, unlike
        // the in-app switcher — see AuthProvider's own 401 handling there):
        // the selection token itself has expired or is invalid. There is
        // nothing to retry against, so go back to OTP login instead of
        // leaving the person stuck re-submitting a dead token forever.
        logout();
        return;
      }
      setError(toDisplayMessage(err));
      setSelectingId(null);
    }
  };

  const handleBack = () => {
    // Mark stale immediately so a select-trip call already in flight can't
    // complete the session after the person has backed out.
    isLiveRef.current = false;
    (onCancel ?? logout)();
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
                  const isActiveSession = trip.trip_id === activeTripId;
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
                            {trip.is_current && (
                              <span className="text-[10px] font-bold uppercase tracking-wide text-sky-700 bg-sky-100 px-2 py-0.5 rounded-full">
                                Em andamento
                              </span>
                            )}
                            {isActiveSession && (
                              <span className="text-[10px] font-bold uppercase tracking-wide text-gray-500 bg-gray-100 px-2 py-0.5 rounded-full">
                                Viagem ativa
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
                          <Loader2
                            size={18}
                            role="status"
                            aria-label="Selecionando viagem"
                            className="animate-spin text-emerald-600 shrink-0"
                          />
                        )}
                      </button>
                    </li>
                  );
                })}
              </ul>
            </>
          )}

          {error && (
            <p role="alert" className="text-red-500 text-xs text-center mt-4">{error}</p>
          )}

          <button
            type="button"
            onClick={handleBack}
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
