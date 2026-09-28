import '../App.css';
import { Fragment, useCallback, useEffect, useState } from 'react';
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
function TripSwitcherOverlay({
  token,
  activeTripId,
  onCancel,
}: {
  token: string;
  activeTripId: string | null;
  onCancel: () => void;
}) {
  const [state, setState] = useState<TripSwitcherState>({ status: 'loading' });

  const load = useCallback(() => {
    setState({ status: 'loading' });
    listTrips(token)
      .then(res => setState({ status: 'ready', trips: res.trips }))
      .catch(() => setState({ status: 'error' }));
  }, [token]);

  useEffect(() => {
    load();
  }, [load]);

  if (state.status === 'loading') {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-emerald-700">
        <Loader2
          size={32}
          role="status"
          aria-label="Carregando viagens"
          className="animate-spin text-white"
        />
      </div>
    );
  }

  if (state.status === 'error') {
    return (
      <div className="fixed inset-0 z-50 flex flex-col items-center justify-center gap-4 bg-emerald-700 px-6 text-center">
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
  }

  return (
    <div className="fixed inset-0 z-50">
      <TripSelectorScreen trips={state.trips} token={token} activeTripId={activeTripId} onCancel={onCancel} />
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
  const { isLoggedIn, user, pendingSelection, isTripSwitcherOpen, cancelTripSwitcher } = useAuth();
  const userId = user?.userId ?? '';
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
        <TripSwitcherOverlay token={user.token} activeTripId={user.tripId} onCancel={cancelTripSwitcher} />
      )}
      {/* Keyed by tripId so switching trips (Task 7) remounts this entire
          subtree — TripProvider's fetch, StaffScreen's own fetch, and any
          cached trip-scoped state — instead of leaving stale data from the
          previous trip mounted. The switcher overlay above is a sibling, not
          a child, of this Fragment: opening/closing it never touches the
          key, so cancelling it never remounts the app underneath. */}
      <Fragment key={user?.tripId ?? 'no-trip'}>
        <TripApp user={user} avatarUrl={avatarUrl} onSetAvatarUrl={handleSetAvatarUrl} />
      </Fragment>
    </>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <AppContent />
      <DevUserSwitcher />
    </AuthProvider>
  );
}
