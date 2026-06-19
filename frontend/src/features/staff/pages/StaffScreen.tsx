import { useEffect, useState } from 'react';
import { Map, QrCode, Phone, LogOut, ChevronRight, Circle, Headphones, Eye } from 'lucide-react';
import { useAuth } from '../../../app/providers/auth-context';
import { getStaffContacts, getStaffTrip, type StaffContactGroup, type StaffDay, type StaffTrip } from '../services/staff-api';

// ── Helpers ───────────────────────────────────────────────────────────────────

function formatDayDate(startsAt: string | null): string {
  if (!startsAt) return '';
  const d = new Date(startsAt);
  return d.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' });
}

function formatTime(startsAt: string | null): string {
  if (!startsAt) return '';
  const d = new Date(startsAt);
  return d.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: false });
}

function isTodayOrPast(startsAt: string | null): boolean {
  if (!startsAt) return false;
  const d = new Date(startsAt);
  d.setHours(0, 0, 0, 0);
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  return d <= today;
}

// ── Sub-screens ────────────────────────────────────────────────────────────────

function ItineraryTab({ days, loading, error }: { days: StaffDay[]; loading: boolean; error: string | null }) {
  const [openDay, setOpenDay] = useState<string | null>(null);
  const [openActivity, setOpenActivity] = useState<string | null>(null);

  // Auto-open today's day
  useEffect(() => {
    const today = days.find(d => isTodayOrPast(d.starts_at));
    if (today) setOpenDay(today.id);
  }, [days]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-48 gap-3">
        <div className="w-7 h-7 border-3 border-emerald-500 border-t-transparent rounded-full animate-spin" />
        <p className="text-gray-400 text-sm">Loading itinerary...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-48 px-6 gap-3">
        <p className="text-red-500 text-sm text-center">{error}</p>
      </div>
    );
  }

  if (days.length === 0) {
    return (
      <div className="flex items-center justify-center h-48">
        <p className="text-gray-400 text-sm">No itinerary found for this trip.</p>
      </div>
    );
  }

  return (
    <div className="px-4 py-5 space-y-3 pb-24">
      {days.map((day) => {
        const isOpen = openDay === day.id;
        const isToday = isTodayOrPast(day.starts_at) &&
          !days.find((d, i) => days.indexOf(day) < i && isTodayOrPast(d.starts_at));

        return (
          <div key={day.id} className={`bg-white rounded-2xl shadow-sm overflow-hidden ${isToday ? 'ring-2 ring-emerald-400' : ''}`}>
            <button
              onClick={() => setOpenDay(isOpen ? null : day.id)}
              className="w-full flex items-center justify-between px-4 py-4"
            >
              <div className="text-left">
                <div className="flex items-center gap-2">
                  <p className="font-semibold text-gray-900">{day.title}</p>
                  {isToday && <span className="text-xs bg-emerald-100 text-emerald-700 px-2 py-0.5 rounded-full font-medium">Today</span>}
                </div>
                <p className="text-xs text-gray-400 mt-0.5">{formatDayDate(day.starts_at)}</p>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-xs text-gray-400">{day.activities.length} activities</span>
                <ChevronRight size={18} className={`text-gray-400 transition-transform ${isOpen ? 'rotate-90' : ''}`} />
              </div>
            </button>

            {isOpen && (
              <div className="border-t border-gray-100 divide-y divide-gray-50">
                {day.activities.length === 0 && (
                  <p className="px-4 py-3 text-sm text-gray-400 italic">No activities for this day.</p>
                )}
                {day.activities.map((act) => {
                  const isActivityOpen = openActivity === act.id;
                  return (
                    <div key={act.id}>
                      <button
                        onClick={() => setOpenActivity(isActivityOpen ? null : act.id)}
                        className="w-full flex items-start gap-3 px-4 py-3 text-left"
                      >
                        <Circle size={20} className="text-gray-300 mt-0.5 flex-shrink-0" />
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium text-gray-800">{act.name}</p>
                          <p className="text-xs text-gray-400 mt-0.5">
                            {formatTime(act.starts_at)}
                            {act.duration_minutes ? ` · ${act.duration_minutes} min` : ''}
                          </p>
                        </div>
                        <ChevronRight size={16} className={`text-gray-300 mt-1 flex-shrink-0 transition-transform ${isActivityOpen ? 'rotate-90' : ''}`} />
                      </button>

                      {isActivityOpen && (
                        <div className="px-4 pb-4 pt-1 bg-gray-50 space-y-2">
                          <p className="text-sm text-gray-600">{act.short_description}</p>
                          {act.practical_info && (
                            <p className="text-xs text-gray-500 bg-white rounded-lg px-3 py-2 border border-gray-100">{act.practical_info}</p>
                          )}
                          {act.amount_brl && (
                            <p className="text-xs text-emerald-600 font-medium">R$ {act.amount_brl.toFixed(2)}</p>
                          )}
                          {act.staff_tasks.length > 0 && (
                            <div className="bg-white rounded-lg border border-emerald-100 overflow-hidden">
                              <div className="px-3 py-2 bg-emerald-50 border-b border-emerald-100">
                                <p className="text-xs font-semibold text-emerald-700 uppercase tracking-wide">My tasks</p>
                              </div>
                              <div className="divide-y divide-gray-100">
                                {act.staff_tasks.map((task) => (
                                  <div key={task.id} className="px-3 py-2">
                                    <p className="text-sm font-medium text-gray-800">{task.title}</p>
                                    {task.description && (
                                      <p className="text-xs text-gray-500 mt-0.5">{task.description}</p>
                                    )}
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

function QrScannerTab() {
  return (
    <div className="px-4 py-5 pb-24 space-y-5">
      <div className="bg-white rounded-2xl shadow-sm overflow-hidden">
        <div className="bg-emerald-700 px-4 py-3">
          <p className="text-white font-semibold text-sm">Scan traveler QR Code</p>
          <p className="text-emerald-200 text-xs mt-0.5">Point camera at traveler's QR to check them in</p>
        </div>
        <div className="p-4">
          <div className="w-full aspect-square bg-gray-100 rounded-xl flex flex-col items-center justify-center gap-3 border-2 border-dashed border-gray-300">
            <QrCode size={48} className="text-gray-300" />
            <p className="text-sm text-gray-400">Camera integration coming soon</p>
          </div>
        </div>
      </div>
    </div>
  );
}

function ContactsTab({ groups, loading, error }: { groups: StaffContactGroup[]; loading: boolean; error: string | null }) {
  if (loading) {
    return (
      <div className="flex items-center justify-center h-48 gap-3">
        <div className="w-7 h-7 border-3 border-emerald-500 border-t-transparent rounded-full animate-spin" />
        <p className="text-gray-400 text-sm">Loading contacts...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-48 px-6 gap-3">
        <p className="text-red-500 text-sm text-center">{error}</p>
      </div>
    );
  }

  if (groups.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-48 gap-2 px-6">
        <Phone size={32} className="text-gray-200" />
        <p className="text-gray-400 text-sm text-center">No contacts yet.</p>
        <p className="text-gray-300 text-xs text-center">Add contacts in the Staff Google Sheet and run the import.</p>
      </div>
    );
  }

  return (
    <div className="px-4 py-5 pb-24 space-y-5">
      {groups.map((group) => (
        <div key={group.category} className="bg-white rounded-2xl shadow-sm overflow-hidden">
          <div className="px-4 py-3 bg-gray-50 border-b border-gray-100">
            <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide">{group.category}</p>
          </div>
          <div className="divide-y divide-gray-50">
            {group.contacts.map((contact) => (
              <div key={contact.id} className="flex items-center justify-between px-4 py-3">
                <div>
                  <p className="text-sm font-medium text-gray-800">{contact.name}</p>
                  {contact.role && <p className="text-xs text-gray-400">{contact.role}</p>}
                </div>
                {contact.phone && (
                  <a
                    href={`tel:${contact.phone}`}
                    className="flex items-center gap-1.5 bg-emerald-50 text-emerald-700 text-xs font-medium px-3 py-1.5 rounded-lg"
                  >
                    <Phone size={13} />
                    {contact.phone}
                  </a>
                )}
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

// ── Main screen ────────────────────────────────────────────────────────────────

type Tab = 'itinerary' | 'scanner' | 'contacts';

interface Props {
  onSwitchToTravelerView: () => void;
}

export default function StaffScreen({ onSwitchToTravelerView }: Props) {
  const { user, logout } = useAuth();
  const [activeTab, setActiveTab] = useState<Tab>('itinerary');
  const [trip, setTrip] = useState<StaffTrip | null>(null);
  const [contactGroups, setContactGroups] = useState<StaffContactGroup[]>([]);
  const [loading, setLoading] = useState(true);
  const [contactsLoading, setContactsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [contactsError, setContactsError] = useState<string | null>(null);

  useEffect(() => {
    getStaffTrip()
      .then(setTrip)
      .catch(e => setError(e instanceof Error ? e.message : 'Failed to load trip'))
      .finally(() => setLoading(false));
    getStaffContacts()
      .then(r => setContactGroups(r.contacts))
      .catch(e => setContactsError(e instanceof Error ? e.message : 'Failed to load contacts'))
      .finally(() => setContactsLoading(false));
  }, []);

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* Header */}
      <div className="bg-emerald-700 text-white px-4 pt-10 pb-5">
        <div className="flex items-center justify-between mb-1">
          <span className="text-emerald-200 text-xs font-semibold uppercase tracking-widest">Staff</span>
          <div className="flex items-center gap-3">
            <button
              onClick={onSwitchToTravelerView}
              className="flex items-center gap-1.5 text-emerald-200 text-xs hover:text-white transition-colors"
            >
              <Eye size={14} />
              Traveler view
            </button>
            <button onClick={logout} className="flex items-center gap-1 text-emerald-300 text-xs hover:text-white">
              <LogOut size={13} />
              Sign out
            </button>
          </div>
        </div>
        <h1 className="text-2xl font-bold">Hi, {user?.name?.split(' ')[0] ?? 'Staff'} 👋</h1>
        <p className="text-emerald-200 text-sm mt-0.5">
          {trip?.title ?? 'Loading...'} {trip?.start_date ? `· ${trip.start_date}` : ''}
        </p>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto">
        {activeTab === 'itinerary' && (
          <ItineraryTab days={trip?.days ?? []} loading={loading} error={error} />
        )}
        {activeTab === 'scanner' && <QrScannerTab />}
        {activeTab === 'contacts' && <ContactsTab groups={contactGroups} loading={contactsLoading} error={contactsError} />}
      </div>

      {/* Bottom nav */}
      <nav className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 z-50 pb-safe">
        <div className="flex items-center justify-around h-16 max-w-lg mx-auto">
          {[
            { id: 'itinerary', icon: Map, label: 'Itinerary' },
            { id: 'scanner', icon: QrCode, label: 'QR Scan' },
            { id: 'contacts', icon: Headphones, label: 'Contacts' },
          ].map(({ id, icon: Icon, label }) => {
            const isActive = activeTab === id;
            return (
              <button
                key={id}
                onClick={() => setActiveTab(id as Tab)}
                className={`flex flex-col items-center justify-center w-full h-full transition-colors ${isActive ? 'text-emerald-700' : 'text-gray-400 hover:text-gray-600'}`}
              >
                <Icon size={22} strokeWidth={isActive ? 2.5 : 2} />
                <span className={`text-xs mt-1 ${isActive ? 'font-semibold' : 'font-medium'}`}>{label}</span>
                {isActive && <div className="absolute bottom-0 w-12 h-0.5 bg-emerald-700 rounded-t-full" />}
              </button>
            );
          })}
        </div>
      </nav>
    </div>
  );
}
