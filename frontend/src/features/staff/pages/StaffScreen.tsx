import { useCallback, useEffect, useRef, useState } from 'react';
import { Html5Qrcode } from 'html5-qrcode';
import { Map, QrCode, Phone, LogOut, ChevronRight, Circle, Headphones, Eye, Bell, Send, Loader2, CheckCircle, MapPin, Pencil, Trash2, X, Check } from 'lucide-react';
import { useAuth } from '../../../app/providers/auth-context';
import {
  getActivityTravelers,
  getStaffAnnouncements,
  getStaffContacts,
  getStaffTrip,
  scanActivityTraveler,
  sendAnnouncement,
  updateAnnouncement,
  deleteAnnouncement,
  type ActivityTraveler,
  type StaffAnnouncement,
  type ActivityScanResponse,
  type CheckinDetail,
  type CheckinStep,
  type StaffActivity,
  type StaffContactGroup,
  type StaffDay,
  type StaffTrip,
} from '../services/staff-api';

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

function ActivityScanPanel({
  activity,
  onCheckedIn,
  onClose,
}: {
  activity: StaffActivity;
  onCheckedIn: (activityId: string) => void;
  onClose: () => void;
}) {
  const scannerElementId = useRef(`staff-activity-scanner-${activity.id}-${Math.random().toString(36).slice(2)}`);
  const scannerRef = useRef<Html5Qrcode | null>(null);
  const submittingRef = useRef(false);
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState<ActivityScanResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [cameraError, setCameraError] = useState<string | null>(null);
  const [cameraReady, setCameraReady] = useState(false);
  const [showTravelerList, setShowTravelerList] = useState(false);
  const [travelerList, setTravelerList] = useState<ActivityTraveler[]>([]);
  const [loadingTravelers, setLoadingTravelers] = useState(false);

  const submitScan = useCallback(async (payload: string) => {
    const trimmedPayload = payload.trim();
    if (!trimmedPayload) return;
    if (submittingRef.current) return;

    submittingRef.current = true;
    setSubmitting(true);
    setError(null);
    setResult(null);
    try {
      const response = await scanActivityTraveler(activity.id, trimmedPayload);
      setResult(response);
      if (response.status === 'checked_in') {
        onCheckedIn(activity.id);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to scan traveler');
    } finally {
      submittingRef.current = false;
      setSubmitting(false);
    }
  }, [activity.id, onCheckedIn]);

  useEffect(() => {
    const scanner = new Html5Qrcode(scannerElementId.current);
    scannerRef.current = scanner;
    let disposed = false;

    scanner
      .start(
        { facingMode: 'environment' },
        { fps: 10, qrbox: { width: 240, height: 240 } },
        decodedText => {
          void submitScan(decodedText);
        },
        () => {}
      )
      .then(() => {
        if (!disposed) {
          setCameraReady(true);
        }
      })
      .catch(e => {
        if (!disposed) {
          setCameraError(e instanceof Error ? e.message : 'Camera unavailable. Select traveler by name instead.');
          setShowTravelerList(true);
        }
      });

    return () => {
      disposed = true;
      const activeScanner = scannerRef.current;
      scannerRef.current = null;
      setCameraReady(false);
      if (!activeScanner) return;
      activeScanner
        .stop()
        .catch(() => undefined)
        .finally(() => {
          activeScanner.clear();
        });
    };
  }, [submitScan]);

  const travelerName = result?.traveler_name ?? 'Traveler';

  return (
    <div className="bg-white rounded-lg border border-emerald-100 p-3 space-y-3">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-sm font-semibold text-gray-900">Scan Travelers</p>
          <p className="text-xs text-gray-500">{activity.name}</p>
        </div>
        <button type="button" onClick={onClose} className="text-xs font-medium text-gray-400 hover:text-gray-600">
          Close
        </button>
      </div>

      <div className="rounded-lg border border-gray-200 bg-gray-950 p-2">
        <div id={scannerElementId.current} className="min-h-48 overflow-hidden rounded-md bg-black" />
      </div>
      <div className="flex items-center justify-between gap-3">
        <div>
          <p className="text-sm font-semibold text-gray-900">Camera scanner</p>
          <p className="text-xs text-gray-500">
            {submitting ? 'Processing scan...' : cameraReady ? 'Point the camera at a traveler QR code.' : 'Starting camera...'}
          </p>
        </div>
        <button
          type="button"
          onClick={async () => {
            const next = !showTravelerList;
            setShowTravelerList(next);
            if (next && travelerList.length === 0) {
              setLoadingTravelers(true);
              try {
                const res = await getActivityTravelers(activity.id);
                setTravelerList(res.travelers);
              } catch { /* ignore */ } finally {
                setLoadingTravelers(false);
              }
            }
          }}
          className="text-xs font-semibold text-emerald-700"
        >
          {showTravelerList ? 'Hide list' : 'Select by name'}
        </button>
      </div>

      {cameraError && (
        <div className="rounded-lg bg-amber-50 border border-amber-100 px-3 py-2">
          <p className="text-sm font-medium text-amber-800">{cameraError}</p>
        </div>
      )}

      {showTravelerList && (
        <div className="rounded-lg border border-gray-200 overflow-hidden">
          <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide px-3 py-2 bg-gray-50 border-b border-gray-100">
            Select traveler to check in
          </p>
          {loadingTravelers ? (
            <div className="flex justify-center py-4">
              <Loader2 size={18} className="animate-spin text-emerald-600" />
            </div>
          ) : (
            travelerList.map(traveler => (
              <button
                key={traveler.id}
                type="button"
                disabled={submitting}
                onClick={() => submitScan(traveler.qr_payload)}
                className="w-full flex items-center justify-between px-3 py-2.5 text-left border-b border-gray-50 last:border-0 hover:bg-emerald-50 transition-colors disabled:opacity-50"
              >
                <span className="text-sm font-medium text-gray-800">{traveler.name}</span>
                <span className="text-xs text-emerald-700 font-semibold">Check in →</span>
              </button>
            ))
          )}
        </div>
      )}

      {result?.status === 'checked_in' && (
        <div className="rounded-lg bg-emerald-50 border border-emerald-100 px-3 py-2">
          <p className="text-sm font-medium text-emerald-800">
            {result.traveler_name || travelerName} — scan {result.scan_number} of {result.max_checkins}
          </p>
        </div>
      )}

      {result?.status === 'already_checked_in' && (
        <div className="rounded-lg bg-amber-50 border border-amber-100 px-3 py-2 space-y-1">
          <p className="text-sm font-medium text-amber-800">
            {result.traveler_name || travelerName} already completed all {result.max_checkins} scan{(result.max_checkins ?? 1) > 1 ? 's' : ''}.
          </p>
          {result.scanned_by_name && (
            <p className="text-xs text-amber-700">Last scan by {result.scanned_by_name}</p>
          )}
        </div>
      )}

      {error && (
        <div className="rounded-lg bg-red-50 border border-red-100 px-3 py-2">
          <p className="text-sm font-medium text-red-700">{error}</p>
        </div>
      )}
    </div>
  );
}

function ItineraryTab({
  days,
  loading,
  error,
  onActivityCheckedIn,
}: {
  days: StaffDay[];
  loading: boolean;
  error: string | null;
  onActivityCheckedIn: (activityId: string) => void;
}) {
  const [openDay, setOpenDay] = useState<string | null>(null);
  const [openActivity, setOpenActivity] = useState<string | null>(null);
  const [scanActivityId, setScanActivityId] = useState<string | null>(null);

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
                          <p className="text-xs font-medium text-emerald-700 mt-1">
                            {act.checkin_steps.length > 0
                              ? act.checkin_steps.map(s => `Step ${s.step}: ${s.count}`).join(' · ')
                              : `0 / ${act.traveler_count} scanned`}
                          </p>
                        </div>
                        <ChevronRight size={16} className={`text-gray-300 mt-1 flex-shrink-0 transition-transform ${isActivityOpen ? 'rotate-90' : ''}`} />
                      </button>

                      {isActivityOpen && (
                        <div className="px-4 pb-4 pt-1 bg-gray-50 space-y-2">
                          {act.address && (
                            <a
                              href={`https://maps.google.com/?q=${encodeURIComponent(act.address)}`}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="flex items-center gap-1.5 text-xs text-blue-600 font-medium"
                            >
                              <MapPin size={12} />
                              {act.address}
                            </a>
                          )}
                          {act.amount_brl && (
                            <p className="text-xs text-emerald-600 font-medium">R$ {act.amount_brl.toFixed(2)}</p>
                          )}
                          <div className="rounded-lg bg-white border border-gray-100 overflow-hidden">
                            <div className="flex items-center justify-between px-3 py-2 border-b border-gray-50">
                              <p className="text-xs font-semibold text-gray-600 uppercase tracking-wide">
                                Attendance · {act.max_checkins} scan{act.max_checkins > 1 ? 's' : ''} per traveler
                              </p>
                              <button
                                type="button"
                                onClick={() => setScanActivityId(act.id)}
                                className="flex items-center gap-1.5 rounded-lg bg-emerald-700 px-3 py-1.5 text-xs font-semibold text-white"
                              >
                                <QrCode size={13} />
                                Scan
                              </button>
                            </div>

                            {/* Steps with present travelers */}
                            {Array.from({ length: act.max_checkins }, (_, i) => i + 1).map(step => {
                              const stepData = act.checkin_steps.find((s: CheckinStep) => s.step === step);
                              const count = stepData?.count ?? 0;
                              return (
                                <div key={step} className="px-3 py-2 border-b border-gray-50">
                                  <div className="flex items-center justify-between mb-1.5">
                                    <span className="text-xs font-semibold text-emerald-700">
                                      ✅ Step {step} — {count} / {act.traveler_count} checked in
                                    </span>
                                  </div>
                                  {stepData && stepData.details.map((d: CheckinDetail, i: number) => (
                                    <div key={i} className="flex items-center justify-between py-0.5">
                                      <span className="text-xs text-gray-700">{d.name}</span>
                                      {d.checked_in_at && (
                                        <span className="text-xs text-gray-400">
                                          {new Date(d.checked_in_at).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: false })}
                                        </span>
                                      )}
                                    </div>
                                  ))}
                                </div>
                              );
                            })}

                            {/* Absent travelers */}
                            {act.absent_travelers.length > 0 && (
                              <div className="px-3 py-2">
                                <p className="text-xs font-semibold text-red-500 mb-1.5">
                                  ⏳ Not yet arrived — {act.absent_travelers.length}
                                </p>
                                {act.absent_travelers.map((name: string, i: number) => (
                                  <p key={i} className="text-xs text-gray-500 py-0.5">{name}</p>
                                ))}
                              </div>
                            )}

                            {act.absent_travelers.length === 0 && act.checkin_steps.length > 0 && (
                              <div className="px-3 py-2">
                                <p className="text-xs font-semibold text-emerald-600">🎉 Everyone is here!</p>
                              </div>
                            )}
                          </div>
                          {scanActivityId === act.id && (
                            <ActivityScanPanel
                              activity={act}
                              onCheckedIn={onActivityCheckedIn}
                              onClose={() => setScanActivityId(null)}
                            />
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
                    href={`https://wa.me/${contact.phone.replace(/\D/g, '')}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-1.5 bg-[#25D366] text-white text-xs font-medium px-3 py-1.5 rounded-lg whitespace-nowrap"
                  >
                    <svg viewBox="0 0 24 24" fill="currentColor" className="w-3.5 h-3.5 shrink-0" aria-hidden="true">
                      <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z" />
                    </svg>
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

// ── Announce tab ──────────────────────────────────────────────────────────────

function formatDate(iso: string) {
  const d = new Date(iso);
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
}

function AnnounceTab({ currentUserId }: { currentUserId: string }) {
  const [title, setTitle] = useState('');
  const [body, setBody] = useState('');
  const [isAnonymous, setIsAnonymous] = useState(false);
  const [sending, setSending] = useState(false);
  const [sent, setSent] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [announcements, setAnnouncements] = useState<StaffAnnouncement[]>([]);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editTitle, setEditTitle] = useState('');
  const [editBody, setEditBody] = useState('');
  const [saving, setSaving] = useState(false);

  const load = () => {
    getStaffAnnouncements()
      .then(r => setAnnouncements(r.announcements))
      .catch(() => {});
  };

  useEffect(() => { load(); }, []);

  const handleSend = async () => {
    if (!title.trim() || !body.trim()) return;
    setSending(true);
    setError(null);
    try {
      await sendAnnouncement(title.trim(), body.trim(), isAnonymous);
      setSent(true);
      setTitle('');
      setBody('');
      setIsAnonymous(false);
      load();
      setTimeout(() => setSent(false), 3000);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to send');
    } finally {
      setSending(false);
    }
  };

  const startEdit = (ann: StaffAnnouncement) => {
    setEditingId(ann.id);
    setEditTitle(ann.title);
    setEditBody(ann.body);
  };

  const handleSaveEdit = async () => {
    if (!editingId || !editTitle.trim() || !editBody.trim()) return;
    setSaving(true);
    try {
      await updateAnnouncement(editingId, editTitle.trim(), editBody.trim());
      setEditingId(null);
      load();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to update');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await deleteAnnouncement(id);
      load();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to delete');
    }
  };

  return (
    <div className="px-4 py-5 pb-24 space-y-4">
      {/* Compose form */}
      <div className="bg-white rounded-2xl shadow-sm p-4 space-y-4">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 bg-emerald-50 rounded-xl flex items-center justify-center">
            <Bell size={18} className="text-emerald-600" />
          </div>
          <div>
            <p className="text-sm font-semibold text-gray-800">Send Notification</p>
            <p className="text-xs text-gray-500">All travelers on this trip will see this</p>
          </div>
        </div>
        <div className="space-y-1">
          <label className="text-xs font-medium text-gray-500">Title</label>
          <input type="text" value={title} onChange={e => setTitle(e.target.value)}
            placeholder="e.g. Meeting point changed"
            className="w-full px-3 py-2.5 text-sm border border-gray-200 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none transition-all" />
        </div>
        <div className="space-y-1">
          <label className="text-xs font-medium text-gray-500">Message</label>
          <textarea value={body} onChange={e => setBody(e.target.value)}
            placeholder="Write your message here..." rows={4}
            className="w-full px-3 py-2.5 text-sm border border-gray-200 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none transition-all resize-none" />
        </div>
        <button
          type="button"
          onClick={() => setIsAnonymous(a => !a)}
          className={`flex items-center gap-2 text-xs font-medium px-3 py-2 rounded-xl transition-colors ${
            isAnonymous ? 'bg-gray-800 text-white' : 'bg-gray-100 text-gray-500 hover:bg-gray-200'
          }`}
        >
          <span>{isAnonymous ? '🕵️ Anonymous' : '👤 Send as yourself'}</span>
        </button>

        {error && <p className="text-xs text-red-600 text-center">{error}</p>}
        <button onClick={handleSend} disabled={sending || !title.trim() || !body.trim()}
          className={`w-full py-3 rounded-xl font-semibold text-sm flex items-center justify-center gap-2 transition-all ${sent ? 'bg-emerald-500 text-white' : 'bg-emerald-700 hover:bg-emerald-800 text-white disabled:opacity-50 disabled:cursor-not-allowed'}`}>
          {sending ? <><Loader2 size={16} className="animate-spin" /> Sending...</>
            : sent ? <><CheckCircle size={16} /> Sent!</>
            : <><Send size={16} /> Send to all travelers</>}
        </button>
      </div>

      {/* Sent messages */}
      {announcements.length > 0 && (
        <div className="space-y-3">
          <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Sent messages</p>
          {announcements.map(ann => (
            <div key={ann.id} className="bg-white rounded-2xl shadow-sm overflow-hidden">
              {editingId === ann.id ? (
                <div className="p-4 space-y-3">
                  <input type="text" value={editTitle} onChange={e => setEditTitle(e.target.value)}
                    className="w-full px-3 py-2 text-sm border border-gray-200 rounded-xl focus:ring-2 focus:ring-emerald-500 outline-none" />
                  <textarea value={editBody} onChange={e => setEditBody(e.target.value)} rows={3}
                    className="w-full px-3 py-2 text-sm border border-gray-200 rounded-xl focus:ring-2 focus:ring-emerald-500 outline-none resize-none" />
                  <div className="flex gap-2">
                    <button onClick={handleSaveEdit} disabled={saving}
                      className="flex-1 flex items-center justify-center gap-1.5 py-2 bg-emerald-700 text-white text-xs font-semibold rounded-xl">
                      {saving ? <Loader2 size={14} className="animate-spin" /> : <Check size={14} />} Save
                    </button>
                    <button onClick={() => setEditingId(null)}
                      className="flex-1 flex items-center justify-center gap-1.5 py-2 bg-gray-100 text-gray-600 text-xs font-semibold rounded-xl">
                      <X size={14} /> Cancel
                    </button>
                  </div>
                </div>
              ) : (
                <div className="p-4">
                  <div className="flex items-start justify-between gap-2 mb-1">
                    <p className="text-sm font-semibold text-gray-800">{ann.title}</p>
                    <span className="text-xs text-gray-400 whitespace-nowrap shrink-0">{formatDate(ann.created_at)}</span>
                  </div>
                  <p className="text-sm text-gray-600 leading-relaxed">{ann.body}</p>
                  {ann.is_anonymous && (
                    <span className="inline-flex items-center gap-1 mt-1 text-xs text-gray-400">🕵️ Sent anonymously</span>
                  )}
                  {ann.sent_by_user_id === currentUserId && (
                    <div className="flex gap-2 mt-3">
                      <button onClick={() => startEdit(ann)}
                        className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-emerald-700 bg-emerald-50 rounded-lg">
                        <Pencil size={12} /> Edit
                      </button>
                      <button onClick={() => handleDelete(ann.id)}
                        className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-red-600 bg-red-50 rounded-lg">
                        <Trash2 size={12} /> Delete
                      </button>
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ── Main screen ────────────────────────────────────────────────────────────────

type Tab = 'itinerary' | 'contacts' | 'announce';

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

  const handleActivityCheckedIn = (_activityId: string) => {
    getStaffTrip().then(setTrip).catch(() => {});
  };

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
          <ItineraryTab days={trip?.days ?? []} loading={loading} error={error} onActivityCheckedIn={handleActivityCheckedIn} />
        )}
        {activeTab === 'contacts' && <ContactsTab groups={contactGroups} loading={contactsLoading} error={contactsError} />}
        {activeTab === 'announce' && <AnnounceTab currentUserId={user?.userId ?? ''} />}
      </div>

      {/* Bottom nav */}
      <nav className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 z-50 pb-safe">
        <div className="flex items-center justify-around h-16 max-w-lg mx-auto">
          {[
            { id: 'itinerary', icon: Map, label: 'Itinerary' },
            { id: 'contacts', icon: Headphones, label: 'Contacts' },
            { id: 'announce', icon: Bell, label: 'Announce' },
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
