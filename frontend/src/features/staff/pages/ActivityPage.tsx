import { useCallback, useEffect, useRef, useState } from 'react';
import { Html5Qrcode } from 'html5-qrcode';
import { ArrowLeft, Camera, Check, Clock, Loader2, MapPin, Search, X } from 'lucide-react';

import {
  getActivityTravelers,
  previewActivityTravelerScan,
  scanActivityTraveler,
  type ActivityScanPreviewResponse,
  type ActivityScanResponse,
  type ActivityTraveler,
  type StaffActivity,
} from '../services/staff-api';

// After a check-in, the camera ignores that same QR for this long.
const SAME_QR_COOLDOWN_MS = 5000;

type TravelerStatus = 'not_arrived' | 'in_progress' | 'done';
type Filter = 'all' | TravelerStatus;

const STATUS_LABEL: Record<TravelerStatus, string> = {
  not_arrived: 'Not arrived',
  in_progress: 'In progress',
  done: 'Done',
};

const STATUS_STYLE: Record<TravelerStatus, string> = {
  not_arrived: 'bg-gray-100 text-gray-600',
  in_progress: 'bg-amber-100 text-amber-700',
  done: 'bg-emerald-100 text-emerald-700',
};

function statusOf(traveler: ActivityTraveler): TravelerStatus {
  if (traveler.checkin_count <= 0) return 'not_arrived';
  return traveler.checkin_count >= traveler.max_checkins ? 'done' : 'in_progress';
}

function formatClock(iso: string | null): string {
  if (!iso) return '';
  return new Date(iso).toLocaleTimeString('en-US', {
    timeZone: 'America/Sao_Paulo', hour: '2-digit', minute: '2-digit', hour12: false,
  });
}

/** Short vibration and beep so staff notice a successful check-in without looking. */
function signalCheckedIn() {
  try {
    navigator.vibrate?.(120);
  } catch { /* not supported */ }
  try {
    const AudioCtx = window.AudioContext
      ?? (window as unknown as { webkitAudioContext?: typeof AudioContext }).webkitAudioContext;
    if (!AudioCtx) return;
    const ctx = new AudioCtx();
    const oscillator = ctx.createOscillator();
    const gain = ctx.createGain();
    oscillator.frequency.value = 880;
    gain.gain.value = 0.15;
    oscillator.connect(gain);
    gain.connect(ctx.destination);
    oscillator.start();
    oscillator.stop(ctx.currentTime + 0.15);
    oscillator.onended = () => void ctx.close();
  } catch { /* audio blocked */ }
}

function CameraScanner({ onScan, onClose }: { onScan: (payload: string) => void; onClose: () => void }) {
  const elementId = useRef(`staff-activity-scanner-${Math.random().toString(36).slice(2)}`);
  const onScanRef = useRef(onScan);
  onScanRef.current = onScan;
  const [ready, setReady] = useState(false);
  const [cameraError, setCameraError] = useState<string | null>(null);

  useEffect(() => {
    const scanner = new Html5Qrcode(elementId.current);
    let disposed = false;
    scanner
      .start(
        { facingMode: 'environment' },
        { fps: 10, qrbox: { width: 240, height: 240 } },
        decodedText => onScanRef.current(decodedText),
        () => {}
      )
      .then(() => { if (!disposed) setReady(true); })
      .catch(e => {
        if (!disposed) setCameraError(e instanceof Error ? e.message : 'Camera unavailable. Check travelers in by name below.');
      });
    return () => {
      disposed = true;
      scanner.stop().catch(() => undefined).finally(() => scanner.clear());
    };
  }, []);

  return (
    <div className="rounded-2xl border border-gray-200 bg-white p-3 space-y-2">
      <div className="flex items-center justify-between">
        <p className="text-sm font-semibold text-gray-900">Camera scanner</p>
        <button type="button" onClick={onClose} className="flex items-center gap-1 text-xs font-medium text-gray-500">
          <X size={14} /> Close camera
        </button>
      </div>
      <div className="rounded-lg bg-gray-950 p-2">
        <div id={elementId.current} className="min-h-48 overflow-hidden rounded-md bg-black" />
      </div>
      <p className="text-xs text-gray-500">
        {cameraError ?? (ready ? 'Point the camera at a traveler QR code.' : 'Starting camera...')}
      </p>
    </div>
  );
}

export default function ActivityPage({
  activity,
  dayTitle,
  onBack,
  onCheckedIn,
}: {
  activity: StaffActivity;
  dayTitle: string;
  onBack: () => void;
  onCheckedIn: (activityId: string) => void;
}) {
  const [travelers, setTravelers] = useState<ActivityTraveler[] | null>(null);
  const [listError, setListError] = useState<string | null>(null);
  const [query, setQuery] = useState('');
  const [filter, setFilter] = useState<Filter>('all');
  const [cameraOpen, setCameraOpen] = useState(false);
  const [preview, setPreview] = useState<ActivityScanPreviewResponse | null>(null);
  const [result, setResult] = useState<ActivityScanResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const submittingRef = useRef(false);
  const pendingPayloadRef = useRef<string | null>(null);
  const recentPayloadsRef = useRef(new Map<string, number>());
  const feedbackRef = useRef<HTMLDivElement>(null);

  // Manual check-ins start from anywhere in the list: bring the confirmation into view.
  useEffect(() => {
    if (preview || result || error) feedbackRef.current?.scrollIntoView?.({ block: 'center', behavior: 'smooth' });
  }, [preview, result, error]);

  const loadTravelers = useCallback(async () => {
    try {
      const response = await getActivityTravelers(activity.id);
      setTravelers(response.travelers);
      setListError(null);
    } catch (e) {
      setListError(e instanceof Error ? e.message : 'Failed to load travelers');
      setTravelers(current => current ?? []);
    }
  }, [activity.id]);

  useEffect(() => { void loadTravelers(); }, [loadTravelers]);

  const previewScan = useCallback(async (payload: string, fromCamera: boolean) => {
    const trimmed = payload.trim();
    if (!trimmed || submittingRef.current) return;
    if (fromCamera) {
      // A camera keeps reading the same QR: ignore it while it is pending or just checked in.
      if (pendingPayloadRef.current === trimmed) return;
      const lastAt = recentPayloadsRef.current.get(trimmed);
      if (lastAt && Date.now() - lastAt < SAME_QR_COOLDOWN_MS) return;
    }

    submittingRef.current = true;
    setSubmitting(true);
    setError(null);
    setResult(null);
    setPreview(null);
    pendingPayloadRef.current = null;
    try {
      const response = await previewActivityTravelerScan(activity.id, trimmed);
      setPreview(response);
      if (response.status === 'ready_to_check_in') pendingPayloadRef.current = trimmed;
      else recentPayloadsRef.current.set(trimmed, Date.now());
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to scan traveler');
    } finally {
      submittingRef.current = false;
      setSubmitting(false);
    }
  }, [activity.id]);

  const cancelPending = () => {
    pendingPayloadRef.current = null;
    setPreview(null);
  };

  const confirmPending = async () => {
    const payload = pendingPayloadRef.current;
    if (!payload || submittingRef.current) return;
    submittingRef.current = true;
    setSubmitting(true);
    setError(null);
    try {
      const response = await scanActivityTraveler(activity.id, payload);
      setResult(response);
      setPreview(null);
      pendingPayloadRef.current = null;
      recentPayloadsRef.current.set(payload, Date.now());
      if (response.status === 'checked_in') {
        signalCheckedIn();
        onCheckedIn(activity.id);
      }
      void loadTravelers();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to confirm check-in');
    } finally {
      submittingRef.current = false;
      setSubmitting(false);
    }
  };

  const all = travelers ?? [];
  const counts = {
    all: all.length,
    not_arrived: all.filter(t => statusOf(t) === 'not_arrived').length,
    in_progress: all.filter(t => statusOf(t) === 'in_progress').length,
    done: all.filter(t => statusOf(t) === 'done').length,
  };
  const normalized = query.trim().toLowerCase();
  const visible = all.filter(t =>
    (filter === 'all' || statusOf(t) === filter)
    && (!normalized || t.name.toLowerCase().includes(normalized))
  );
  const filters: { id: Filter; label: string }[] = [
    { id: 'all', label: 'All' },
    { id: 'not_arrived', label: 'Not arrived' },
    { id: 'in_progress', label: 'In progress' },
    { id: 'done', label: 'Done' },
  ].filter(f => f.id !== 'in_progress' || activity.max_checkins > 1) as { id: Filter; label: string }[];

  const name = (r: { traveler_name?: string | null } | null) => r?.traveler_name || 'Traveler';

  return (
    <div className="px-4 py-4 pb-24 space-y-4">
      <div>
        <button
          type="button"
          onClick={onBack}
          aria-label="Back to itinerary"
          className="mb-3 flex items-center gap-1.5 text-sm font-medium text-emerald-700"
        >
          <ArrowLeft size={16} /> Itinerary
        </button>
        <p className="text-xs font-medium uppercase tracking-wide text-gray-400">{dayTitle}</p>
        <h2 className="text-xl font-bold text-gray-900">{activity.name}</h2>
        <div className="mt-1 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-gray-500">
          {activity.starts_at && (
            <span className="flex items-center gap-1"><Clock size={12} />{formatClock(activity.starts_at)}</span>
          )}
          <span>{activity.max_checkins} check-in{activity.max_checkins > 1 ? 's' : ''} per traveler</span>
          {activity.address && (
            <a
              href={`https://maps.google.com/?q=${encodeURIComponent(activity.address)}`}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1 text-blue-600"
            >
              <MapPin size={12} />{activity.address}
            </a>
          )}
        </div>
      </div>

      {!cameraOpen ? (
        <button
          type="button"
          onClick={() => setCameraOpen(true)}
          className="flex w-full items-center justify-center gap-2 rounded-xl bg-emerald-700 px-4 py-3 text-sm font-semibold text-white"
        >
          <Camera size={16} /> Scan with camera
        </button>
      ) : (
        <CameraScanner onScan={payload => void previewScan(payload, true)} onClose={() => setCameraOpen(false)} />
      )}

      <div ref={feedbackRef} aria-live="polite" className="space-y-2 scroll-mt-24">
        {submitting && !preview && (
          <p className="flex items-center gap-2 text-sm text-gray-500"><Loader2 size={14} className="animate-spin" /> Checking...</p>
        )}
        {preview?.status === 'ready_to_check_in' && (
          <div className="rounded-xl border border-emerald-200 bg-emerald-50 px-3 py-3 space-y-3">
            <div>
              <p className="text-sm font-semibold text-emerald-900">{name(preview)}</p>
              <p className="text-xs text-emerald-700">Ready for check-in {preview.scan_number} of {preview.max_checkins}</p>
            </div>
            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => void confirmPending()}
                disabled={submitting}
                className="flex items-center gap-1.5 rounded-lg bg-emerald-700 px-3 py-2 text-xs font-semibold text-white disabled:opacity-50"
              >
                {submitting ? <Loader2 size={13} className="animate-spin" /> : <Check size={13} />}
                Confirm check-in
              </button>
              <button
                type="button"
                onClick={cancelPending}
                disabled={submitting}
                className="rounded-lg border border-emerald-200 px-3 py-2 text-xs font-semibold text-emerald-700 disabled:opacity-50"
              >
                Cancel
              </button>
            </div>
          </div>
        )}
        {(preview?.status === 'already_checked_in' || result?.status === 'already_checked_in') && (() => {
          const info = preview ?? result;
          return (
            <div className="rounded-xl border border-amber-200 bg-amber-50 px-3 py-2">
              <p className="text-sm font-medium text-amber-800">
                {name(info)} already completed all {info?.max_checkins} check-in{(info?.max_checkins ?? 1) > 1 ? 's' : ''}.
              </p>
              {info?.scanned_by_name && <p className="text-xs text-amber-700">Last check-in by {info.scanned_by_name}</p>}
            </div>
          );
        })()}
        {(preview?.status === 'recently_checked_in' || result?.status === 'recently_checked_in') && (() => {
          const info = preview ?? result;
          return (
            <div className="rounded-xl border border-amber-200 bg-amber-50 px-3 py-2">
              <p className="text-sm font-medium text-amber-800">
                {name(info)} was just checked in (check-in {info?.scan_number} of {info?.max_checkins}).
              </p>
              <p className="text-xs text-amber-700">Next check-in available in {info?.retry_after_seconds} s.</p>
            </div>
          );
        })()}
        {result?.status === 'checked_in' && (
          <div className="flex items-center gap-2 rounded-xl border border-emerald-200 bg-emerald-50 px-3 py-2">
            <Check size={16} className="text-emerald-700" />
            <p className="text-sm font-medium text-emerald-800">
              {name(result)} — check-in {result.scan_number} of {result.max_checkins}
            </p>
          </div>
        )}
        {error && (
          <div className="rounded-xl border border-red-100 bg-red-50 px-3 py-2">
            <p className="text-sm font-medium text-red-700">{error}</p>
          </div>
        )}
      </div>

      <div className="rounded-2xl bg-white shadow-sm overflow-hidden">
        <div className="p-3 space-y-2 border-b border-gray-100">
          <div className="relative">
            <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
            <input
              type="search"
              value={query}
              onChange={e => setQuery(e.target.value)}
              placeholder="Search traveler"
              className="w-full rounded-xl border border-gray-200 bg-white py-2 pl-9 pr-3 text-sm outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500"
            />
          </div>
          <div className="flex flex-wrap gap-1.5">
            {filters.map(f => (
              <button
                key={f.id}
                type="button"
                onClick={() => setFilter(f.id)}
                className={`rounded-full px-3 py-1 text-xs font-semibold transition-colors ${
                  filter === f.id ? 'bg-emerald-700 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
              >
                {f.label} ({counts[f.id]})
              </button>
            ))}
          </div>
        </div>

        {travelers === null ? (
          <div className="flex justify-center py-6"><Loader2 size={18} className="animate-spin text-emerald-600" /></div>
        ) : listError && all.length === 0 ? (
          <p className="px-4 py-6 text-center text-sm text-red-500">{listError}</p>
        ) : visible.length === 0 ? (
          <p className="px-4 py-6 text-center text-sm text-gray-400">No travelers found.</p>
        ) : (
          <ul className="divide-y divide-gray-50">
            {visible.map(t => {
              const status = statusOf(t);
              return (
                <li key={t.id} className="flex items-center gap-3 px-4 py-3">
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-sm font-medium text-gray-800">{t.name}</p>
                    <div className="mt-0.5 flex flex-wrap items-center gap-x-2 gap-y-0.5 text-xs text-gray-500">
                      <span className={`rounded-full px-2 py-0.5 font-semibold ${STATUS_STYLE[status]}`}>{STATUS_LABEL[status]}</span>
                      <span>{t.checkin_count} of {t.max_checkins} check-ins</span>
                      {t.last_checked_in_at && <span>· last {formatClock(t.last_checked_in_at)}</span>}
                      {status === 'in_progress' && <span>· Next: check-in {t.checkin_count + 1} of {t.max_checkins}</span>}
                    </div>
                  </div>
                  <button
                    type="button"
                    aria-label={`Check in ${t.name}`}
                    disabled={status === 'done' || submitting}
                    onClick={() => void previewScan(t.qr_payload, false)}
                    className="shrink-0 rounded-lg border border-emerald-200 px-3 py-1.5 text-xs font-semibold text-emerald-700 disabled:border-gray-100 disabled:text-gray-300"
                  >
                    {status === 'done' ? 'Done' : 'Check in'}
                  </button>
                </li>
              );
            })}
          </ul>
        )}
      </div>

      {activity.staff_tasks.length > 0 && (
        <div className="rounded-2xl border border-emerald-100 bg-white overflow-hidden">
          <div className="px-3 py-2 bg-emerald-50 border-b border-emerald-100">
            <p className="text-xs font-semibold text-emerald-700 uppercase tracking-wide">My tasks</p>
          </div>
          <div className="divide-y divide-gray-100">
            {activity.staff_tasks.map(task => (
              <div key={task.id} className="px-3 py-2">
                <p className="text-sm font-medium text-gray-800">{task.title}</p>
                {task.description && <p className="text-xs text-gray-500 mt-0.5">{task.description}</p>}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
