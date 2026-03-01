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
