import '../App.css';
import { Fragment, useEffect, useState } from 'react';

import LoginScreen from '../features/auth/pages/LoginScreen';
import TripSelectorScreen from '../features/auth/pages/TripSelectorScreen';
import StaffScreen from '../features/staff/pages/StaffScreen';
import DevUserSwitcher from '../features/dev/DevUserSwitcher';

import { AuthProvider } from './providers/AuthProvider';
import { TripProvider } from './providers/TripProvider';
import { useAuth } from './providers/auth-context';
import { StaffViewContext } from './providers/staff-view-context';
import { AvatarContext, loadStoredAvatar, persistAvatar } from './providers/avatar-context';
import { NotificationProvider } from './providers/notification-context';
import AppRouter from './router';

function initialTravelerViewRequested() {
  return new URLSearchParams(window.location.search).get('view') === 'traveler';
}

function AppContent() {
  const { isLoggedIn, user, pendingSelection } = useAuth();
  const [viewingAsTraveler, setViewingAsTraveler] = useState(() => initialTravelerViewRequested());
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
    // Keyed by tripId so switching trips (Task 7) remounts this entire
    // subtree — TripProvider's fetch, StaffScreen's own fetch, and any
    // cached trip-scoped state — instead of leaving stale data from the
    // previous trip mounted.
    <Fragment key={user?.tripId ?? 'no-trip'}>
      {user?.role === 'staff' && !viewingAsTraveler ? (
        <StaffScreen onSwitchToTravelerView={() => setViewingAsTraveler(true)} />
      ) : (
        <TripProvider>
          <StaffViewContext.Provider value={{
            onSwitchToStaffView: user?.role === 'staff' ? () => setViewingAsTraveler(false) : null,
          }}>
            <AvatarContext.Provider value={{ avatarUrl, setAvatarUrl: handleSetAvatarUrl }}>
              <NotificationProvider>
                <AppRouter />
              </NotificationProvider>
            </AvatarContext.Provider>
          </StaffViewContext.Provider>
        </TripProvider>
      )}
    </Fragment>
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
