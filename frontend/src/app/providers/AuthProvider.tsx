import { useState, type ReactNode } from 'react';
import * as Sentry from '@sentry/react';
import posthog from 'posthog-js';

import type { TripChoice } from '../../features/auth/services/auth-api';
import {
  AuthContext,
  type AuthUser,
  type PendingTripSelection,
  type UserRole,
} from './auth-context';

function getStoredUser(): AuthUser | null {
  try {
    const stored = localStorage.getItem('parrot_user');
    if (!stored) return null;

    const parsed = JSON.parse(stored) as Partial<AuthUser>;
    if (parsed.tripId === undefined) {
      // Predates trip-scoped sessions (no `tripId` key at all): the backend
      // no longer honors this token shape, so drop it and force a fresh login
      // rather than trusting stale/invalid data.
      localStorage.removeItem('parrot_user');
      return null;
    }

    return parsed as AuthUser;
  } catch {
    return null;
  }
}

function getDevAutoLoginUser(): AuthUser | null {
  if (!import.meta.env.DEV || import.meta.env.VITE_DEV_AUTO_LOGIN !== 'true') {
    return null;
  }

  const userId = import.meta.env.VITE_DEV_USER_ID ?? '';
  const role = (import.meta.env.VITE_DEV_USER_ROLE ?? 'traveler') as UserRole;

  return {
    userId,
    phone: import.meta.env.VITE_DEV_USER_PHONE ?? '+15550000001',
    name: import.meta.env.VITE_DEV_USER_NAME ?? 'Dev Traveler',
    token: import.meta.env.VITE_DEV_TOKEN ?? '',
    role,
    tripId: null,
    activeTrip: null,
  };
}

function identify(newUser: AuthUser) {
  posthog.identify(newUser.userId, {
    telefone: newUser.phone,
    nome: newUser.name,
    papel: newUser.role,
  });
  Sentry.setUser({ id: newUser.userId, username: newUser.name ?? newUser.phone });
}

function getInitialUser(): AuthUser | null {
  const stored = getStoredUser();
  if (stored) return stored;

  const devUser = getDevAutoLoginUser();
  if (devUser) {
    // Persist synchronously during the lazy initializer (i.e. before React's
    // first commit, let alone any effect) so a child mounted once
    // `isLoggedIn` is true never races the API client's localStorage-backed
    // getToken() — same reasoning as establishSession below.
    localStorage.setItem('parrot_user', JSON.stringify(devUser));
  }
  return devUser;
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(getInitialUser);
  const [pendingSelection, setPendingSelection] = useState<PendingTripSelection | null>(null);
  const [isTripSwitcherOpen, setIsTripSwitcherOpen] = useState(false);

  const establishSession = (newUser: AuthUser) => {
    // Persist synchronously, before setUser, and never from a useEffect:
    // React commits child effects before a parent's, so any child mounted
    // once isLoggedIn flips true (e.g. TripProvider fetching /me/trip) would
    // otherwise run before an AuthProvider effect had persisted the token,
    // reading a missing or stale value from localStorage via the API
    // client's getToken(). Writing here — inside the same event handler that
    // calls setUser — guarantees the token is already there before React
    // even starts rendering, exactly like logout()'s synchronous removeItem.
    localStorage.setItem('parrot_user', JSON.stringify(newUser));
    // One setState call per piece of state: no intermediate render can see a
    // half-replaced session (e.g. new tripId with the old token), whether
    // this is the first login or an in-app trip switch.
    setUser(newUser);
    setPendingSelection(null);
    setIsTripSwitcherOpen(false);
    identify(newUser);
  };

  const login = (userId: string, phone: string, name: string | null, token: string, role: UserRole) => {
    establishSession({ userId, phone, name, token, role, tripId: null, activeTrip: null });
  };

  const beginTripSelection = (selection: PendingTripSelection) => {
    setPendingSelection(selection);
  };

  const completeTripSelection = (
    userId: string,
    phone: string,
    name: string | null,
    token: string,
    activeTrip: TripChoice
  ) => {
    // Role is derived from activeTrip.role rather than accepted separately,
    // so a caller can't pass a role that disagrees with the chosen trip.
    establishSession({ userId, phone, name, token, role: activeTrip.role, tripId: activeTrip.trip_id, activeTrip });
  };

  const openTripSwitcher = () => setIsTripSwitcherOpen(true);
  const cancelTripSwitcher = () => setIsTripSwitcherOpen(false);

  const logout = () => {
    localStorage.removeItem('parrot_user');
    setUser(null);
    setPendingSelection(null);
    setIsTripSwitcherOpen(false);
    posthog.reset();
    Sentry.setUser(null);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isLoggedIn: !!user,
        pendingSelection,
        isTripSwitcherOpen,
        login,
        beginTripSelection,
        completeTripSelection,
        openTripSwitcher,
        cancelTripSwitcher,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}
