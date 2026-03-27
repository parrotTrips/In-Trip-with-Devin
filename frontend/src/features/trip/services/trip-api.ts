import { request } from '../../../shared/api/client';

export interface TripComment {
  id: number;
  user_id: number;
  user_name: string;
  text: string;
  created_at: string;
  is_private: boolean;
}

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
    comments: TripComment[];
  }>(`/comments/${tripId}/${phaseId}`);
}
