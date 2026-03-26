import { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  getPhaseById,
  getTravelersAtPhase,
} from '../features/trip/data/tripData';
import {
  ArrowLeft,
  CheckCircle2,
  Circle,
  ExternalLink,
  FileDown,
  Send,
  MessageSquare,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';
import { useAuth } from '../services/AuthContext';
import {
  updateChecklistItem as apiUpdateChecklist,
  getChecklistProgress,
  updatePhaseCompletion,
  addComment as apiAddComment,
  getComments,
} from '../services/api';

const TRIP_ID = 'ross26';

interface BackendComment {
  id: number;
  user_id: number;
  user_name: string;
  text: string;
  created_at: string;
  is_private: boolean;
}

export default function PhaseDetails() {
  const { phaseId } = useParams<{ phaseId: string }>();
  const navigate = useNavigate();
  const { user } = useAuth();
  const phase = phaseId ? getPhaseById(phaseId) : undefined;
  const [isCompleted, setIsCompleted] = useState(phase?.completed || false);
  const [checklist, setChecklist] = useState(phase?.checklist || []);
  const [comment, setComment] = useState('');
  const [backendComments, setBackendComments] = useState<BackendComment[]>([]);
  const [showDetails, setShowDetails] = useState(true);
  const travelers = phaseId ? getTravelersAtPhase(phaseId) : [];

  const loadComments = useCallback(async () => {
    if (!phaseId) return;
    try {
      const data = await getComments(TRIP_ID, phaseId);
      setBackendComments(data.comments);
    } catch {
      // silently fail
    }
  }, [phaseId]);

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
    loadComments();
    loadChecklistProgress();
  }, [loadComments, loadChecklistProgress]);

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

  const handleAddComment = async () => {
    if (!comment.trim() || !user || !phaseId) return;
    try {
      await apiAddComment(user.userId, TRIP_ID, phaseId, comment.trim());
      setComment('');
      await loadComments();
    } catch {
      // silently fail
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

        {/* Attachments */}
        {phase.attachments && phase.attachments.length > 0 && (
          <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-4">
            <h3 className="font-semibold text-gray-800 font-[Fredoka] mb-3">Documents</h3>
            <div className="space-y-2">
              {phase.attachments.map((att, i) => (
                <button
                  key={i}
                  className="flex items-center gap-3 p-3 rounded-xl bg-gray-50 hover:bg-gray-100 transition-colors w-full text-left"
                >
                  <div className="w-10 h-10 bg-red-50 rounded-xl flex items-center justify-center flex-shrink-0">
                    <FileDown size={18} className="text-red-500" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-700 truncate">{att.name}</p>
                    <p className="text-xs text-gray-400 uppercase">{att.type}</p>
                  </div>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Comments Section */}
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
          <div className="p-4 border-b border-gray-50">
            <h3 className="font-semibold text-gray-800 font-[Fredoka]">Comments</h3>
          </div>

          {/* Comment feed */}
          <div className="p-4 space-y-4">
            {backendComments.length === 0 ? (
              <p className="text-sm text-gray-400 text-center py-4">
                No comments yet. Be the first to share!
              </p>
            ) : (
              backendComments.map(c => (
                <div key={c.id} className="flex gap-3">
                  <div className="flex-shrink-0">
                    <div className="w-9 h-9 rounded-full bg-blue-100 flex items-center justify-center">
                      <span className="text-sm font-bold text-blue-600">{c.user_name.charAt(0)}</span>
                    </div>
                  </div>
                  <div className="flex-1 min-w-0">
                    <span className="text-sm font-semibold text-gray-800">
                      {c.user_name}
                    </span>
                    <p className="text-sm text-gray-600 mt-0.5">{c.text}</p>
                    <span className="text-xs text-gray-400 mt-1 block">{new Date(c.created_at).toLocaleString()}</span>
                  </div>
                </div>
              ))
            )}
          </div>

          {/* Add comment */}
          <div className="p-4 border-t border-gray-50">
            <div className="flex items-center gap-2">
              <input
                type="text"
                value={comment}
                onChange={e => setComment(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && handleAddComment()}
                placeholder="Add public comment..."
                className="flex-1 py-2.5 px-4 bg-gray-50 rounded-full text-sm outline-none focus:ring-2 focus:ring-blue-300 transition-all"
              />
              <button
                onClick={handleAddComment}
                disabled={!comment.trim()}
                className="p-2.5 bg-blue-500 text-white rounded-full hover:bg-blue-600 disabled:opacity-40 disabled:hover:bg-blue-500 transition-all"
              >
                <Send size={16} />
              </button>
            </div>
            <button className="flex items-center gap-2 mt-3 text-xs text-gray-400 hover:text-gray-600 transition-colors">
              <MessageSquare size={14} />
              <span>Send Private Feedback to Team</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
