import { request } from '../../../shared/api/client';

/** A trip a person may enter, as resolved by the backend's eligible-trip lookup. */
export interface TripChoice {
  trip_id: string;
  title: string;
  destination: string | null;
  start_date: string | null;
  end_date: string | null;
  role: 'traveler' | 'staff';
  is_current: boolean;
}

/**
 * The full set of outcomes `POST /auth/verify-otp` can return.
 *
 * - `no_trips`: the person has no current/future trip membership.
 * - `selection_required`: more than one eligible trip; `selection_token` must be
 *   exchanged via `selectTrip`/`POST /auth/select-trip` for a real session.
 * - `trip_selected`: exactly one eligible trip; a trip-scoped session token is
 *   already issued.
 * - `admin_authenticated`: an admin account. This app has no admin experience —
 *   the token is only valid on the separate `/console` app (see `console/`).
 *   Kept here so callers can match on `status` instead of assuming a shape.
 */
export type VerifyOTPResult =
  | { status: 'no_trips'; user_id: string; phone: string; name: string | null; message: string }
  | {
      status: 'selection_required';
      user_id: string;
      phone: string;
      name: string | null;
      message: string;
      selection_token: string;
      trips: TripChoice[];
    }
  | {
      status: 'trip_selected';
      user_id: string;
      phone: string;
      name: string | null;
      role: 'traveler' | 'staff';
      message: string;
      access_token: string;
      active_trip: TripChoice;
    }
  | {
      status: 'admin_authenticated';
      user_id: string;
      phone: string;
      name: string | null;
      role: 'admin';
      message: string;
      access_token: string;
    };

export async function requestOTP(phone: string) {
  return request<{ message: string; debug_code?: string }>('/auth/request-otp', {
    method: 'POST',
    body: JSON.stringify({ phone }),
  });
}

export async function verifyOTP(phone: string, code: string) {
  return request<VerifyOTPResult>('/auth/verify-otp', {
    method: 'POST',
    body: JSON.stringify({ phone, code }),
  });
}

/** Lists the eligible trips for the token's owner. Accepts a selection or session token. */
export async function listTrips(token: string) {
  return request<{ trips: TripChoice[] }>('/auth/trips', {
    method: 'GET',
    headers: { Authorization: `Bearer ${token}` },
  });
}

/**
 * Exchanges a selection or session token for a scoped session on `tripId`.
 * Returns the same shape as a `trip_selected` verify-otp result.
 */
export async function selectTrip(token: string, tripId: string) {
  return request<Extract<VerifyOTPResult, { status: 'trip_selected' }>>('/auth/select-trip', {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
    body: JSON.stringify({ trip_id: tripId }),
  });
}
