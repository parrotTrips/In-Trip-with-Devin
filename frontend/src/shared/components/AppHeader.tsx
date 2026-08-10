import { Bell, User } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useAvatar } from '../../app/providers/avatar-context';

interface AppHeaderProps {
  title: string;
}

export default function AppHeader({ title }: AppHeaderProps) {
  const navigate = useNavigate();
  const { avatarUrl } = useAvatar();

  return (
    <header className="fixed top-0 left-0 right-0 z-[60] bg-white/90 backdrop-blur-md border-b border-gray-100">
      <div className="flex items-center justify-between h-14 px-4 max-w-lg mx-auto">
        <button
          onClick={() => navigate('/profile')}
          className="w-10 h-10 flex items-center justify-center rounded-full hover:bg-gray-100 transition-colors overflow-hidden shrink-0"
          aria-label="My Profile"
        >
          {avatarUrl ? (
            <img src={avatarUrl} alt="Profile" className="w-10 h-10 rounded-full object-cover" />
          ) : (
            <User size={20} className="text-gray-500" />
          )}
        </button>

        <div className="flex items-center gap-2">
          <span className="text-lg">🦜</span>
          <h1 className="text-base font-semibold text-gray-800 font-[Fredoka]">{title}</h1>
        </div>

        <button
          onClick={() => navigate('/notifications')}
          className="w-10 h-10 flex items-center justify-center rounded-full hover:bg-gray-100 transition-colors"
          aria-label="Notifications"
        >
          <Bell size={20} className="text-gray-500" />
        </button>
      </div>
    </header>
  );
}
