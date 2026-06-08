import { useState } from 'react';
import { Map, QrCode, Phone, LogOut, ChevronRight, CheckCircle2, Circle, AlertCircle, Headphones } from 'lucide-react';
import { useAuth } from '../../../app/providers/auth-context';

// ── Mock data ──────────────────────────────────────────────────────────────────

const MOCK_TRIP = {
  title: 'Galápagos',
  dates: 'Jul 10 — Jul 16, 2026',
};

const MOCK_DAYS = [
  {
    id: '1',
    label: 'Day 1',
    date: 'Thu, Jul 10',
    activities: [
      {
        id: 'a1', time: '10:00', title: 'Airport reception',
        description: 'Pick up travelers at Baltra Airport. Check all names against the manifest.',
        travelers_expected: 12, travelers_checked_in: 9,
      },
      {
        id: 'a2', time: '13:00', title: 'Hotel check-in & welcome briefing',
        description: 'Distribute room keys. Run 30-min briefing on trip rules and safety.',
        travelers_expected: 12, travelers_checked_in: 12,
      },
      {
        id: 'a3', time: '19:30', title: 'Welcome dinner',
        description: 'Confirm reservation at restaurant. Seat everyone, introduce local guides.',
        travelers_expected: 12, travelers_checked_in: 0,
      },
    ],
  },
  {
    id: '2',
    label: 'Day 2',
    date: 'Fri, Jul 11',
    activities: [
      {
        id: 'a4', time: '07:30', title: 'Breakfast & kit distribution',
        description: 'Hand out snorkel kits and water bottles. Check allergies list.',
        travelers_expected: 12, travelers_checked_in: 0,
      },
      {
        id: 'a5', time: '09:00', title: 'Boat tour — Las Tintoreras',
        description: 'Coordinate boarding. Lifejackets mandatory. Count heads before departure.',
        travelers_expected: 12, travelers_checked_in: 0,
      },
      {
        id: 'a6', time: '16:00', title: 'Optional snorkeling',
        description: 'Voluntary activity. Confirm who is joining and who stays at the hotel.',
        travelers_expected: 6, travelers_checked_in: 0,
      },
    ],
  },
  {
    id: '3',
    label: 'Day 3',
    date: 'Sat, Jul 12',
    activities: [
      {
        id: 'a7', time: '08:00', title: 'Morning hike — Sierra Negra',
        description: 'Check equipment. Confirm guide availability. Sunscreen and water for everyone.',
        travelers_expected: 12, travelers_checked_in: 0,
      },
      {
        id: 'a8', time: '20:00', title: 'Closing party',
        description: 'Setup venue by 19:00. Coordinate DJ and catering arrival.',
        travelers_expected: 12, travelers_checked_in: 0,
      },
    ],
  },
];

const MOCK_CONTACTS = [
  {
    category: 'Local guides',
    contacts: [
      { id: 'c1', name: 'Carlos Mendoza', role: 'Lead guide', phone: '+593 99 123 4567' },
      { id: 'c2', name: 'Ana Torres', role: 'Naturalist guide', phone: '+593 99 234 5678' },
    ],
  },
  {
    category: 'Accommodation',
    contacts: [
      { id: 'c3', name: 'Hotel Galápagos Dreams', role: 'Front desk', phone: '+593 5 252 6000' },
    ],
  },
  {
    category: 'Transport',
    contacts: [
      { id: 'c4', name: 'Isla Transfers', role: 'Boat operator', phone: '+593 99 345 6789' },
      { id: 'c5', name: 'Airport Shuttle', role: 'Driver — Jorge', phone: '+593 99 456 7890' },
    ],
  },
  {
    category: 'Emergency',
    contacts: [
      { id: 'c6', name: 'Local hospital', role: 'Hospital Oskar Jandl', phone: '+593 5 252 0118' },
      { id: 'c7', name: 'Parrot Trips HQ', role: '24h emergency line', phone: '+55 11 91234-5678' },
    ],
  },
];

// ── Sub-screens ────────────────────────────────────────────────────────────────

function ItineraryTab() {
  const [openDay, setOpenDay] = useState<string | null>('1');
  const [openActivity, setOpenActivity] = useState<string | null>(null);

  return (
    <div className="px-4 py-5 space-y-3 pb-24">
      {MOCK_DAYS.map((day) => {
        const isOpen = openDay === day.id;
        const totalExpected = day.activities.reduce((s, a) => s + a.travelers_expected, 0);
        const totalChecked = day.activities.reduce((s, a) => s + a.travelers_checked_in, 0);

        return (
          <div key={day.id} className="bg-white rounded-2xl shadow-sm overflow-hidden">
            {/* Day header */}
            <button
              onClick={() => setOpenDay(isOpen ? null : day.id)}
              className="w-full flex items-center justify-between px-4 py-4"
            >
              <div className="text-left">
                <p className="font-semibold text-gray-900">{day.label}</p>
                <p className="text-xs text-gray-400 mt-0.5">{day.date}</p>
              </div>
              <div className="flex items-center gap-3">
                <span className="text-xs text-gray-500">{totalChecked}/{totalExpected} ✓</span>
                <ChevronRight
                  size={18}
                  className={`text-gray-400 transition-transform ${isOpen ? 'rotate-90' : ''}`}
                />
              </div>
            </button>

            {/* Activities */}
            {isOpen && (
              <div className="border-t border-gray-100 divide-y divide-gray-50">
                {day.activities.map((act) => {
                  const isActivityOpen = openActivity === act.id;
                  const allChecked = act.travelers_checked_in >= act.travelers_expected;
                  const partialChecked = act.travelers_checked_in > 0 && !allChecked;

                  return (
                    <div key={act.id}>
                      <button
                        onClick={() => setOpenActivity(isActivityOpen ? null : act.id)}
                        className="w-full flex items-start gap-3 px-4 py-3 text-left"
                      >
                        <div className="mt-0.5 flex-shrink-0">
                          {allChecked
                            ? <CheckCircle2 size={20} className="text-emerald-500" />
                            : partialChecked
                            ? <AlertCircle size={20} className="text-amber-400" />
                            : <Circle size={20} className="text-gray-300" />
                          }
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium text-gray-800">{act.title}</p>
                          <p className="text-xs text-gray-400 mt-0.5">{act.time} · {act.travelers_checked_in}/{act.travelers_expected} travelers</p>
                        </div>
                        <ChevronRight
                          size={16}
                          className={`text-gray-300 mt-1 flex-shrink-0 transition-transform ${isActivityOpen ? 'rotate-90' : ''}`}
                        />
                      </button>

                      {/* Activity detail */}
                      {isActivityOpen && (
                        <div className="px-4 pb-4 pt-1 bg-gray-50 space-y-3">
                          <p className="text-sm text-gray-600">{act.description}</p>
                          <div className="flex items-center justify-between">
                            <span className="text-xs text-gray-500">
                              {act.travelers_checked_in} of {act.travelers_expected} checked in
                            </span>
                            <button className="flex items-center gap-1.5 bg-emerald-600 text-white text-xs font-medium px-3 py-1.5 rounded-lg">
                              <QrCode size={14} />
                              Scan QR
                            </button>
                          </div>
                          {/* Attendance bar */}
                          <div className="w-full bg-gray-200 rounded-full h-1.5">
                            <div
                              className="bg-emerald-500 h-1.5 rounded-full transition-all"
                              style={{ width: `${(act.travelers_checked_in / act.travelers_expected) * 100}%` }}
                            />
                          </div>
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
      {/* Scanner area */}
      <div className="bg-white rounded-2xl shadow-sm overflow-hidden">
        <div className="bg-emerald-700 px-4 py-3">
          <p className="text-white font-semibold text-sm">Scan traveler QR Code</p>
          <p className="text-emerald-200 text-xs mt-0.5">Point camera at traveler's QR to check them in</p>
        </div>
        <div className="p-4">
          {/* Placeholder camera viewfinder */}
          <div className="w-full aspect-square bg-gray-100 rounded-xl flex flex-col items-center justify-center gap-3 border-2 border-dashed border-gray-300">
            <QrCode size={48} className="text-gray-300" />
            <p className="text-sm text-gray-400">Camera preview</p>
            <p className="text-xs text-gray-300">(QR scanner integration pending)</p>
          </div>
        </div>
      </div>

      {/* Activity selector */}
      <div className="bg-white rounded-2xl shadow-sm p-4 space-y-2">
        <p className="text-sm font-semibold text-gray-700">Checking in for:</p>
        <select className="w-full border border-gray-200 rounded-xl px-3 py-2.5 text-sm text-gray-700 bg-gray-50 focus:outline-none focus:ring-2 focus:ring-emerald-500">
          <option>Day 1 · 10:00 — Airport reception</option>
          <option>Day 1 · 13:00 — Hotel check-in & welcome briefing</option>
          <option>Day 1 · 19:30 — Welcome dinner</option>
          <option>Day 2 · 07:30 — Breakfast & kit distribution</option>
        </select>
      </div>

      {/* Last scans */}
      <div className="bg-white rounded-2xl shadow-sm overflow-hidden">
        <div className="px-4 py-3 border-b border-gray-100">
          <p className="text-sm font-semibold text-gray-700">Recent scans</p>
        </div>
        <div className="divide-y divide-gray-50">
          {[
            { name: 'Maria Souza', time: '10:04', status: 'checked' },
            { name: 'James Walker', time: '10:07', status: 'checked' },
            { name: 'Yuki Tanaka', time: '10:09', status: 'checked' },
          ].map((scan) => (
            <div key={scan.name} className="flex items-center justify-between px-4 py-3">
              <div>
                <p className="text-sm font-medium text-gray-800">{scan.name}</p>
                <p className="text-xs text-gray-400">{scan.time}</p>
              </div>
              <CheckCircle2 size={18} className="text-emerald-500" />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function ContactsTab() {
  return (
    <div className="px-4 py-5 pb-24 space-y-5">
      {MOCK_CONTACTS.map((group) => (
        <div key={group.category} className="bg-white rounded-2xl shadow-sm overflow-hidden">
          <div className="px-4 py-3 bg-gray-50 border-b border-gray-100">
            <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide">{group.category}</p>
          </div>
          <div className="divide-y divide-gray-50">
            {group.contacts.map((contact) => (
              <div key={contact.id} className="flex items-center justify-between px-4 py-3">
                <div>
                  <p className="text-sm font-medium text-gray-800">{contact.name}</p>
                  <p className="text-xs text-gray-400">{contact.role}</p>
                </div>
                <a
                  href={`tel:${contact.phone}`}
                  className="flex items-center gap-1.5 bg-emerald-50 text-emerald-700 text-xs font-medium px-3 py-1.5 rounded-lg"
                >
                  <Phone size={13} />
                  {contact.phone}
                </a>
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

export default function StaffScreen() {
  const { user, logout } = useAuth();
  const [activeTab, setActiveTab] = useState<Tab>('itinerary');

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* Header */}
      <div className="bg-emerald-700 text-white px-4 pt-10 pb-5">
        <div className="flex items-center justify-between mb-1">
          <span className="text-emerald-200 text-xs font-semibold uppercase tracking-widest">Staff</span>
          <button onClick={logout} className="flex items-center gap-1 text-emerald-300 text-sm hover:text-white">
            <LogOut size={14} />
            Sign out
          </button>
        </div>
        <h1 className="text-2xl font-bold">Hi, {user?.name?.split(' ')[0] ?? 'Staff'} 👋</h1>
        <p className="text-emerald-200 text-sm mt-0.5">{MOCK_TRIP.title} · {MOCK_TRIP.dates}</p>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto">
        {activeTab === 'itinerary' && <ItineraryTab />}
        {activeTab === 'scanner' && <QrScannerTab />}
        {activeTab === 'contacts' && <ContactsTab />}
      </div>

      {/* Bottom nav */}
      <nav className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 z-50 pb-safe">
        <div className="flex items-center justify-around h-16 max-w-lg mx-auto">
          {[
            { id: 'itinerary', icon: Map, label: 'Itinerary' },
            { id: 'scanner',   icon: QrCode, label: 'QR Scan' },
            { id: 'contacts',  icon: Headphones, label: 'Contacts' },
          ].map(({ id, icon: Icon, label }) => {
            const isActive = activeTab === id;
            return (
              <button
                key={id}
                onClick={() => setActiveTab(id as Tab)}
                className={`flex flex-col items-center justify-center w-full h-full transition-colors ${
                  isActive ? 'text-emerald-700' : 'text-gray-400 hover:text-gray-600'
                }`}
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
