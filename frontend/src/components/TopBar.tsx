import { Menu, Bell } from 'lucide-react';
import { useState } from 'react';

interface TopBarProps {
  title?: string;
  showBack?: boolean;
  onBack?: () => void;
}

export default function TopBar({ title }: TopBarProps) {
  const [menuOpen, setMenuOpen] = useState(false);

  return (
    <>
      <header className="fixed top-0 left-0 right-0 z-50 bg-white/90 backdrop-blur-md border-b border-gray-100">
        <div className="flex items-center justify-between h-14 px-4 max-w-lg mx-auto">
          <button
            onClick={() => setMenuOpen(true)}
            className="p-2 -ml-2 rounded-full hover:bg-gray-100 transition-colors"
          >
            <Menu size={22} className="text-gray-700" />
          </button>

          <div className="flex items-center gap-2">
            <span className="text-lg">🦜</span>
            <h1 className="text-base font-semibold text-gray-800 font-[Fredoka]">
              {title || 'Parrot Trips'}
            </h1>
          </div>

          <button className="p-2 -mr-2 rounded-full hover:bg-gray-100 transition-colors relative">
            <Bell size={20} className="text-gray-700" />
            <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full" />
          </button>
        </div>
      </header>

      {/* Hamburger Menu Overlay */}
      {menuOpen && (
        <div className="fixed inset-0 z-[100]" onClick={() => setMenuOpen(false)}>
          <div className="absolute inset-0 bg-black/40" />
          <div
            className="absolute left-0 top-0 bottom-0 w-72 bg-white shadow-2xl"
            onClick={e => e.stopPropagation()}
          >
            <div className="bg-gradient-to-br from-emerald-700 to-emerald-600 p-6 pt-10">
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 rounded-full bg-white/20 flex items-center justify-center">
                  <span className="text-2xl">🦜</span>
                </div>
                <div>
                  <h2 className="text-white font-semibold text-lg font-[Fredoka]">Parrot Trips</h2>
                  <p className="text-emerald-100 text-sm">MIT Brazil Trek 2026</p>
                </div>
              </div>
            </div>
            <nav className="p-4 space-y-1">
              {[
                { label: 'My Profile', emoji: '👤' },
                { label: 'Trip Details', emoji: '✈️' },
                { label: 'Emergency Contacts', emoji: '🆘' },
                { label: 'Travel Insurance', emoji: '🛡️' },
                { label: 'Group Chat', emoji: '💬' },
                { label: 'Settings', emoji: '⚙️' },
              ].map(item => (
                <button
                  key={item.label}
                  className="flex items-center gap-3 w-full px-3 py-3 rounded-xl hover:bg-gray-50 transition-colors text-gray-700"
                >
                  <span className="text-lg">{item.emoji}</span>
                  <span className="font-medium text-sm">{item.label}</span>
                </button>
              ))}
            </nav>
            <div className="absolute bottom-8 left-0 right-0 px-6">
              <button className="w-full py-3 text-sm text-gray-400 hover:text-red-500 transition-colors">
                Sign Out
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
