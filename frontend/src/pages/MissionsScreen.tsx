import TopBar from '../shared/components/TopBar';
import { Sparkles, Trophy, Star, Loader2, CheckCircle2, Circle, Crown, Medal } from 'lucide-react';
import { completeMission, getLeaderboard, getMissions, uncompleteMission, type LeaderboardEntry, type Mission } from '../features/missions/services/missions-api';
import { useAuth } from '../services/AuthContext';
import { useState, useEffect } from 'react';

const TRIP_ID = 'ross26';

const categoryColors: Record<string, string> = {
  social: 'bg-blue-50 text-blue-600',
  preparation: 'bg-amber-50 text-amber-600',
  adventure: 'bg-emerald-50 text-emerald-600',
  culture: 'bg-purple-50 text-purple-600',
  general: 'bg-gray-50 text-gray-600',
};

export default function MissionsScreen() {
  const { user } = useAuth();
  const [missions, setMissions] = useState<Mission[]>([]);
  const [leaderboard, setLeaderboard] = useState<LeaderboardEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'missions' | 'leaderboard'>('missions');
  const [filter, setFilter] = useState<string>('all');
  const [togglingId, setTogglingId] = useState<number | null>(null);

  const loadData = async () => {
    if (!user) return;
    try {
      const [missionsRes, lbRes] = await Promise.all([
        getMissions(TRIP_ID, user.userId),
        getLeaderboard(TRIP_ID),
      ]);
      setMissions(missionsRes.missions);
      setLeaderboard(lbRes.leaderboard);
    } catch (err) {
      console.error('Failed to load missions:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadData(); }, [user]);

  const toggleMission = async (mission: Mission) => {
    if (!user || togglingId !== null) return;
    setTogglingId(mission.id);
    try {
      if (mission.completed) {
        await uncompleteMission(TRIP_ID, user.userId, mission.id);
      } else {
        await completeMission(TRIP_ID, user.userId, mission.id);
      }
      await loadData();
    } catch (err) {
      console.error('Failed to toggle mission:', err);
    } finally {
      setTogglingId(null);
    }
  };

  const totalPoints = missions.filter(m => m.completed).reduce((sum, m) => sum + m.points, 0);
  const maxPoints = missions.reduce((sum, m) => sum + m.points, 0);
  const completedCount = missions.filter(m => m.completed).length;

  const categories = ['all', ...Array.from(new Set(missions.map(m => m.category)))];
  const filteredMissions = filter === 'all' ? missions : missions.filter(m => m.category === filter);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <Loader2 className="animate-spin text-purple-600" size={32} />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-purple-50 via-white to-amber-50 pb-20">
      <TopBar title="Secret Missions" />

      <div className="pt-14">
        {/* Header */}
        <div className="bg-gradient-to-br from-purple-600 via-purple-500 to-indigo-600 px-5 py-6 text-white">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-12 h-12 bg-white/20 rounded-2xl flex items-center justify-center">
              <Sparkles size={24} />
            </div>
            <div>
              <h2 className="text-xl font-bold font-[Fredoka]">Secret Missions</h2>
              <p className="text-purple-200 text-sm">{completedCount}/{missions.length} completed</p>
            </div>
          </div>

          {/* Points summary */}
          <div className="bg-white/10 rounded-2xl p-4">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <Trophy size={16} className="text-yellow-300" />
                <span className="text-sm font-semibold">Your Points</span>
              </div>
              <span className="text-lg font-bold text-yellow-300">{totalPoints}/{maxPoints}</span>
            </div>
            <div className="h-2 bg-white/20 rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-yellow-400 to-amber-500 rounded-full transition-all"
                style={{ width: maxPoints > 0 ? `${(totalPoints / maxPoints) * 100}%` : '0%' }}
              />
            </div>
          </div>

          {/* Tabs */}
          <div className="flex gap-2 mt-4">
            <button
              onClick={() => setActiveTab('missions')}
              className={`flex-1 py-2 rounded-xl text-sm font-semibold transition-all ${
                activeTab === 'missions' ? 'bg-white/20 text-white' : 'text-white/60'
              }`}
            >
              Missions
            </button>
            <button
              onClick={() => setActiveTab('leaderboard')}
              className={`flex-1 py-2 rounded-xl text-sm font-semibold transition-all ${
                activeTab === 'leaderboard' ? 'bg-white/20 text-white' : 'text-white/60'
              }`}
            >
              Leaderboard
            </button>
          </div>
        </div>
      </div>

      {activeTab === 'missions' ? (
        <>
          {/* Category filters */}
          <div className="px-4 pt-4 flex gap-2 overflow-x-auto scrollbar-hide">
            {categories.map(cat => (
              <button
                key={cat}
                onClick={() => setFilter(cat)}
                className={`px-3 py-1.5 rounded-full text-xs font-semibold whitespace-nowrap transition-all ${
                  filter === cat
                    ? 'bg-purple-600 text-white'
                    : 'bg-white text-gray-600 border border-gray-200'
                }`}
              >
                {cat === 'all' ? 'All' : cat.charAt(0).toUpperCase() + cat.slice(1)}
              </button>
            ))}
          </div>

          {/* Missions list */}
          <div className="px-4 py-4 space-y-3">
            {filteredMissions.map(mission => (
              <button
                key={mission.id}
                onClick={() => toggleMission(mission)}
                disabled={togglingId !== null}
                className={`w-full text-left bg-white rounded-2xl border shadow-sm p-4 transition-all ${
                  mission.completed
                    ? 'border-emerald-200 bg-emerald-50/50'
                    : 'border-gray-100 hover:shadow-md'
                }`}
              >
                <div className="flex items-start gap-3">
                  <div className={`w-12 h-12 rounded-2xl flex items-center justify-center text-xl ${
                    mission.completed ? 'bg-emerald-100' : 'bg-purple-50'
                  }`}>
                    {mission.icon}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <h3 className={`font-semibold text-sm font-[Fredoka] ${
                        mission.completed ? 'text-emerald-700' : 'text-gray-800'
                      }`}>
                        {mission.title}
                      </h3>
                      <span className={`text-[10px] px-1.5 py-0.5 rounded-full font-medium ${categoryColors[mission.category] || categoryColors.general}`}>
                        {mission.category}
                      </span>
                    </div>
                    <p className="text-xs text-gray-500 mt-0.5">{mission.description}</p>
                    <div className="flex items-center gap-1 mt-1.5 text-amber-500">
                      <Star size={12} fill="currentColor" />
                      <span className="text-xs font-bold">{mission.points} pts</span>
                    </div>
                  </div>
                  <div className="flex-shrink-0 pt-1">
                    {togglingId === mission.id ? (
                      <Loader2 size={22} className="animate-spin text-purple-400" />
                    ) : mission.completed ? (
                      <CheckCircle2 size={22} className="text-emerald-500" />
                    ) : (
                      <Circle size={22} className="text-gray-300" />
                    )}
                  </div>
                </div>
              </button>
            ))}
          </div>
        </>
      ) : (
        /* Leaderboard */
        <div className="px-4 py-5 space-y-3">
          {leaderboard.map((entry, index) => (
            <div
              key={entry.user_id}
              className={`bg-white rounded-2xl border shadow-sm p-4 flex items-center gap-3 ${
                index === 0 ? 'border-yellow-200 bg-yellow-50/30' :
                index === 1 ? 'border-gray-200 bg-gray-50/30' :
                index === 2 ? 'border-amber-200 bg-amber-50/30' : 'border-gray-100'
              }`}
            >
              <div className={`w-10 h-10 rounded-full flex items-center justify-center font-bold text-sm ${
                index === 0 ? 'bg-yellow-100 text-yellow-700' :
                index === 1 ? 'bg-gray-100 text-gray-700' :
                index === 2 ? 'bg-amber-100 text-amber-700' : 'bg-gray-50 text-gray-500'
              }`}>
                {index === 0 ? <Crown size={20} className="text-yellow-500" /> :
                 index === 1 ? <Medal size={20} className="text-gray-400" /> :
                 index === 2 ? <Medal size={20} className="text-amber-500" /> :
                 `#${index + 1}`}
              </div>
              <div className="flex-1 min-w-0">
                <p className={`font-semibold text-sm font-[Fredoka] ${
                  entry.user_id === user?.userId ? 'text-purple-700' : 'text-gray-800'
                }`}>
                  {entry.name} {entry.user_id === user?.userId && '(You)'}
                </p>
                <p className="text-xs text-gray-500">{entry.missions_completed} missions completed</p>
              </div>
              <div className="flex items-center gap-1 text-amber-500">
                <Star size={14} fill="currentColor" />
                <span className="text-sm font-bold">{entry.total_points}</span>
              </div>
            </div>
          ))}
          {leaderboard.length === 0 && (
            <div className="text-center py-12">
              <Trophy className="mx-auto text-gray-300 mb-3" size={40} />
              <p className="text-sm text-gray-500">No points earned yet. Complete missions to climb the leaderboard!</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
