import '../App.css';
import { Fragment, useCallback, useEffect, useRef, useState } from 'react';
import { Loader2 } from 'lucide-react';

import LoginScreen from '../features/auth/pages/LoginScreen';
import TripSelectorScreen from '../features/auth/pages/TripSelectorScreen';
import StaffScreen from '../features/staff/pages/StaffScreen';
import DevUserSwitcher from '../features/dev/DevUserSwitcher';
import { listTrips, type TripChoice } from '../features/auth/services/auth-api';

import { AuthProvider } from './providers/AuthProvider';
import { TripProvider } from './providers/TripProvider';
import { useAuth, type AuthUser } from './providers/auth-context';
import { StaffViewContext } from './providers/staff-view-context';
import { AvatarContext, loadStoredAvatar, persistAvatar } from './providers/avatar-context';
import { NotificationProvider } from './providers/notification-context';
import AppRouter from './router';

function initialTravelerViewRequested() {
  return new URLSearchParams(window.location.search).get('view') === 'traveler';
}

/**
 * Removes `?view=traveler` from the URL once it's been read into state.
 * Without this, the deep link would re-apply every time `TripApp` remounts —
 * including on a later in-app trip switch (Task 7 review fix round 1) —
 * incorrectly forcing a staff member back into traveler view on a brand new
 * trip. Left as a plain read in `initialTravelerViewRequested` (called from
 * `useState`'s lazy initializer, which must stay a pure read to behave the
 * same under React StrictMode's dev-only double-invoke) and done here
 * instead, from an effect that runs once after mount.
 */
function consumeTravelerViewDeepLink() {
  const params = new URLSearchParams(window.location.search);
  if (!params.has('view')) return;

  params.delete('view');
  const newSearch = params.toString();
  const newUrl = `${window.location.pathname}${newSearch ? `?${newSearch}` : ''}${window.location.hash}`;
  window.history.replaceState(window.history.state, '', newUrl);
}

type TripSwitcherState =
  | { status: 'loading' }
  | { status: 'error' }
  | { status: 'ready'; trips: TripChoice[] };

/**
 * The Task 7 in-app "Trocar de viagem" overlay. Rendered as a sibling of the
 * tripId-keyed subtree below (never nested inside it), so opening/closing it
 * never changes that subtree's key — cancel returns to the exact previous
 * session untouched, without remounting the app underneath.
 *
 * Per spec, opening the switcher always refreshes memberships (`GET
 * /auth/trips`) rather than reusing a possibly-stale list; a failed refresh
 * shows a retryable error, and cancelling from either state leaves the
 * current session alone.
 */
// z-[100]: above every fixed app-chrome element (AppHeader/TopBar are
// z-[60], BottomNav/the staff bottom nav are z-50) so the overlay actually
// paints on top of them instead of underneath (Task 7 review fix round 1).
const OVERLAY_CLASS = 'fixed inset-0 z-[100] overflow-y-auto';

function TripSwitcherOverlay({
  token,
  activeTripId,
  onCancel,
  initialTrips,
  onNoTrips,
}: {
  token: string;
  activeTripId: string | null;
  onCancel: () => void;
  initialTrips: TripChoice[] | null;
  onNoTrips: () => void;
}) {
  const [state, setState] = useState<TripSwitcherState>(() =>
    initialTrips ? { status: 'ready', trips: initialTrips } : { status: 'loading' }
  );
  const dialogRef = useRef<HTMLDivElement>(null);
  const titleRef = useRef<HTMLHeadingElement>(null);
  const returnFocusRef = useRef<HTMLElement | null>(null);
  // Guards against an in-flight `listTrips` call (e.g. from a stale retry,
  // or one already superseded by a newer one) resolving after a newer
  // request or an unmount — without this, a slow first response landing
  // after a fast retry's response could silently overwrite fresher state.
  const requestIdRef = useRef(0);

  const load = useCallback(() => {
    const requestId = ++requestIdRef.current;
    setState({ status: 'loading' });
    listTrips(token)
      .then(res => {
        if (requestIdRef.current !== requestId) return;
        if (res.trips.length === 0) {
          onNoTrips();
          return;
        }
        if (res.trips.length === 1) {
          onCancel();
          return;
        }
        setState({ status: 'ready', trips: res.trips });
      })
      .catch(() => {
        if (requestIdRef.current !== requestId) return;
        setState({ status: 'error' });
      });
  }, [onCancel, onNoTrips, token]);

  useEffect(() => {
    if (!initialTrips) load();
    return () => {
      requestIdRef.current += 1;
    };
  }, [initialTrips, load]);

  useEffect(() => {
    returnFocusRef.current = document.activeElement instanceof HTMLElement
      ? document.activeElement
      : null;
    titleRef.current?.focus();

    return () => {
      const returnTarget = returnFocusRef.current;
      window.setTimeout(() => {
        if (returnTarget?.isConnected) {
          returnTarget.focus();
        } else {
          document.querySelector<HTMLElement>('[data-app-focus-root]')?.focus();
        }
      }, 0);
    };
  }, []);

  const handleDialogKeyDown = (event: React.KeyboardEvent<HTMLDivElement>) => {
    if (event.key === 'Escape') {
      event.preventDefault();
      onCancel();
      return;
    }
    if (event.key !== 'Tab') return;

    const focusable = Array.from(dialogRef.current?.querySelectorAll<HTMLElement>(
      'button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'
    ) ?? []).filter(element => !element.hasAttribute('hidden'));
    if (focusable.length === 0) {
      event.preventDefault();
      titleRef.current?.focus();
      return;
    }

    const first = focusable[0];
    const last = focusable[focusable.length - 1];
    if (event.shiftKey && (document.activeElement === first || document.activeElement === titleRef.current)) {
      event.preventDefault();
      last.focus();
    } else if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault();
      first.focus();
    }
  };

  let content: React.ReactNode;

  if (state.status === 'loading') {
    content = (
      <div className={`${OVERLAY_CLASS} flex flex-col items-center justify-center gap-4 bg-emerald-700`}>
        <Loader2
          size={32}
          role="status"
          aria-label="Carregando viagens"
          className="animate-spin text-white"
        />
        <button
          type="button"
          onClick={onCancel}
          className="rounded-xl border border-white/40 px-4 py-2 text-sm font-semibold text-white"
        >
          Cancelar
        </button>
      </div>
    );
  } else if (state.status === 'error') {
    content = (
      <div className={`${OVERLAY_CLASS} flex flex-col items-center justify-center gap-4 bg-emerald-700 px-6 text-center`}>
        <p className="text-sm text-white">Não foi possível carregar suas viagens.</p>
        <div className="flex gap-3">
          <button
            type="button"
            onClick={load}
            className="rounded-xl bg-white px-4 py-2 text-sm font-semibold text-emerald-700"
          >
            Tentar novamente
          </button>
          <button
            type="button"
            onClick={onCancel}
            className="rounded-xl border border-white/40 px-4 py-2 text-sm font-semibold text-white"
          >
            Cancelar
          </button>
        </div>
      </div>
    );
  } else {
    content = (
      <div className={OVERLAY_CLASS}>
        <TripSelectorScreen trips={state.trips} token={token} activeTripId={activeTripId} onCancel={onCancel} />
      </div>
    );
  }

  return (
    <div
      ref={dialogRef}
      role="dialog"
      aria-modal="true"
      aria-labelledby="trip-switcher-title"
      onKeyDown={handleDialogKeyDown}
    >
      <h2 id="trip-switcher-title" ref={titleRef} tabIndex={-1} className="sr-only">
        Trocar de viagem
      </h2>
      {content}
    </div>
  );
}

/**
 * The staff/traveler app for the current `tripId`. Rendered inside the
 * tripId-keyed `Fragment` in `AppContent`, so switching trips remounts it
 * fresh — including `viewingAsTraveler`: owning that state here (rather than
 * above the key, where it used to live) means a staff member who previewed
 * the traveler view and then switches to a different staff-role trip lands
 * back in the staff view instead of carrying the stale preview over (Task 6
 * review carry-over fix).
 */
function TripApp({
  user,
  avatarUrl,
  onSetAvatarUrl,
}: {
  user: AuthUser | null;
  avatarUrl: string | null;
  onSetAvatarUrl: (url: string | null) => void;
}) {
  const [viewingAsTraveler, setViewingAsTraveler] = useState(() => initialTravelerViewRequested());

  useEffect(() => {
    consumeTravelerViewDeepLink();
  }, []);

  if (user?.role === 'staff' && !viewingAsTraveler) {
    return <StaffScreen onSwitchToTravelerView={() => setViewingAsTraveler(true)} />;
  }

  return (
    <TripProvider>
      <StaffViewContext.Provider value={{
        onSwitchToStaffView: user?.role === 'staff' ? () => setViewingAsTraveler(false) : null,
      }}>
        <AvatarContext.Provider value={{ avatarUrl, setAvatarUrl: onSetAvatarUrl }}>
          <NotificationProvider>
            <AppRouter />
          </NotificationProvider>
        </AvatarContext.Provider>
      </StaffViewContext.Provider>
    </TripProvider>
  );
}

function AppContent() {
  const {
    isLoggedIn, user, pendingSelection, isTripSwitcherOpen, tripSwitcherTrips,
    hasNoTrips, cancelTripSwitcher, enterNoTrips, clearNoTrips,
  } = useAuth();
  const userId = user?.userId ?? '';
  // `inert` isn't in this project's @types/react (only its `experimental`
  // typings), so it's set imperatively via the DOM property — which IS
  // typed on `HTMLElement` by TypeScript's own DOM lib — rather than as a
  // JSX prop.
  const appTreeRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (appTreeRef.current) {
      appTreeRef.current.inert = isTripSwitcherOpen;
    }
  }, [isTripSwitcherOpen]);

  const [avatarUrl, setAvatarUrl] = useState<string | null>(() =>
    userId ? loadStoredAvatar(userId) : null
  );

  useEffect(() => {
    if (userId) {
      setAvatarUrl(loadStoredAvatar(userId));
    } else {
      setAvatarUrl(null);
    }
  }, [userId]);

  const handleSetAvatarUrl = (url: string | null) => {
    if (userId) persistAvatar(userId, url);
    setAvatarUrl(url);
  };

  // Gate order: OTP login (phone/code, plus the no-trip explanatory state,
  // both handled locally inside LoginScreen) → trip selector (a pending
  // selection from `selection_required`, which never coexists with
  // isLoggedIn) → staff/traveler app.
  if (hasNoTrips) {
    return (
      <div className="min-h-dvh bg-emerald-700 flex items-center justify-center px-4">
        <div className="w-full max-w-sm rounded-3xl bg-white p-6 text-center shadow-2xl">
          <h1 className="text-lg font-bold text-gray-800">Sem viagens disponíveis</h1>
          <p className="mt-2 text-sm text-gray-500">Você não tem viagens atuais ou futuras</p>
          <button type="button" onClick={clearNoTrips} className="mt-6 w-full rounded-xl bg-emerald-600 py-3 text-sm font-semibold text-white">
            Sair
          </button>
        </div>
      </div>
    );
  }

  if (pendingSelection) {
    return (
      <TripSelectorScreen
        trips={pendingSelection.trips}
        token={pendingSelection.selectionToken}
      />
    );
  }

  if (!isLoggedIn) {
    return <LoginScreen />;
  }

  return (
    <>
      {isTripSwitcherOpen && user && (
        <TripSwitcherOverlay
          token={user.token}
          activeTripId={user.tripId}
          initialTrips={tripSwitcherTrips}
          onCancel={cancelTripSwitcher}
          onNoTrips={enterNoTrips}
        />
      )}
      {/* Keyed by tripId so switching trips (Task 7) remounts this entire
          subtree — TripProvider's fetch, StaffScreen's own fetch, and any
          cached trip-scoped state — instead of leaving stale data from the
          previous trip mounted. The switcher overlay above is a sibling, not
          a child, of this Fragment: opening/closing it never touches the
          key, so cancelling it never remounts the app underneath.

          The wrapping div's `inert`/`aria-hidden` (while the overlay is
          open) makes the app underneath non-interactive and unfocusable
          regardless of the fixed-position app chrome (headers, bottom
          navs) that would otherwise still sit on top by z-index and stay
          clickable/tabbable through the overlay (Task 7 review fix round
          1). */}
      <div ref={appTreeRef} aria-hidden={isTripSwitcherOpen || undefined} data-app-focus-root tabIndex={-1}>
        <Fragment key={user?.tripId ?? 'no-trip'}>
          <TripApp user={user} avatarUrl={avatarUrl} onSetAvatarUrl={handleSetAvatarUrl} />
        </Fragment>
        <DevUserSwitcher />
      </div>
    </>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}
