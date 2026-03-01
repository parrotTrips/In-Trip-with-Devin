const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Request failed');
  }
  return res.json();
}

// ── Auth ─────────────────────────────────────────────────────────

export async function requestOTP(phone: string) {
  return request<{ message: string; debug_code?: string }>('/auth/request-otp', {
    method: 'POST',
    body: JSON.stringify({ phone }),
  });
}

export async function verifyOTP(phone: string, code: string) {
  return request<{ user_id: number; phone: string; name: string | null; message: string }>(
    '/auth/verify-otp',
    { method: 'POST', body: JSON.stringify({ phone, code }) }
  );
}

// ── User ─────────────────────────────────────────────────────────

export async function getUser(userId: number) {
  return request<{ id: number; phone: string; name: string | null }>(`/users/${userId}`);
}

export async function updateUser(userId: number, name: string) {
  return request<{ message: string }>(`/users/${userId}`, {
    method: 'PUT',
    body: JSON.stringify({ name }),
  });
}

// ── Checklist ────────────────────────────────────────────────────

export async function updateChecklistItem(
  userId: number,
  tripId: string,
  phaseId: string,
  itemId: string,
  completed: boolean
) {
  return request<{ message: string }>(`/checklist/update?user_id=${userId}`, {
    method: 'POST',
    body: JSON.stringify({ trip_id: tripId, phase_id: phaseId, item_id: itemId, completed }),
  });
}

export async function getChecklistProgress(tripId: string, userId: number) {
  return request<{
    trip_id: string;
    user_id: number;
    progress: Record<string, Record<string, boolean>>;
  }>(`/checklist/${tripId}/${userId}`);
}

// ── Phase Completion ─────────────────────────────────────────────

export async function updatePhaseCompletion(
  userId: number,
  tripId: string,
  phaseId: string,
  completed: boolean
) {
  return request<{ message: string }>(`/phases/complete?user_id=${userId}`, {
    method: 'POST',
    body: JSON.stringify({ trip_id: tripId, phase_id: phaseId, completed }),
  });
}

export async function getPhaseCompletions(tripId: string, userId: number) {
  return request<{
    trip_id: string;
    user_id: number;
    completions: Record<string, boolean>;
  }>(`/phases/${tripId}/${userId}`);
}

// ── Comments ─────────────────────────────────────────────────────

export async function addComment(
  userId: number,
  tripId: string,
  phaseId: string,
  text: string,
  isPrivate = false
) {
  return request<{ message: string }>(`/comments?user_id=${userId}`, {
    method: 'POST',
    body: JSON.stringify({ trip_id: tripId, phase_id: phaseId, text, is_private: isPrivate }),
  });
}

export async function getComments(tripId: string, phaseId: string) {
  return request<{
    trip_id: string;
    phase_id: string;
    comments: Array<{
      id: number;
      user_id: number;
      user_name: string;
      text: string;
      created_at: string;
      is_private: boolean;
    }>;
  }>(`/comments/${tripId}/${phaseId}`);
}

// ── Profile ─────────────────────────────────────────────────────

export interface ProfileData {
  preferred_name: string | null;
  email: string | null;
  dob: string | null;
  gender: string | null;
  transfer_platform: string | null;
  package_option: string | null;
  num_people: number | null;
  usd_amount: number | null;
  proof_of_transfer: string | null;
  dietary_restrictions_yn: string | null;
  dietary_restrictions_desc: string | null;
  seasickness_yn: string | null;
  first_name_passport: string | null;
  last_name_passport: string | null;
  passport_country: string | null;
  passport_number: string | null;
  passport_issue_date: string | null;
  passport_expiration_date: string | null;
  plus_one_yn: string | null;
  plus_one_name: string | null;
  plus_one_email: string | null;
  intl_flights_help_yn: string | null;
  intl_flights_help_details: string | null;
  travel_insurance_help_yn: string | null;
  unforgettable_trip_details: string | null;
  receive_addon_updates: string | null;
  esim_qr_image: string | null;
  roommate_user_id: number | null;
  arrival_date: string | null;
  arrival_time: string | null;
  arrival_flight: string | null;
  departure_date: string | null;
  departure_time: string | null;
  departure_flight: string | null;
  service_agreement_url: string | null;
}

export interface ProfileResponse {
  user_id: number;
  phone: string;
  name: string | null;
  profile: ProfileData | null;
  roommate: { id: number; name: string | null; phone: string } | null;
}

export interface TravelerInfo {
  id: number;
  name: string | null;
  phone: string;
}

export async function getProfile(userId: number) {
  return request<ProfileResponse>(`/profile/${userId}`);
}

export async function updateProfile(userId: number, data: Partial<ProfileData>) {
  return request<{ message: string }>(`/profile/${userId}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  });
}

export async function getTripTravelers(tripId: string) {
  return request<{ trip_id: string; travelers: TravelerInfo[] }>(`/trip/${tripId}/travelers`);
}

// ── Notifications ──────────────────────────────────────────────

export interface Notification {
  id: number;
  title: string;
  body: string;
  type: string;
  link: string | null;
  read: boolean;
  created_at: string;
}

export interface NotificationsResponse {
  notifications: Notification[];
  unread_count: number;
}

export async function getNotifications(userId: number, unreadOnly = false) {
  const params = unreadOnly ? '?unread_only=true' : '';
  return request<NotificationsResponse>(`/notifications/${userId}${params}`);
}

export async function getUnreadCount(userId: number) {
  return request<{ unread_count: number }>(`/notifications/${userId}/count`);
}

export async function markNotificationRead(notificationId: number) {
  return request<{ message: string }>(`/notifications/${notificationId}/read`, {
    method: 'PUT',
  });
}

export async function markAllNotificationsRead(userId: number) {
  return request<{ message: string }>(`/notifications/${userId}/read-all`, {
    method: 'PUT',
  });
}
