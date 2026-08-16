import { Bell } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useNotifications } from '../../app/providers/notification-context';

interface TopBarProps {
  title?: string;
}

export default function TopBar({ title }: TopBarProps) {
  const navigate = useNavigate();
  const { unreadCount } = useNotifications();

  return (
    <header className="fixed top-0 left-0 right-0 z-[60] bg-white/90 backdrop-blur-md border-b border-gray-100">
      <div className="flex items-center justify-between h-14 px-4 max-w-lg mx-auto">
        <div className="w-10" aria-hidden="true" />

        <div className="flex items-center gap-2">
          <span className="text-lg">🦜</span>
          <h1 className="text-base font-semibold text-gray-800 font-[Fredoka]">
            {title || 'Parrot Trips'}
          </h1>
        </div>

        <button
          onClick={() => navigate('/notifications')}
          className="relative w-10 h-10 flex items-center justify-center rounded-full hover:bg-gray-100 transition-colors"
          aria-label="Notifications"
        >
          <Bell size={20} className="text-gray-500" />
          {unreadCount > 0 && (
            <span
              aria-label="Unread notifications"
              className="absolute top-2 right-2 w-2.5 h-2.5 rounded-full bg-emerald-500 ring-2 ring-white"
            />
          )}
        </button>
      </div>
    </header>
  );
}
