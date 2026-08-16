import { Bell, Loader2, ChevronDown, ChevronUp } from 'lucide-react';
import { useEffect, useState } from 'react';
import { getMyAnnouncements, markAnnouncementRead, type Announcement } from '../../trip/services/trip-api';
import AppHeader from '../../../shared/components/AppHeader';

function formatDate(iso: string) {
  const d = new Date(iso);
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
}

function AnnouncementCard({ ann, onRead }: { ann: Announcement; onRead: (id: string) => void }) {
  const [open, setOpen] = useState(false);

  function handleToggle() {
    const nextOpen = !open;
    setOpen(nextOpen);
    if (nextOpen && !ann.is_read) {
      onRead(ann.id);
    }
  }

  return (
    <div className={`bg-white rounded-2xl border shadow-sm overflow-hidden ${ann.is_read ? 'border-gray-100' : 'border-emerald-200'}`}>
      <button
        onClick={handleToggle}
        className="w-full flex items-center gap-3 p-4 text-left"
      >
        <div className={`w-9 h-9 rounded-xl flex items-center justify-center shrink-0 ${ann.is_read ? 'bg-gray-50' : 'bg-emerald-50'}`}>
          <Bell size={16} className="text-emerald-600" />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 min-w-0">
            {!ann.is_read && (
              <span
                aria-label="Unread notification"
                className="w-2 h-2 rounded-full bg-emerald-500 shrink-0"
              />
            )}
            <h3 className="text-sm font-semibold text-gray-800 truncate">{ann.title}</h3>
          </div>
          <span className="text-xs text-gray-400">{formatDate(ann.created_at)}</span>
        </div>
        {open
          ? <ChevronUp size={16} className="text-gray-400 shrink-0" />
          : <ChevronDown size={16} className="text-gray-400 shrink-0" />
        }
      </button>

      {open && (
        <div className="px-4 pb-4 pt-0 border-t border-gray-50">
          <p className="text-sm text-gray-600 leading-relaxed mt-3">{ann.body}</p>
          <p className="text-xs text-emerald-600 mt-2 font-medium">— {ann.sent_by}</p>
        </div>
      )}
    </div>
  );
}

export default function NotificationsScreen() {
  const [announcements, setAnnouncements] = useState<Announcement[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getMyAnnouncements()
      .then(r => setAnnouncements(r.announcements))
      .catch(e => setError(e instanceof Error ? e.message : 'Failed to load notifications'))
      .finally(() => setLoading(false));
  }, []);

  async function handleReadAnnouncement(id: string) {
    try {
      await markAnnouncementRead(id);
      setAnnouncements(current =>
        current.map(ann => ann.id === id ? { ...ann, is_read: true } : ann)
      );
    } catch {
      // Keep the card unread so expanding it again can retry the read receipt.
    }
  }

  return (
    <div className="min-h-screen bg-gray-50" style={{ paddingBottom: 'calc(80px + env(safe-area-inset-bottom))' }}>
      <AppHeader title="Notifications" />
      <div className="pt-14" />

      <div className="px-4 py-4 space-y-3">
        {loading && (
          <div className="flex justify-center py-12">
            <Loader2 className="animate-spin text-emerald-600" size={28} />
          </div>
        )}

        {error && (
          <div className="bg-red-50 rounded-2xl p-4 text-center">
            <p className="text-sm text-red-600">{error}</p>
          </div>
        )}

        {!loading && !error && announcements.length === 0 && (
          <div className="flex flex-col items-center justify-center py-16 gap-3">
            <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center">
              <Bell size={28} className="text-gray-300" />
            </div>
            <p className="text-sm font-medium text-gray-500">No notifications yet</p>
            <p className="text-xs text-gray-400 text-center">The Parrot team will send updates here</p>
          </div>
        )}

        {announcements.map((ann) => (
          <AnnouncementCard
            key={ann.id}
            ann={ann}
            onRead={handleReadAnnouncement}
          />
        ))}
      </div>
    </div>
  );
}
