import { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  getPhaseById,
  getTravelersAtPhase,
} from '../data/tripData';
import {
  ArrowLeft,
  CheckCircle2,
  Circle,
  ExternalLink,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';
import { useAuth } from '../../../app/providers/auth-context';
import {
  updateChecklistItem as apiUpdateChecklist,
  getChecklistProgress,
  updatePhaseCompletion,
} from '../services/trip-api';

const TRIP_ID = 'ross26';

export default function PhaseDetails() {
  const { phaseId } = useParams<{ phaseId: string }>();
  const navigate = useNavigate();
  const { user } = useAuth();
  const phase = phaseId ? getPhaseById(phaseId) : undefined;
  const [isCompleted, setIsCompleted] = useState(phase?.completed || false);
  const [checklist, setChecklist] = useState(phase?.checklist || []);
  const [showDetails, setShowDetails] = useState(true);
  const travelers = phaseId ? getTravelersAtPhase(phaseId) : [];

  const loadChecklistProgress = useCallback(async () => {
    if (!user || !phaseId) return;
    try {
      const data = await getChecklistProgress(TRIP_ID, user.userId);
      const phaseProgress = data.progress[phaseId] || {};
      setChecklist(prev =>
        prev.map(item => ({
          ...item,
          completed: phaseProgress[item.id] ?? item.completed,
        }))
      );
    } catch {
      // silently fail
    }
  }, [user, phaseId]);

  useEffect(() => {
    loadChecklistProgress();
  }, [loadChecklistProgress]);

  if (!phase) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-gray-500">Phase not found</p>
      </div>
    );
  }

  const handleCheckItem = async (itemId: string) => {
    const item = checklist.find(c => c.id === itemId);
    if (!item) return;
    const newCompleted = !item.completed;
    setChecklist(prev =>
      prev.map(i => i.id === itemId ? { ...i, completed: newCompleted } : i)
    );
    if (user && phaseId) {
      try {
        await apiUpdateChecklist(user.userId, TRIP_ID, phaseId, itemId, newCompleted);
      } catch {
        // revert on error
        setChecklist(prev =>
          prev.map(i => i.id === itemId ? { ...i, completed: !newCompleted } : i)
        );
      }
    }
  };

  const handleToggleCompleted = async () => {
    const newVal = !isCompleted;
    setIsCompleted(newVal);
    if (user && phaseId) {
      try {
        await updatePhaseCompletion(user.userId, TRIP_ID, phaseId, newVal);
      } catch {
        setIsCompleted(!newVal);
      }
    }
  };

  const completedCount = checklist.filter(c => c.completed).length;
  const checklistProgress = checklist.length > 0
    ? Math.round((completedCount / checklist.length) * 100)
    : 0;

  return (
    <div className="min-h-screen bg-gray-50 pb-8">
      {/* Header */}
      <div className="bg-gradient-to-br from-blue-600 via-blue-500 to-indigo-600 text-white">
        <div className="flex items-center gap-3 px-4 pt-12 pb-4">
          <button
            onClick={() => navigate(-1)}
            className="p-2 -ml-2 rounded-full hover:bg-white/10 transition-colors"
          >
            <ArrowLeft size={22} />
          </button>
          <div className="flex-1">
            <h1 className="text-xl font-bold font-[Fredoka]">{phase.title}</h1>
            {phase.subtitle && (
              <p className="text-blue-100 text-sm">{phase.subtitle}</p>
            )}
          </div>
        </div>

        {/* Travelers here */}
        {travelers.length > 0 && (
          <div className="px-4 pb-4 flex items-center gap-2">
            <div className="flex -space-x-2">
              {travelers.slice(0, 5).map(t => (
                <img
                  key={t.id}
                  src={t.avatar}
                  alt={t.name}
                  className="w-7 h-7 rounded-full border-2 border-blue-500 object-cover"
                />
              ))}
            </div>
            <span className="text-xs text-blue-200">
              {travelers.length} traveler{travelers.length !== 1 ? 's' : ''} on this phase
            </span>
          </div>
        )}

        {/* Status button */}
        <div className="px-4 pb-5">
          <button
            onClick={handleToggleCompleted}
            className={`w-full py-3 rounded-xl font-semibold text-sm flex items-center justify-center gap-2 transition-all ${
              isCompleted
                ? 'bg-emerald-500 text-white shadow-lg shadow-emerald-500/30'
                : 'bg-white/15 text-white border border-white/30 hover:bg-white/25'
            }`}
          >
            {isCompleted ? (
              <>
                <CheckCircle2 size={18} />
                Completed!
              </>
            ) : (
              <>
                <Circle size={18} />
                Mark as Completed
              </>
            )}
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="px-4 -mt-3 space-y-4">
        {/* Checklist Card */}
        {checklist.length > 0 && (
          <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
            <div className="p-4 border-b border-gray-50">
              <div className="flex items-center justify-between mb-2">
                <h3 className="font-semibold text-gray-800 font-[Fredoka]">Checklist</h3>
                <span className="text-xs font-bold text-blue-600">{completedCount}/{checklist.length}</span>
              </div>
              <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-blue-400 to-blue-600 rounded-full transition-all duration-500"
                  style={{ width: `${checklistProgress}%` }}
                />
              </div>
            </div>
            <div className="p-4 space-y-2">
              {checklist.map(item => (
                <button
                  key={item.id}
                  onClick={() => handleCheckItem(item.id)}
                  className="flex items-start gap-3 w-full text-left p-2 rounded-xl hover:bg-gray-50 transition-colors"
                >
                  <div className={`mt-0.5 flex-shrink-0 w-5 h-5 rounded-md border-2 flex items-center justify-center transition-all ${
                    item.completed
                      ? 'bg-emerald-500 border-emerald-500'
                      : 'border-gray-300'
                  }`}>
                    {item.completed && <span className="text-white text-xs font-bold">✓</span>}
                  </div>
                  <span className={`text-sm ${item.completed ? 'text-gray-400 line-through' : 'text-gray-700'}`}>
                    {item.text}
                  </span>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Detailed Instructions */}
        {phase.detailedDescription && (
          <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
            <button
              onClick={() => setShowDetails(!showDetails)}
              className="w-full flex items-center justify-between p-4"
            >
              <h3 className="font-semibold text-gray-800 font-[Fredoka]">Instructions</h3>
              {showDetails ? <ChevronUp size={18} className="text-gray-400" /> : <ChevronDown size={18} className="text-gray-400" />}
            </button>
            {showDetails && (
              <div className="px-4 pb-4">
                <p className="text-sm text-gray-600 leading-relaxed whitespace-pre-line">
                  {phase.detailedDescription}
                </p>
              </div>
            )}
          </div>
        )}

        {/* Links */}
        {phase.links && phase.links.length > 0 && (
          <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-4">
            <h3 className="font-semibold text-gray-800 font-[Fredoka] mb-3">Useful Links</h3>
            <div className="space-y-2">
              {phase.links.map((link, i) => (
                <a
                  key={i}
                  href={link.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-3 p-3 rounded-xl bg-blue-50 hover:bg-blue-100 transition-colors"
                >
                  <ExternalLink size={16} className="text-blue-500 flex-shrink-0" />
                  <span className="text-sm text-blue-700 font-medium">{link.label}</span>
                </a>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
