import { createContext, useContext } from 'react';

import type { TripChoice } from '../../features/auth/services/auth-api';

export type { TripChoice };
export type UserRole = 'traveler' | 'staff';

export interface AuthUser {
  userId: string;
  phone: string;
  name: string | null;
  token: string;
  /** The person's role on `activeTrip` (derived per-trip, not a global role). */
  role: UserRole;
  /**
   * The trip this session's token is scoped to.
   *
   * `null` only for sessions created through the back-compat `login()` action
   * (dev auto-login, `DevUserSwitcher`), which predates trip selection. Any
   * stored session missing this field entirely (no key at all) is legacy data
   * from before multi-trip login shipped and is discarded on load — see
   * `getStoredUser` in `AuthProvider.tsx`.
   */
  tripId: string | null;
  /** Full trip details for `tripId`, or `null` alongside a `null` `tripId`. */
  activeTrip: TripChoice | null;
}

/**
 * Holds the identity + trips returned by `verify-otp` with `status:
 * "selection_required"`, while the person has not yet picked a trip and is
 * NOT logged in. Consumed by the Task 6 trip selector screen.
 */
export interface PendingTripSelection {
  userId: string;
  phone: string;
  name: string | null;
  selectionToken: string;
  trips: TripChoice[];
}

export interface AuthContextType {
  user: AuthUser | null;
  isLoggedIn: boolean;
  /** Set while `verify-otp` returned `selection_required`; `null` otherwise. */
  pendingSelection: PendingTripSelection | null;
  /** Whether the in-app "switch trip" UI (Task 7) is open. */
  isTripSwitcherOpen: boolean;
  tripSwitcherTrips: TripChoice[] | null;
  hasNoTrips: boolean;

  /**
   * Back-compat session setter used by callers that don't yet carry a trip
   * choice (dev auto-login, `DevUserSwitcher`). Stores `tripId`/`activeTrip`
   * as `null`. Prefer `completeTripSelection` for any real `verify-otp` /
   * `select-trip` result.
   */
  login: (userId: string, phone: string, name: string | null, token: string, role: UserRole) => void;

  /**
   * Records a `selection_required` result so a trip selector can render it.
   * Does not log the person in.
   */
  beginTripSelection: (selection: PendingTripSelection) => void;

  /**
   * Atomically (re)establishes the trip-scoped session — used both for the
   * first trip choice after OTP and for switching trips in-app later (Task
   * 7): the previous session (if any) and any pending selection are replaced
   * in one update, never left partially applied. `role` is not a separate
   * parameter: it is always `activeTrip.role`, so a caller can't pass a role
   * that disagrees with the chosen trip. Pass a `trip_selected`/`select-trip`
   * result's fields directly.
   */
  completeTripSelection: (
    userId: string,
    phone: string,
    name: string | null,
    token: string,
    activeTrip: TripChoice
  ) => void;

  /** Opens the in-app trip switcher without touching the current session. */
  openTripSwitcher: () => void;
  /** Closes the in-app trip switcher, leaving the current session untouched. */
  cancelTripSwitcher: () => void;
  enterNoTrips: () => void;
  clearNoTrips: () => void;

  logout: () => void;
}

export const AuthContext = createContext<AuthContextType>({
  user: null,
  isLoggedIn: false,
  pendingSelection: null,
  isTripSwitcherOpen: false,
  tripSwitcherTrips: null,
  hasNoTrips: false,
  login: () => {},
  beginTripSelection: () => {},
  completeTripSelection: () => {},
  openTripSwitcher: () => {},
  cancelTripSwitcher: () => {},
  enterNoTrips: () => {},
  clearNoTrips: () => {},
  logout: () => {},
});

export function useAuth() {
  return useContext(AuthContext);
}
