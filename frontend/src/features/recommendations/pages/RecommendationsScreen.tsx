import {
  ArrowLeft,
  Coffee,
  ExternalLink,
  Loader2,
  MapPin,
  ShoppingBag,
  Sparkles,
  Star,
  Utensils,
  Waves,
  Wine,
} from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';
import type { ReactNode } from 'react';
import posthog from 'posthog-js';
import { useNavigate } from 'react-router-dom';

import AppHeader from '../../../shared/components/AppHeader';
import { getMyRecommendations, type Recommendation } from '../../trip/services/trip-api';

type CategoryKey = 'all' | 'restaurants' | 'bars' | 'cafes' | 'beaches' | 'wellness' | 'shopping';
type LocationKey = 'all' | 'rio' | 'ilha-grande';

const categories: { key: CategoryKey; label: string; icon: ReactNode }[] = [
  { key: 'all', label: 'All', icon: <Star size={14} /> },
  { key: 'restaurants', label: 'Food', icon: <Utensils size={14} /> },
  { key: 'bars', label: 'Bars', icon: <Wine size={14} /> },
  { key: 'cafes', label: 'Cafes', icon: <Coffee size={14} /> },
  { key: 'beaches', label: 'Beaches', icon: <Waves size={14} /> },
  { key: 'wellness', label: 'Wellness', icon: <Sparkles size={14} /> },
  { key: 'shopping', label: 'Shopping', icon: <ShoppingBag size={14} /> },
];

const locations: { key: LocationKey; label: string }[] = [
  { key: 'all', label: 'All Locations' },
  { key: 'rio', label: 'Rio de Janeiro' },
  { key: 'ilha-grande', label: 'Ilha Grande' },
];

function normalize(value: string | null | undefined) {
  return (value || '').trim().toLowerCase();
}

function mapUrlFor(rec: Recommendation) {
  if (rec.map_url) return rec.map_url;
  if (rec.address) return `https://maps.google.com/?q=${encodeURIComponent(rec.address)}`;
  return null;
}

function RecommendationCard({ rec }: { rec: Recommendation }) {
  const mapUrl = mapUrlFor(rec);
  const neighborhood = rec.neighborhood || rec.address;

  return (
    <article className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden hover:shadow-md transition-shadow">
      {rec.photo_url && (
        <img src={rec.photo_url} alt={rec.name} className="w-full h-40 object-cover bg-emerald-50" />
      )}
      <div className="p-4">
        <div className="flex items-start gap-3">
          <div className="w-12 h-12 bg-emerald-50 rounded-xl flex items-center justify-center text-xl shrink-0">
            {rec.emoji || '📍'}
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <h2 className="text-sm font-semibold text-gray-800">{rec.name}</h2>
              {rec.highlight && (
                <span className="text-[10px] bg-emerald-100 text-emerald-700 px-2 py-0.5 rounded-full font-medium">
                  {rec.highlight}
                </span>
              )}
            </div>
            <div className="flex items-center gap-2 mt-1 flex-wrap">
              {neighborhood && (
                <span className="text-xs text-gray-400 flex items-center gap-1">
                  <MapPin size={10} />
                  {neighborhood}
                </span>
              )}
              {rec.price_range && <span className="text-xs text-gray-400">{rec.price_range}</span>}
              {rec.rating !== null && (
                <span className="text-xs text-emerald-600 flex items-center gap-0.5">
                  <Star size={10} fill="currentColor" />
                  {rec.rating.toFixed(1)}
                </span>
              )}
            </div>
            {rec.description && (
              <p className="text-xs text-gray-600 mt-2 leading-relaxed">{rec.description}</p>
            )}
            {mapUrl && (
              <a
                href={mapUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1 text-xs text-emerald-600 hover:text-emerald-700 font-medium mt-3"
                onClick={() => posthog.capture('recommendation_opened', { recommendation_id: rec.id, name: rec.name })}
              >
                <ExternalLink size={12} />
                Open in Maps
              </a>
            )}
          </div>
        </div>
      </div>
    </article>
  );
}

export default function RecommendationsScreen() {
  const navigate = useNavigate();
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [activeCategory, setActiveCategory] = useState<CategoryKey>('all');
  const [activeLocation, setActiveLocation] = useState<LocationKey>('all');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getMyRecommendations()
      .then(data => setRecommendations(data.recommendations))
      .catch(() => setRecommendations([]))
      .finally(() => setLoading(false));
  }, []);

  const filtered = useMemo(() => recommendations.filter(rec => {
    if (activeCategory !== 'all' && normalize(rec.category) !== activeCategory) return false;
    if (activeLocation !== 'all' && normalize(rec.location) !== activeLocation) return false;
    return true;
  }), [activeCategory, activeLocation, recommendations]);

  return (
    <div className="min-h-screen bg-gradient-to-b from-emerald-50 via-white to-gray-50" style={{ paddingBottom: 'calc(100px + env(safe-area-inset-bottom))' }}>
      <AppHeader title="Recommendations" />
      <div className="pt-14">
        <section className="bg-gradient-to-br from-emerald-700 via-emerald-600 to-teal-600 px-5 py-6 text-white">
          <div className="flex items-center gap-3">
            <button
              type="button"
              aria-label="Back"
              onClick={() => navigate(-1)}
              className="w-10 h-10 bg-white/15 hover:bg-white/25 rounded-full flex items-center justify-center shrink-0 transition-colors"
            >
              <ArrowLeft size={20} />
            </button>
            <div className="w-12 h-12 bg-white/20 rounded-2xl flex items-center justify-center text-2xl">
              📍
            </div>
            <div>
              <h1 className="text-xl font-bold font-[Fredoka]">Local Recommendations</h1>
              <p className="text-emerald-100 text-sm">Curated spots by the Parrot Trips team</p>
            </div>
          </div>
        </section>

        <div className="px-4 pt-4 flex gap-2 overflow-x-auto">
          {locations.map(loc => (
            <button
              key={loc.key}
              onClick={() => setActiveLocation(loc.key)}
              className={`px-3 py-1.5 rounded-full text-xs font-medium whitespace-nowrap transition-all ${
                activeLocation === loc.key
                  ? 'bg-emerald-700 text-white shadow-sm'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              {loc.label}
            </button>
          ))}
        </div>

        <div className="px-4 pt-3 pb-2 overflow-x-auto">
          <div className="flex gap-2">
            {categories.map(cat => (
              <button
                key={cat.key}
                onClick={() => setActiveCategory(cat.key)}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium whitespace-nowrap transition-all ${
                  activeCategory === cat.key
                    ? 'bg-emerald-700 text-white shadow-sm'
                    : 'bg-white border border-gray-200 text-gray-600 hover:bg-gray-50'
                }`}
              >
                {cat.icon}
                {cat.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {loading ? (
        <div className="flex justify-center py-16">
          <Loader2 className="animate-spin text-emerald-600" size={28} />
        </div>
      ) : (
        <>
          <div className="px-5 py-2">
            <p className="text-xs text-gray-400">
              {filtered.length} recommendation{filtered.length !== 1 ? 's' : ''}
            </p>
          </div>
          <div className="px-4 space-y-3 pb-4">
            {filtered.length === 0 ? (
              <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6 text-center">
                <p className="text-sm text-gray-400">No recommendations for this filter yet</p>
              </div>
            ) : (
              filtered.map(rec => <RecommendationCard key={rec.id} rec={rec} />)
            )}
          </div>
        </>
      )}
    </div>
  );
}
