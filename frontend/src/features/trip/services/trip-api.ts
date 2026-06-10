import { request } from '../../../shared/api/client';

export interface TripInfo {
  wetravel_trip_uuid: string;
  title: string;
  destination: string;
  start_date: string;
  end_date: string;
  url: string | null;
  service_agreement_url: string | null;
  trip_mode: 'pre-trip' | 'in-trip';
}

export interface ChecklistItem {
  id: string;
  label: string;
  sort_order: number;
  is_required: boolean;
}

export interface PhaseLink {
  id: string;
  label: string;
  url: string;
  sort_order: number;
}

export interface Activity {
  id: string;
  name: string;
  activity_type: 'included' | 'optional' | 'suggested' | 'logistics';
  starts_at: string | null;
  duration_minutes: number | null;
  short_description: string;
  practical_info: string | null;
  amount_brl: number | null;
  sort_order: number;
}

export interface TripPhase {
  id: string;
  phase_type: 'pre-trip' | 'in-trip';
  title: string;
  subtitle: string | null;
  icon: string | null;
  short_description: string;
  detailed_description: string | null;
  sort_order: number;
  starts_at: string | null;
  is_locked_by_default: boolean;
  checklist_items: ChecklistItem[];
  links: PhaseLink[];
}

export interface TripPhaseDetail extends TripPhase {
  activities: Activity[];
}

export interface TripTraveler {
  id: string;
  name: string | null;
  phone: string;
  current_phase_id: string | null;
}

export async function getMyTrip() {
  return request<{ trip: TripInfo | null }>('/me/trip');
}

export async function getMyTripPhases() {
  return request<{ wetravel_trip_uuid: string; phases: TripPhase[] }>('/me/trip/phases');
}

export async function getMyTripPhaseDetail(phaseId: string) {
  return request<TripPhaseDetail>(`/me/trip/phases/${phaseId}`);
}

export async function getMyTripTravelers() {
  return request<{ travelers: TripTraveler[] }>('/me/trip/travelers');
}

export async function updateChecklistItem(
  userId: string,
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

export async function getChecklistProgress(tripId: string, userId: string) {
  return request<{
    trip_id: string;
    user_id: string;
    progress: Record<string, Record<string, boolean>>;
  }>(`/checklist/${tripId}/${userId}`);
}

export async function updatePhaseCompletion(
  userId: string,
  tripId: string,
  phaseId: string,
  completed: boolean
) {
  return request<{ message: string }>(`/phases/complete?user_id=${userId}`, {
    method: 'POST',
    body: JSON.stringify({ trip_id: tripId, phase_id: phaseId, completed }),
  });
}

export async function getPhaseCompletions(tripId: string, userId: string) {
  return request<{
    trip_id: string;
    user_id: string;
    completions: Record<string, boolean>;
  }>(`/phases/${tripId}/${userId}`);
}
