import { Map, QrCode, User } from 'lucide-react';
import { useLocation, useNavigate } from 'react-router-dom';

const navItems = [
  { path: '/', icon: Map, label: 'Map' },
  { path: '/qr-code', icon: QrCode, label: 'QR Code' },
  { path: '/profile', icon: User, label: 'My Profile' },
];

export default function BottomNav() {
  const location = useLocation();
  const navigate = useNavigate();

  if (location.pathname === '/login') return null;

  return (
    <nav className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 z-50 pb-safe">
      <div className="flex items-center justify-around h-16 max-w-lg mx-auto">
        {navItems.map(({ path, icon: Icon, label }) => {
          const isActive = location.pathname === path;

          return (
            <button
              key={path}
              onClick={() => navigate(path)}
              className={`flex flex-col items-center justify-center w-full h-full transition-colors ${
                isActive ? 'text-emerald-700' : 'text-gray-400 hover:text-gray-600'
              }`}
            >
              <Icon
                size={22}
                strokeWidth={isActive ? 2.5 : 2}
                className={isActive ? 'text-emerald-700' : ''}
              />
              <span className={`text-xs mt-1 ${isActive ? 'font-semibold' : 'font-medium'}`}>
                {label}
              </span>
              {isActive && (
                <div className="absolute bottom-0 w-12 h-0.5 bg-emerald-700 rounded-t-full" />
              )}
            </button>
          );
        })}
      </div>
    </nav>
  );
}
