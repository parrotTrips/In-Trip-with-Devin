import { useState, useRef, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  getPhaseById,
  isTripDay,
  type Activity,
} from '../data/tripData';
import {
  ArrowLeft,
  Clock,
  MapPin,
  Star,
  ChevronRight,
  Send,
  Camera,
  Check,
  DollarSign,
  ImagePlus,
} from 'lucide-react';
import { useAuth } from '../services/AuthContext';
import { addComment as apiAddComment, getComments } from '../services/api';

const TRIP_ID = 'ross26';

interface BackendComment {
  id: number;
  user_id: number;
  user_name: string;
  text: string;
  created_at: string;
  is_private: boolean;
}

function ActivityCard({ activity, index }: { activity: Activity; index: number }) {
  const [expanded, setExpanded] = useState(false);
  const [currentImage, setCurrentImage] = useState(0);

  const typeConfig: Record<string, { label: string; color: string; icon: React.ReactNode }> = {
    included: { label: 'Included', color: 'bg-emerald-100 text-emerald-700', icon: <Check size={12} /> },
    optional: { label: 'Optional', color: 'bg-amber-100 text-amber-700', icon: <Star size={12} /> },
    suggested: { label: 'Suggested', color: 'bg-blue-100 text-blue-700', icon: <Star size={12} /> },
    logistics: { label: 'Logistics', color: 'bg-gray-100 text-gray-700', icon: <MapPin size={12} /> },
  };

  const config = typeConfig[activity.type] || typeConfig.included;

  return (
    <div className="relative">
      {/* Timeline connector */}
      <div className="absolute left-6 top-0 bottom-0 w-0.5 bg-gray-200" />

      <div className="relative flex gap-3">
        {/* Timeline dot */}
        <div className="flex-shrink-0 w-12 flex flex-col items-center">
          <div className={`relative z-10 w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold text-white ${
            activity.type === 'included' ? 'bg-emerald-500' : activity.type === 'optional' ? 'bg-amber-500' : activity.type === 'logistics' ? 'bg-gray-500' : 'bg-blue-500'
          }`}>
            {index + 1}
          </div>
        </div>

        {/* Activity content */}
        <div className="flex-1 pb-6">
          <button
            onClick={() => setExpanded(!expanded)}
            className="w-full text-left bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden hover:shadow-md transition-shadow"
          >
            {/* Activity images carousel */}
            {activity.images.length > 0 && (
              <div className="relative h-40 overflow-hidden">
                <img
                  src={activity.images[currentImage]}
                  alt={activity.name}
                  className="w-full h-full object-cover"
                  onError={(e) => {
                    (e.target as HTMLImageElement).src = 'https://placehold.co/600x400/e2e8f0/94a3b8?text=Photo';
                  }}
                />
                {activity.images.length > 1 && (
                  <div className="absolute bottom-2 left-1/2 -translate-x-1/2 flex gap-1">
                    {activity.images.map((_, i) => (
                      <button
                        key={i}
                        onClick={(e) => { e.stopPropagation(); setCurrentImage(i); }}
                        className={`w-1.5 h-1.5 rounded-full transition-all ${
                          i === currentImage ? 'bg-white w-4' : 'bg-white/60'
                        }`}
                      />
                    ))}
                  </div>
                )}
                {/* Type badge on image */}
                <div className={`absolute top-3 left-3 px-2.5 py-1 rounded-full text-xs font-semibold flex items-center gap-1 ${config.color}`}>
                  {config.icon}
                  {config.label}
                </div>
                {activity.price && (
                  <div className="absolute top-3 right-3 px-2.5 py-1 rounded-full text-xs font-semibold bg-white/90 text-gray-800 flex items-center gap-1">
                    <DollarSign size={12} />
                    {activity.price}
                  </div>
                )}
              </div>
            )}

            <div className="p-4">
              {/* No image - show badge inline */}
              {activity.images.length === 0 && (
                <div className="flex items-center gap-2 mb-2">
                  <span className={`px-2.5 py-1 rounded-full text-xs font-semibold flex items-center gap-1 ${config.color}`}>
                    {config.icon}
                    {config.label}
                  </span>
                  {activity.price && (
                    <span className="text-xs font-semibold text-gray-600 flex items-center gap-1">
                      <DollarSign size={12} />
                      {activity.price}
                    </span>
                  )}
                </div>
              )}

              <h4 className="font-semibold text-gray-800 text-sm font-[Fredoka]">
                {activity.name}
              </h4>

              <div className="flex items-center gap-3 mt-2 text-xs text-gray-500">
                <span className="flex items-center gap-1">
                  <Clock size={12} />
                  {activity.time}
                </span>
                <span className="flex items-center gap-1">
                  ⏱ {activity.duration}
                </span>
              </div>

              <p className="text-sm text-gray-600 mt-2 leading-relaxed">
                {activity.description}
              </p>

              {expanded && (
                <div className="mt-3 pt-3 border-t border-gray-100">
                  <div className="flex items-start gap-2 text-sm text-gray-600">
                    <MapPin size={14} className="text-emerald-500 flex-shrink-0 mt-0.5" />
                    <p>{activity.practicalInfo}</p>
                  </div>
                  {activity.price && activity.type === 'optional' && (
                    <button className="mt-3 w-full py-2.5 bg-amber-500 text-white rounded-xl font-semibold text-sm hover:bg-amber-600 transition-colors">
                      Book Now — {activity.price}
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
  const { user } = useAuth();
  const phase = dayId ? getPhaseById(dayId) : undefined;
  const [comment, setComment] = useState('');
  const [backendComments, setBackendComments] = useState<BackendComment[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const loadComments = useCallback(async () => {
    if (!dayId) return;
    try {
      const data = await getComments(TRIP_ID, dayId);
      setBackendComments(data.comments);
    } catch {
      // silently fail
    }
  }, [dayId]);

  useEffect(() => {
    loadComments();
  }, [loadComments]);

  if (!phase || !isTripDay(phase)) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-gray-500">Day not found</p>
      </div>
    );
  }

  const handleAddComment = async () => {
    if (!comment.trim() || !user || !dayId) return;
    try {
      await apiAddComment(user.userId, TRIP_ID, dayId, comment.trim());
      setComment('');
      await loadComments();
    } catch {
      // silently fail
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 pb-8">
      {/* Header */}
      <div className="bg-gradient-to-br from-emerald-700 via-emerald-600 to-teal-600 text-white">
        <div className="flex items-center gap-3 px-4 pt-12 pb-2">
          <button
            onClick={() => navigate(-1)}
            className="p-2 -ml-2 rounded-full hover:bg-white/10 transition-colors"
          >
            <ArrowLeft size={22} />
          </button>
          <div className="flex-1">
            <h1 className="text-xl font-bold font-[Fredoka]">{phase.title} — {phase.subtitle}</h1>
            <p className="text-emerald-100 text-sm mt-0.5">{phase.description}</p>
          </div>
        </div>

        {/* Day overview */}
        <div className="px-4 pb-5 mt-2">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-1.5 text-emerald-100 text-xs">
              <Clock size={14} />
              <span>{phase.activities.length} activities</span>
            </div>
            <div className="flex items-center gap-1.5 text-emerald-100 text-xs">
              <Camera size={14} />
              <span>{phase.albumPhotos.length} photos</span>
            </div>
          </div>
        </div>
      </div>

      {/* Activities Timeline */}
      <div className="px-4 pt-6">
        <h2 className="text-lg font-bold text-gray-800 font-[Fredoka] mb-4">
          Today's Itinerary
        </h2>
        <div>
          {phase.activities.map((activity, index) => (
            <ActivityCard key={activity.id} activity={activity} index={index} />
          ))}
        </div>
      </div>

      {/* Collaborative Album */}
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
            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              className="hidden"
            />
          </div>

          {phase.albumPhotos.length > 0 ? (
            <div className="p-4">
              <div className="grid grid-cols-2 gap-3">
                {phase.albumPhotos.map(photo => (
                  <div key={photo.id} className="relative rounded-xl overflow-hidden aspect-square">
                    <img
                      src={photo.url}
                      alt={photo.caption}
                      className="w-full h-full object-cover"
                      onError={(e) => {
                        (e.target as HTMLImageElement).src = 'https://placehold.co/400x300/e2e8f0/94a3b8?text=Photo';
                      }}
                    />
                    <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/60 to-transparent p-2">
                      <p className="text-white text-xs font-medium">{photo.userName}</p>
                      <p className="text-white/80 text-xs">{photo.caption}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="p-8 text-center">
              <div className="w-16 h-16 mx-auto bg-gray-100 rounded-2xl flex items-center justify-center mb-3">
                <Camera size={24} className="text-gray-400" />
              </div>
              <p className="text-sm text-gray-400">No photos yet. Be the first to share!</p>
            </div>
          )}
        </div>
      </div>

      {/* Comments Section */}
      <div className="px-4 mt-6">
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
          <div className="p-4 border-b border-gray-50">
            <h3 className="font-semibold text-gray-800 font-[Fredoka]">Share Your Experience</h3>
          </div>

          <div className="p-4 space-y-4">
            {backendComments.length === 0 ? (
              <p className="text-sm text-gray-400 text-center py-4">
                How was your day? Share with the group!
              </p>
            ) : (
              backendComments.map(c => (
                <div key={c.id} className="flex gap-3">
                  <div className="flex-shrink-0">
                    <div className="w-9 h-9 rounded-full bg-emerald-100 flex items-center justify-center">
                      <span className="text-sm font-bold text-emerald-600">{c.user_name.charAt(0)}</span>
                    </div>
                  </div>
                  <div className="flex-1">
                    <span className="text-sm font-semibold text-gray-800">{c.user_name}</span>
                    <p className="text-sm text-gray-600 mt-0.5">{c.text}</p>
                    <span className="text-xs text-gray-400 mt-1 block">{new Date(c.created_at).toLocaleString()}</span>
                  </div>
                </div>
              ))
            )}
          </div>

          <div className="p-4 border-t border-gray-50">
            <div className="flex items-center gap-2">
              <input
                type="text"
                value={comment}
                onChange={e => setComment(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && handleAddComment()}
                placeholder="Share your experience today!"
                className="flex-1 py-2.5 px-4 bg-gray-50 rounded-full text-sm outline-none focus:ring-2 focus:ring-emerald-300 transition-all"
              />
              <button
                onClick={handleAddComment}
                disabled={!comment.trim()}
                className="p-2.5 bg-emerald-500 text-white rounded-full hover:bg-emerald-600 disabled:opacity-40 transition-all"
              >
                <Send size={16} />
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
