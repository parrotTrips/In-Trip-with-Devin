import { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  ArrowLeft,
  Clock,
  MapPin,
  Star,
  ChevronRight,
  Camera,
  Check,
  DollarSign,
  ImagePlus,
} from 'lucide-react';
import {
  getMyTripPhaseDetail,
  type Activity,
  type TripPhaseDetail,
} from '../services/trip-api';

function ActivityCard({ activity, index }: { activity: Activity; index: number }) {
  const [expanded, setExpanded] = useState(false);

  const typeConfig: Record<string, { label: string; color: string; icon: React.ReactNode }> = {
    included: { label: 'Included', color: 'bg-emerald-100 text-emerald-700', icon: <Check size={12} /> },
    optional: { label: 'Optional', color: 'bg-amber-100 text-amber-700', icon: <Star size={12} /> },
    suggested: { label: 'Suggested', color: 'bg-blue-100 text-blue-700', icon: <Star size={12} /> },
    logistics: { label: 'Logistics', color: 'bg-gray-100 text-gray-700', icon: <MapPin size={12} /> },
  };

  const config = typeConfig[activity.activity_type] ?? typeConfig.included;

  function formatTime(startsAt: string | null, durationMinutes: number | null): string {
    if (!startsAt) return '—';
    const d = new Date(startsAt);
    const hours = d.getHours();
    const minutes = d.getMinutes().toString().padStart(2, '0');
    const ampm = hours >= 12 ? 'PM' : 'AM';
    const h = hours % 12 || 12;
    const base = `${h}:${minutes} ${ampm}`;
    if (!durationMinutes) return base;
    const hrs = Math.floor(durationMinutes / 60);
    const mins = durationMinutes % 60;
    const dur = hrs > 0 ? (mins > 0 ? `${hrs}h ${mins}min` : `${hrs}h`) : `${mins}min`;
    return `${base} · ~${dur}`;
  }

  return (
    <div className="relative">
      <div className="absolute left-6 top-0 bottom-0 w-0.5 bg-gray-200" />

      <div className="relative flex gap-3">
        <div className="flex-shrink-0 w-12 flex flex-col items-center">
          <div className={`relative z-10 w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold text-white ${
            activity.activity_type === 'included' ? 'bg-emerald-500'
            : activity.activity_type === 'optional' ? 'bg-amber-500'
            : activity.activity_type === 'logistics' ? 'bg-gray-500'
            : 'bg-blue-500'
          }`}>
            {index + 1}
          </div>
        </div>

        <div className="flex-1 pb-6">
          <button
            onClick={() => setExpanded(!expanded)}
            className="w-full text-left bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden hover:shadow-md transition-shadow"
          >
            <div className="p-4">
              <div className="flex items-center gap-2 mb-2">
                <span className={`px-2.5 py-1 rounded-full text-xs font-semibold flex items-center gap-1 ${config.color}`}>
                  {config.icon}
                  {config.label}
                </span>
                {activity.amount_brl !== null && (
                  <span className="text-xs font-semibold text-gray-600 flex items-center gap-1">
                    <DollarSign size={12} />
                    R$ {activity.amount_brl}
                  </span>
                )}
              </div>

              <h4 className="font-semibold text-gray-800 text-sm font-[Fredoka]">{activity.name}</h4>

              <div className="flex items-center gap-1 mt-2 text-xs text-gray-500">
                <Clock size={12} />
                <span>{formatTime(activity.starts_at, activity.duration_minutes)}</span>
              </div>

              <div className="text-sm text-gray-600 mt-2 leading-relaxed whitespace-pre-line">
                {activity.short_description}
              </div>

              {expanded && activity.practical_info && (
                <div className="mt-3 pt-3 border-t border-gray-100">
                  <div className="flex items-start gap-2 text-sm text-gray-600">
                    <MapPin size={14} className="text-emerald-500 flex-shrink-0 mt-0.5" />
                    <div className="whitespace-pre-line">{activity.practical_info}</div>
                  </div>
                  {activity.amount_brl !== null && activity.activity_type === 'optional' && (
                    <button className="mt-3 w-full py-2.5 bg-amber-500 text-white rounded-xl font-semibold text-sm hover:bg-amber-600 transition-colors">
                      Book Now — R$ {activity.amount_brl}
                    </button>
                  )}
                </div>
              )}

              <div className="flex items-center justify-end mt-2 text-xs text-blue-500 font-medium">
                <span>{expanded ? 'Show less' : 'See details'}</span>
                <ChevronRight size={14} className={`transition-transform ${expanded ? 'rotate-90' : ''}`} />
              </div>
            </div>
          </button>
        </div>
      </div>
    </div>
  );
}

export default function DayDetails() {
  const { dayId } = useParams<{ dayId: string }>();
  const navigate = useNavigate();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [phase, setPhase] = useState<TripPhaseDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!dayId) return;
    setLoading(true);
    setError(null);
    getMyTripPhaseDetail(dayId)
      .then(data => setPhase(data))
      .catch(e => setError(e instanceof Error ? e.message : 'Erro ao carregar dia'))
      .finally(() => setLoading(false));
  }, [dayId]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="w-8 h-8 border-4 border-emerald-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (error || !phase || phase.phase_type !== 'in-trip') {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center gap-4 px-6">
        <div className="w-14 h-14 bg-red-100 rounded-full flex items-center justify-center text-2xl">⚠️</div>
        <p className="text-gray-700 font-semibold text-center">Dia não encontrado</p>
        <p className="text-gray-400 text-sm text-center">{error}</p>
        <button onClick={() => navigate(-1)} className="text-emerald-500 text-sm font-medium">Voltar</button>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 pb-8">
      <div className="bg-gradient-to-br from-emerald-700 via-emerald-600 to-teal-600 text-white">
        <div className="flex items-center gap-3 px-4 pt-12 pb-2">
          <button
            onClick={() => navigate(-1)}
            className="p-2 -ml-2 rounded-full hover:bg-white/10 transition-colors"
          >
            <ArrowLeft size={22} />
          </button>
          <div className="flex-1">
            <h1 className="text-xl font-bold font-[Fredoka]">
              {phase.subtitle ? `${phase.title} — ${phase.subtitle}` : phase.title}
            </h1>
            <p className="text-emerald-100 text-sm mt-0.5">{phase.short_description}</p>
          </div>
        </div>

        <div className="px-4 pb-2 mt-2">
          <div className="flex items-center gap-1.5 text-emerald-100 text-xs">
            <Clock size={14} />
            <span>{phase.activities.length} activities</span>
          </div>
        </div>

      </div>

      <div className="px-4 pt-6">
        <h2 className="text-lg font-bold text-gray-800 font-[Fredoka] mb-4">Today's Itinerary</h2>
        <div>
          {phase.activities.map((activity, index) => (
            <ActivityCard key={activity.id} activity={activity} index={index} />
          ))}
        </div>
      </div>

      <div className="px-4 mt-6">
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
          <div className="p-4 border-b border-gray-50 flex items-center justify-between">
            <h3 className="font-semibold text-gray-800 font-[Fredoka]">Group Album</h3>
            <button
              onClick={() => fileInputRef.current?.click()}
              className="flex items-center gap-1.5 text-xs font-semibold text-emerald-600 bg-emerald-50 px-3 py-1.5 rounded-full hover:bg-emerald-100 transition-colors"
            >
              <ImagePlus size={14} />
              Add Photo
            </button>
            <input ref={fileInputRef} type="file" accept="image/*" className="hidden" />
          </div>
          <div className="p-8 text-center">
            <div className="w-16 h-16 mx-auto bg-gray-100 rounded-2xl flex items-center justify-center mb-3">
              <Camera size={24} className="text-gray-400" />
            </div>
            <p className="text-sm text-gray-400">No photos yet. Be the first to share!</p>
          </div>
        </div>
      </div>
    </div>
  );
}
