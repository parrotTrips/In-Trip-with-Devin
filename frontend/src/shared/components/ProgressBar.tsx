interface Props {
  totalPhases: number;
  completedCount: number;
  parrotCompletedCount: number;
}

export default function ProgressBar({ totalPhases, completedCount, parrotCompletedCount }: Props) {
  if (totalPhases === 0) return null;

  const userProgress = Math.round((completedCount / totalPhases) * 100);
  const parrotProgress = Math.round((parrotCompletedCount / totalPhases) * 100);
  const isBehind = userProgress < parrotProgress;

  return (
    <div className="px-4 py-3">
      <div className="flex items-center justify-between mb-1.5">
        <span className="text-xs font-semibold text-gray-500 uppercase tracking-wide">
          Trip Progress
        </span>
        <span className={`text-xs font-bold ${isBehind ? 'text-amber-600' : 'text-emerald-600'}`}>
          {userProgress}%
        </span>
      </div>
      <div className="relative h-3 bg-gray-100 rounded-full overflow-hidden">
        <div
          className="absolute top-0 bottom-0 w-0.5 bg-emerald-400 z-10"
          style={{ left: `${parrotProgress}%` }}
        >
          <div className="absolute -top-1 -left-1.5 text-xs">🦜</div>
        </div>
        <div
          className={`h-full rounded-full transition-all duration-1000 ease-out ${
            isBehind
              ? 'bg-gradient-to-r from-amber-400 to-amber-500'
              : 'bg-gradient-to-r from-emerald-400 to-emerald-600'
          }`}
          style={{ width: `${userProgress}%` }}
        />
      </div>
      {isBehind && (
        <p className="text-xs text-amber-600 mt-1 flex items-center gap-1">
          <span>⚡</span> You're a bit behind! Catch up with the parrot!
        </p>
      )}
    </div>
  );
}
