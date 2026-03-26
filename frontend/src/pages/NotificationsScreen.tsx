import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, Bell, BellOff, CheckCheck, Info, AlertTriangle, Clock, Megaphone } from 'lucide-react';
import { getNotifications, markAllNotificationsRead, markNotificationRead, type Notification } from '../features/notifications/services/notifications-api';
import { useAuth } from '../services/AuthContext';

const typeConfig: Record<string, { icon: typeof Bell; color: string; bg: string }> = {
  info: { icon: Info, color: 'text-blue-600', bg: 'bg-blue-50' },
  reminder: { icon: Clock, color: 'text-amber-600', bg: 'bg-amber-50' },
  alert: { icon: AlertTriangle, color: 'text-red-600', bg: 'bg-red-50' },
  update: { icon: Megaphone, color: 'text-emerald-600', bg: 'bg-emerald-50' },
};

function timeAgo(dateStr: string): string {
  const now = new Date();
  const date = new Date(dateStr + 'Z');
  const diff = Math.floor((now.getTime() - date.getTime()) / 1000);
  if (diff < 60) return 'just now';
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  if (diff < 604800) return `${Math.floor(diff / 86400)}d ago`;
  return date.toLocaleDateString();
}

export default function NotificationsScreen() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const userId = user?.userId;
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<'all' | 'unread'>('all');

  useEffect(() => {
    if (!userId) return;
    loadNotifications();
  }, [userId]);

  async function loadNotifications() {
    if (!userId) return;
    try {
      const data = await getNotifications(userId);
      setNotifications(data.notifications);
    } catch (err) {
      console.error('Failed to load notifications:', err);
    } finally {
      setLoading(false);
    }
  }

  async function handleMarkRead(notifId: number) {
    try {
      await markNotificationRead(notifId);
      setNotifications(prev =>
        prev.map(n => (n.id === notifId ? { ...n, read: true } : n))
      );
    } catch (err) {
      console.error('Failed to mark as read:', err);
    }
  }

  async function handleMarkAllRead() {
    if (!userId) return;
    try {
      await markAllNotificationsRead(userId);
      setNotifications(prev => prev.map(n => ({ ...n, read: true })));
    } catch (err) {
      console.error('Failed to mark all as read:', err);
    }
  }

  const filtered = filter === 'unread'
    ? notifications.filter(n => !n.read)
    : notifications;

  const unreadCount = notifications.filter(n => !n.read).length;

  return (
    <div className="min-h-screen bg-gray-50 pb-24">
      {/* Header */}
      <header className="fixed top-0 left-0 right-0 z-50 bg-white/90 backdrop-blur-md border-b border-gray-100">
        <div className="flex items-center justify-between h-14 px-4 max-w-lg mx-auto">
          <button
            onClick={() => navigate(-1)}
            className="p-2 -ml-2 rounded-full hover:bg-gray-100 transition-colors"
          >
            <ArrowLeft size={22} className="text-gray-700" />
          </button>
          <h1 className="text-base font-semibold text-gray-800 font-[Fredoka]">
            Notifications
          </h1>
          {unreadCount > 0 ? (
            <button
              onClick={handleMarkAllRead}
              className="p-2 -mr-2 rounded-full hover:bg-gray-100 transition-colors"
              title="Mark all as read"
            >
              <CheckCheck size={20} className="text-emerald-600" />
            </button>
          ) : (
            <div className="w-10" />
          )}
        </div>
      </header>

      <div className="pt-16 px-4 max-w-lg mx-auto">
        {/* Filter tabs */}
        <div className="flex gap-2 mb-4">
          {(['all', 'unread'] as const).map(f => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`px-4 py-2 rounded-full text-sm font-medium transition-colors ${
                filter === f
                  ? 'bg-emerald-600 text-white'
                  : 'bg-white text-gray-600 border border-gray-200 hover:bg-gray-50'
              }`}
            >
              {f === 'all' ? 'All' : `Unread (${unreadCount})`}
            </button>
          ))}
        </div>

        {/* Notification list */}
        {loading ? (
          <div className="text-center py-12 text-gray-400">Loading...</div>
        ) : filtered.length === 0 ? (
          <div className="text-center py-16">
            <BellOff size={48} className="mx-auto text-gray-300 mb-4" />
            <p className="text-gray-500 font-medium">
              {filter === 'unread' ? 'No unread notifications' : 'No notifications yet'}
            </p>
            <p className="text-gray-400 text-sm mt-1">
              {filter === 'unread'
                ? 'You\'re all caught up!'
                : 'Notifications about your trip will appear here'}
            </p>
          </div>
        ) : (
          <div className="space-y-2">
            {filtered.map(notif => {
              const config = typeConfig[notif.type] || typeConfig.info;
              const Icon = config.icon;
              return (
                <button
                  key={notif.id}
                  onClick={() => {
                    if (!notif.read) handleMarkRead(notif.id);
                    if (notif.link) navigate(notif.link);
                  }}
                  className={`w-full text-left rounded-xl p-4 transition-all ${
                    notif.read
                      ? 'bg-white border border-gray-100'
                      : 'bg-white border-l-4 border-l-emerald-500 border border-gray-100 shadow-sm'
                  }`}
                >
                  <div className="flex gap-3">
                    <div className={`w-10 h-10 rounded-full ${config.bg} flex items-center justify-center flex-shrink-0`}>
                      <Icon size={18} className={config.color} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-start justify-between gap-2">
                        <h3 className={`text-sm font-semibold ${notif.read ? 'text-gray-600' : 'text-gray-900'}`}>
                          {notif.title}
                        </h3>
                        {!notif.read && (
                          <span className="w-2 h-2 rounded-full bg-emerald-500 flex-shrink-0 mt-1.5" />
                        )}
                      </div>
                      <p className={`text-sm mt-0.5 ${notif.read ? 'text-gray-400' : 'text-gray-600'}`}>
                        {notif.body}
                      </p>
                      <p className="text-xs text-gray-400 mt-1">{timeAgo(notif.created_at)}</p>
                    </div>
                  </div>
                </button>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
