import { Bell } from 'lucide-react';
import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { useAuth } from '../../app/providers/auth-context';
import { getUnreadCount } from '../../features/notifications/services/notifications-api';

interface TopBarProps {
  title?: string;
}

export default function TopBar({ title }: TopBarProps) {
  const [unreadCount, setUnreadCount] = useState(0);
  const navigate = useNavigate();
  const { user } = useAuth();

  useEffect(() => {
    if (!user?.userId) return;

    const uid = user.userId;
    const fetchCount = () => {
      getUnreadCount(uid)
        .then((data) => setUnreadCount(data.unread_count))
        .catch(() => {});
    };

    fetchCount();
    const interval = setInterval(fetchCount, 30000);
    return () => clearInterval(interval);
  }, [user?.userId]);

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

        <button
          onClick={() => navigate('/notifications')}
          aria-label="Open notifications"
          className="p-2 -mr-2 rounded-full hover:bg-gray-100 transition-colors relative"
        >
          <Bell size={20} className="text-gray-700" />
          {unreadCount > 0 && (
            <span className="absolute top-0.5 right-0.5 min-w-[18px] h-[18px] bg-red-500 rounded-full flex items-center justify-center">
              <span className="text-[10px] font-bold text-white leading-none">
                {unreadCount > 99 ? '99+' : unreadCount}
              </span>
            </span>
          )}
        </button>
      </div>
    </header>
  );
}
