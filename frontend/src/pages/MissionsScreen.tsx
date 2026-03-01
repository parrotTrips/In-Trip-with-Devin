import TopBar from '../components/TopBar';
import { Sparkles, Lock, Trophy, Star } from 'lucide-react';

const missions = [
  {
    id: 1,
    title: 'First Photo!',
    description: 'Upload your first photo to the group album',
    points: 50,
    unlocked: true,
    completed: false,
    icon: '📸',
  },
  {
    id: 2,
    title: 'Social Butterfly',
    description: 'Comment on 3 different activities',
    points: 100,
    unlocked: true,
    completed: true,
    icon: '🦋',
  },
  {
    id: 3,
    title: 'Early Bird',
    description: 'Complete all pre-trip phases before the parrot!',
    points: 200,
    unlocked: true,
    completed: false,
    icon: '🐦',
  },
  {
    id: 4,
    title: 'Adventure Seeker',
    description: 'Book at least 2 optional activities',
    points: 150,
    unlocked: false,
    completed: false,
    icon: '🏄',
  },
  {
    id: 5,
    title: 'Memory Maker',
    description: 'Share 10 photos across the trip',
    points: 300,
    unlocked: false,
    completed: false,
    icon: '🌟',
  },
  {
    id: 6,
    title: 'Group Leader',
    description: 'Help 3 travelers with their preparation',
    points: 250,
    unlocked: false,
    completed: false,
    icon: '👑',
  },
];

export default function MissionsScreen() {
  const totalPoints = missions.filter(m => m.completed).reduce((sum, m) => sum + m.points, 0);
  const maxPoints = missions.reduce((sum, m) => sum + m.points, 0);

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
              <p className="text-purple-200 text-sm">Complete challenges to earn points!</p>
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
                style={{ width: `${(totalPoints / maxPoints) * 100}%` }}
              />
            </div>
          </div>
        </div>
      </div>

      {/* Missions list */}
      <div className="px-4 py-5 space-y-3">
        {missions.map(mission => (
          <div
            key={mission.id}
            className={`bg-white rounded-2xl border shadow-sm p-4 transition-all ${
              mission.completed
                ? 'border-emerald-200 bg-emerald-50/50'
                : mission.unlocked
                  ? 'border-gray-100 hover:shadow-md'
                  : 'border-gray-100 opacity-60'
            }`}
          >
            <div className="flex items-start gap-3">
              <div className={`w-12 h-12 rounded-2xl flex items-center justify-center text-xl ${
                mission.completed
                  ? 'bg-emerald-100'
                  : mission.unlocked
                    ? 'bg-purple-50'
                    : 'bg-gray-100'
              }`}>
                {mission.unlocked ? mission.icon : <Lock size={20} className="text-gray-400" />}
              </div>
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <h3 className={`font-semibold text-sm font-[Fredoka] ${
                    mission.completed ? 'text-emerald-700' : 'text-gray-800'
                  }`}>
                    {mission.title}
                  </h3>
                  {mission.completed && (
                    <span className="text-xs bg-emerald-100 text-emerald-600 px-2 py-0.5 rounded-full font-medium">
                      Done!
                    </span>
                  )}
                </div>
                <p className="text-xs text-gray-500 mt-0.5">
                  {mission.unlocked ? mission.description : 'Complete previous missions to unlock'}
                </p>
              </div>
              <div className="flex items-center gap-1 text-amber-500">
                <Star size={14} fill="currentColor" />
                <span className="text-sm font-bold">{mission.points}</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
