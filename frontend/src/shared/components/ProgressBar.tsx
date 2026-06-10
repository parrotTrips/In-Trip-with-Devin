interface Props {
  totalPhases: number;
  completedCount: number;
}

export default function ProgressBar({ totalPhases, completedCount }: Props) {
  if (totalPhases === 0) return null;

  const progress = Math.round((completedCount / totalPhases) * 100);

  return (
    <div className="px-4 py-3">
      <div className="flex items-center justify-between mb-1.5">
        <span className="text-xs font-semibold text-emerald-200 uppercase tracking-wide">
          Trip Progress
        </span>
        <span className="text-xs font-bold text-white">
          {progress}%
        </span>
      </div>
      <div className="relative h-3 bg-emerald-800/50 rounded-full overflow-hidden">
        <div
          className="h-full rounded-full bg-gradient-to-r from-emerald-300 to-white transition-all duration-1000 ease-out"
          style={{ width: `${progress}%` }}
        />
      </div>
    </div>
  );
}
