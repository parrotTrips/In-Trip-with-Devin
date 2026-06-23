import { useNavigate } from 'react-router-dom';
import { useTripContext } from '../../../app/providers/trip-context';
import { useAuth } from '../../../app/providers/auth-context';
import { type TripPhase } from '../services/trip-api';
import ParrotMascot from '../../../shared/components/ParrotMascot';
import ProgressBar from '../../../shared/components/ProgressBar';
import TopBar from '../../../shared/components/TopBar';
import {
  FileText,
  Syringe,
  Luggage,
  PlaneLanding,
  Mountain,
  Sun,
  ShieldCheck,
  Flame,
  Landmark,
  Ship,
  Palmtree,
  Bus,
  Plane,
  Sailboat,
} from 'lucide-react';

const iconMap: Record<string, React.ReactNode> = {
  passport: <ShieldCheck size={20} />,
  syringe: <Syringe size={20} />,
  luggage: <Luggage size={20} />,
  'file-text': <FileText size={20} />,
  'plane-landing': <PlaneLanding size={20} />,
  mountain: <Mountain size={20} />,
  sun: <Sun size={20} />,
  flame: <Flame size={20} />,
  landmark: <Landmark size={20} />,
  ship: <Ship size={20} />,
  sailboat: <Sailboat size={20} />,
  palmtree: <Palmtree size={20} />,
  bus: <Bus size={20} />,
  plane: <Plane size={20} />,
};

function formatDateRange(start: string, end: string): string {
  const s = new Date(start + 'T12:00:00');
  const e = new Date(end + 'T12:00:00');
  const monthDay: Intl.DateTimeFormatOptions = { month: 'short', day: 'numeric' };
  return `${s.toLocaleDateString('en-US', monthDay)} — ${e.toLocaleDateString('en-US', { ...monthDay, year: 'numeric' })}`;
}


export default function HomeScreen() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const { tripInfo, phases, travelers, idealPacePhaseId, loading, error } = useTripContext();

  const currentUserPhaseId = travelers.find(t => t.id === user?.userId)?.current_phase_id ?? null;

  const isInTrip = tripInfo?.trip_mode === 'in-trip';

  const progressPhases = isInTrip
    ? phases.filter(p => p.phase_type === 'in-trip')
    : phases.filter(p => p.phase_type === 'pre-trip');

  const totalPhases = progressPhases.length;

  // completedCount = number of phases completed before the current one.
  // findIndex returns the index of the FIRST incomplete phase (= count of completed phases).
  // null → user has no phase assigned yet → 0 completed.
  // -1  → currentUserPhaseId not in progressPhases (e.g. all pre-trip done, pointer is an
  //        in-trip day) OR all in-trip phases started (backend returns last phase) → all complete.
  const rawUserIdx = currentUserPhaseId === null
    ? 0
    : progressPhases.findIndex(p => p.id === currentUserPhaseId);
  const completedCount = rawUserIdx === -1 ? totalPhases : rawUserIdx;

  const now = new Date();
  const dateBasedCount = isInTrip
    ? progressPhases.filter(p => p.starts_at && new Date(p.starts_at) <= now).length
    : 0;
  const userCompletedCount = isInTrip ? Math.min(dateBasedCount, totalPhases) : completedCount;

  const displayTitle = tripInfo?.title ?? 'Sua Viagem';
  const displayDates = tripInfo
    ? formatDateRange(tripInfo.start_date, tripInfo.end_date)
    : '';

  const handlePhaseClick = (phase: TripPhase) => {
    if (phase.phase_type === 'in-trip') {
      navigate(`/day/${phase.id}`);
    } else {
      navigate(`/phase/${phase.id}`);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-sky-50 via-white to-emerald-50 pb-20">
        <TopBar title="Carregando..." />
        <div className="pt-14 flex flex-col items-center justify-center h-64 gap-3">
          <div className="w-8 h-8 border-4 border-emerald-500 border-t-transparent rounded-full animate-spin" />
          <p className="text-gray-400 text-sm">Carregando sua viagem...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-sky-50 via-white to-emerald-50 pb-20">
        <TopBar title="Parrot Trips" />
        <div className="pt-14 flex flex-col items-center justify-center h-64 gap-4 px-6">
          <div className="w-14 h-14 bg-red-100 rounded-full flex items-center justify-center text-2xl">⚠️</div>
          <p className="text-gray-700 font-semibold text-center">Não conseguimos carregar sua viagem</p>
          <p className="text-gray-400 text-sm text-center">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-sky-50 via-white to-emerald-50 pb-20">
      <TopBar title={displayTitle} />

      {/* Hero Section */}
      <div className="pt-14">
        <div className="relative overflow-hidden bg-gradient-to-br from-emerald-700 via-emerald-600 to-teal-600 px-5 py-6">
          <div className="absolute top-0 right-0 w-32 h-32 bg-emerald-500/30 rounded-full -translate-y-1/2 translate-x-1/2" />
          <div className="absolute bottom-0 left-0 w-24 h-24 bg-teal-500/20 rounded-full translate-y-1/2 -translate-x-1/2" />

          <div className="relative z-10">
            <h2 className="text-2xl font-bold text-white font-[Fredoka] leading-tight">
              {displayTitle || 'Sua Viagem'}
            </h2>
            {displayDates && <p className="text-emerald-100 text-sm mt-1">{displayDates}</p>}
          </div>

          <div className="relative z-10 mt-1">
            <div className="flex items-center px-4 pb-1">
              <span className="text-xs font-semibold text-emerald-200 uppercase tracking-wide">
                {isInTrip ? '🗺 In-Trip' : '📋 Pre-Trip'}
              </span>
            </div>
            <ProgressBar
              totalPhases={totalPhases}
              completedCount={userCompletedCount}
            />
          </div>
        </div>
      </div>

      {phases.length === 0 ? (
        <div className="flex flex-col items-center justify-center h-48 gap-3 px-6">
          <p className="text-gray-400 text-sm text-center">Nenhuma fase encontrada para esta viagem.</p>
        </div>
      ) : (
        /* Game Board Path */
        <div className="relative px-4 py-6">
          <div className="absolute left-1/2 top-0 bottom-0 w-1 bg-gradient-to-b from-blue-200 via-emerald-200 to-emerald-300 -translate-x-1/2 rounded-full" />

          <div className="relative space-y-4">
            {phases.map((phase, index) => {
              const isLeft = index % 2 === 0;
              const isCurrentUser = phase.id === currentUserPhaseId;
              const isParrotHere = !isInTrip && !!idealPacePhaseId && phase.id === idealPacePhaseId;
              const phaseProgressIdx = progressPhases.findIndex(p => p.id === phase.id);
              const isPast = isInTrip
                ? (phaseProgressIdx >= 0 && phaseProgressIdx < userCompletedCount)
                : (phaseProgressIdx >= 0 && currentUserPhaseId !== null && phaseProgressIdx < completedCount);
              const isCurrent = phase.id === currentUserPhaseId;
              const isPreTrip = phase.phase_type === 'pre-trip';
              const travelersHere = travelers.filter(t => t.current_phase_id === phase.id);

              return (
                <div key={phase.id} className="relative">
                  <div className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 z-10">
                    <div
                      className={`w-4 h-4 rounded-full border-2 ${
                        isPast
                          ? 'bg-emerald-500 border-emerald-600'
                          : isCurrent
                            ? 'bg-amber-400 border-amber-500 animate-pulse'
                            : 'bg-white border-gray-300'
                      }`}
                    />
                  </div>

                  <div
                    className={`relative ${isLeft ? 'mr-auto pr-4 ml-2' : 'ml-auto pl-4 mr-2'} w-5/12`}
                    style={{ [isLeft ? 'marginRight' : 'marginLeft']: '52%' }}
                  >
                    <button
                      onClick={() => handlePhaseClick(phase)}
                      className={`w-full rounded-2xl border-2 p-3 transition-all duration-300 hover:scale-105 active:scale-95 ${
                        isPast
                          ? isPreTrip
                            ? 'bg-blue-50 border-blue-200'
                            : 'bg-emerald-50 border-emerald-200'
                          : isCurrent
                            ? isPreTrip
                              ? 'bg-blue-500 border-blue-600 shadow-lg shadow-blue-200'
                              : 'bg-emerald-500 border-emerald-600 shadow-lg shadow-emerald-200'
                            : 'bg-white border-gray-200 hover:border-gray-300'
                      }`}
                    >
                      {isParrotHere && (
                        <div className={`absolute -top-3 ${isLeft ? '-right-2' : '-left-2'}`}>
                          <ParrotMascot
                            size={36}
                            showSpeech
                            speechText="You should be here!"
                          />
                        </div>
                      )}

                      <div
                        className={`w-10 h-10 rounded-xl flex items-center justify-center mb-2 ${
                          isPast
                            ? isPreTrip
                              ? 'bg-blue-100 text-blue-600'
                              : 'bg-emerald-100 text-emerald-600'
                            : isCurrent
                              ? 'bg-white/20 text-white'
                              : isPreTrip
                                ? 'bg-blue-50 text-blue-400'
                                : 'bg-emerald-50 text-emerald-400'
                        }`}
                      >
                        {iconMap[phase.icon ?? ''] || <FileText size={20} />}
                      </div>

                      <h3
                        className={`font-semibold text-sm font-[Fredoka] ${
                          isPast
                            ? isPreTrip ? 'text-blue-700' : 'text-emerald-700'
                            : isCurrent
                              ? 'text-white'
                              : 'text-gray-700'
                        }`}
                      >
                        {phase.title}
                      </h3>
                      {phase.subtitle && (
                        <p
                          className={`text-xs mt-0.5 ${
                            isPast
                              ? isPreTrip ? 'text-blue-500' : 'text-emerald-500'
                              : isCurrent
                                ? 'text-white/80'
                                : 'text-gray-400'
                          }`}
                        >
                          {phase.subtitle}
                        </p>
                      )}

                      {isPast && (
                        <div className="absolute -top-1 -right-1 w-5 h-5 bg-emerald-500 rounded-full flex items-center justify-center">
                          <span className="text-white text-xs">✓</span>
                        </div>
                      )}

                      {isCurrentUser && (
                        <div className="mt-2 flex items-center gap-1 text-xs text-amber-200">
                          <span>📍</span>
                          <span className="font-medium">You are here</span>
                        </div>
                      )}
                    </button>

                    {travelersHere.length > 0 && (
                      <div className={`flex -space-x-2 mt-2 ${isLeft ? '' : 'justify-end'}`}>
                        {travelersHere.slice(0, 4).map((t) => (
                          <div
                            key={t.id}
                            className="w-7 h-7 rounded-full border-2 border-white shadow-sm bg-emerald-400 flex items-center justify-center"
                            title={t.name ?? t.phone}
                          >
                            <span className="text-white text-xs font-bold">
                              {(t.name ?? t.phone).charAt(0).toUpperCase()}
                            </span>
                          </div>
                        ))}
                        {travelersHere.length > 4 && (
                          <div className="w-7 h-7 rounded-full bg-gray-200 border-2 border-white flex items-center justify-center">
                            <span className="text-xs font-bold text-gray-500">
                              +{travelersHere.length - 4}
                            </span>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
