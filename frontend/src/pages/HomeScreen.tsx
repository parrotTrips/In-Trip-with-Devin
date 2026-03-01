import { useNavigate } from 'react-router-dom';
import {
  getAllPhases,
  getTravelersAtPhase,
  currentUserPhaseId,
  parrotPhaseId,
  tripName,
  tripDates,
  isTripDay,
} from '../data/tripData';
import TopBar from '../components/TopBar';
import ProgressBar from '../components/ProgressBar';
import ParrotMascot from '../components/ParrotMascot';
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
  Lock,
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

export default function HomeScreen() {
  const navigate = useNavigate();
  const allPhases = getAllPhases();

  const currentUserIdx = allPhases.findIndex(p => p.id === currentUserPhaseId);

  const handlePhaseClick = (phaseId: string) => {
    const phase = allPhases.find(p => p.id === phaseId);
    if (!phase) return;
    if (phase.locked) return;
    if (isTripDay(phase)) {
      navigate(`/day/${phaseId}`);
    } else {
      navigate(`/phase/${phaseId}`);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-sky-50 via-white to-emerald-50 pb-20">
      <TopBar title={tripName} />

      {/* Hero Section */}
      <div className="pt-14">
        <div className="relative overflow-hidden bg-gradient-to-br from-emerald-700 via-emerald-600 to-teal-600 px-5 py-6">
          {/* Decorative background elements */}
          <div className="absolute top-0 right-0 w-32 h-32 bg-emerald-500/30 rounded-full -translate-y-1/2 translate-x-1/2" />
          <div className="absolute bottom-0 left-0 w-24 h-24 bg-teal-500/20 rounded-full translate-y-1/2 -translate-x-1/2" />

          <div className="relative z-10">
            <h2 className="text-2xl font-bold text-white font-[Fredoka] leading-tight">
              Your Brazilian<br />Adventure! 🇧🇷
            </h2>
            <p className="text-emerald-100 text-sm mt-1">{tripDates}</p>
          </div>

          <div className="relative z-10 mt-1">
            <ProgressBar />
          </div>
        </div>
      </div>

      {/* Phase Labels */}
      <div className="flex justify-center gap-6 py-3 border-b border-gray-100 bg-white/80 backdrop-blur-sm">
        <div className="flex items-center gap-1.5">
          <div className="w-3 h-3 rounded-full bg-blue-500" />
          <span className="text-xs font-medium text-gray-500">Pre-Trip</span>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="w-3 h-3 rounded-full bg-emerald-500" />
          <span className="text-xs font-medium text-gray-500">In-Trip</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="text-xs">🦜</span>
          <span className="text-xs font-medium text-gray-500">Ideal pace</span>
        </div>
      </div>

      {/* Game Board Path */}
      <div className="relative px-4 py-6">
        {/* Winding path background */}
        <div className="absolute left-1/2 top-0 bottom-0 w-1 bg-gradient-to-b from-blue-200 via-emerald-200 to-emerald-300 -translate-x-1/2 rounded-full" />

        <div className="relative space-y-4">
          {allPhases.map((phase, index) => {
            const isLeft = index % 2 === 0;
            const isCurrentUser = phase.id === currentUserPhaseId;
            const isParrotHere = phase.id === parrotPhaseId;
            const isPast = index < currentUserIdx;
            const isCurrent = index === currentUserIdx;
            const isPreTrip = phase.type === 'pre-trip';
            const travelersHere = getTravelersAtPhase(phase.id);

            return (
              <div key={phase.id} className="relative">
                {/* Connecting dot on the center path */}
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

                {/* Phase card */}
                <div
                  className={`relative ${isLeft ? 'mr-auto pr-4 ml-2' : 'ml-auto pl-4 mr-2'} w-5/12`}
                  style={{ [isLeft ? 'marginRight' : 'marginLeft']: '52%' }}
                >
                  <button
                    onClick={() => handlePhaseClick(phase.id)}
                    className={`w-full rounded-2xl border-2 p-3 transition-all duration-300 ${phase.locked ? 'opacity-60 cursor-default' : 'hover:scale-105 active:scale-95'} ${
                      phase.locked
                        ? 'bg-gray-100 border-gray-300'
                        : isPast
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
                    {/* Parrot indicator */}
                    {isParrotHere && (
                      <div className={`absolute -top-3 ${isLeft ? '-right-2' : '-left-2'}`}>
                        <ParrotMascot
                          size={36}
                          showSpeech
                          speechText="You should be here!"
                        />
                      </div>
                    )}

                    {/* Phase icon */}
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
                      {iconMap[phase.icon] || <FileText size={20} />}
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

                    {/* Locked badge */}
                    {phase.locked && (
                      <div className="absolute -top-1 -right-1 w-5 h-5 bg-gray-400 rounded-full flex items-center justify-center">
                        <Lock size={10} className="text-white" />
                      </div>
                    )}

                    {/* Completed badge */}
                    {!phase.locked && isPast && (
                      <div className="absolute -top-1 -right-1 w-5 h-5 bg-emerald-500 rounded-full flex items-center justify-center">
                        <span className="text-white text-xs">✓</span>
                      </div>
                    )}

                    {/* Current user indicator */}
                    {isCurrentUser && (
                      <div className="mt-2 flex items-center gap-1 text-xs text-amber-200">
                        <span>📍</span>
                        <span className="font-medium">You are here</span>
                      </div>
                    )}
                  </button>

                  {/* Travelers avatars */}
                  {travelersHere.length > 0 && (
                    <div className={`flex -space-x-2 mt-2 ${isLeft ? '' : 'justify-end'}`}>
                      {travelersHere.slice(0, 4).map((t) => (
                        <img
                          key={t.id}
                          src={t.avatar}
                          alt={t.name}
                          className="w-7 h-7 rounded-full border-2 border-white shadow-sm object-cover"
                          title={t.name}
                        />
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
    </div>
  );
}
