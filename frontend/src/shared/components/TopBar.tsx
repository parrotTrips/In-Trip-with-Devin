interface TopBarProps {
  title?: string;
}

export default function TopBar({ title }: TopBarProps) {
  return (
    <header className="fixed top-0 left-0 right-0 z-50 bg-white/90 backdrop-blur-md border-b border-gray-100">
      <div className="flex items-center justify-between h-14 px-4 max-w-lg mx-auto">
        <div className="w-10" aria-hidden="true" />

        <div className="flex items-center gap-2">
          <span className="text-lg">🦜</span>
          <h1 className="text-base font-semibold text-gray-800 font-[Fredoka]">
            {title || 'Parrot Trips'}
          </h1>
        </div>

        <div className="w-10" aria-hidden="true" />
      </div>
    </header>
  );
}
