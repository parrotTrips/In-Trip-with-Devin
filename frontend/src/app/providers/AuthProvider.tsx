import { useEffect, useState, type ReactNode } from 'react';
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

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(() => getStoredUser() ?? getDevAutoLoginUser());
  const [pendingSelection, setPendingSelection] = useState<PendingTripSelection | null>(null);
  const [isTripSwitcherOpen, setIsTripSwitcherOpen] = useState(false);

  useEffect(() => {
    if (user) {
      localStorage.setItem('parrot_user', JSON.stringify(user));
      return;
    }
    localStorage.removeItem('parrot_user');
  }, [user]);

  const establishSession = (newUser: AuthUser) => {
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
    role: UserRole,
    activeTrip: TripChoice
  ) => {
    establishSession({ userId, phone, name, token, role, tripId: activeTrip.trip_id, activeTrip });
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
