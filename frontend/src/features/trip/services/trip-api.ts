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

export interface TravelerQrCode {
  trip_uuid: string;
  trip_traveler_id: string;
  qr_payload: string;
}

export interface Announcement {
  id: string;
  title: string;
  body: string;
  sent_by: string;
  created_at: string;
  is_read: boolean;
}

export interface TeamMember {
  id: string;
  name: string;
  function: string | null;
  phone: string | null;
  photo_url: string | null;
  bio: string | null;
}

export async function getMyTrip() {
  return request<{ trip: TripInfo | null }>('/me/trip');
}

export async function getMyTripPhases() {
  return request<{ wetravel_trip_uuid: string; phases: TripPhase[]; ideal_pace_phase_id: string | null }>('/me/trip/phases');
}

export async function getMyTripPhaseDetail(phaseId: string) {
  return request<TripPhaseDetail>(`/me/trip/phases/${phaseId}`);
}

export async function getMyTripTravelers() {
  return request<{ travelers: TripTraveler[] }>('/me/trip/travelers');
}

export async function getMyQrCode() {
  return request<TravelerQrCode>('/me/qr-code');
}

export async function getMyAnnouncements() {
  return request<{ announcements: Announcement[]; unread_count: number }>('/me/announcements');
}

export async function markAnnouncementRead(id: string) {
  return request<{ status: string; announcement_id: string }>(`/me/announcements/${id}/read`, {
    method: 'POST',
  });
}

export async function getMyTeam() {
  return request<{ team: TeamMember[] }>('/me/team');
}

export interface EmergencyContact {
  id: string;
  name: string;
  role: string | null;
  phone: string | null;
  sort_order: number;
}

export interface Recommendation {
  id: string;
  name: string;
  description: string | null;
  address: string | null;
  photo_url: string | null;
  sort_order: number;
  category: string | null;
  neighborhood: string | null;
  location: string | null;
  highlight: string | null;
  price_range: string | null;
  rating: number | null;
  map_url: string | null;
  emoji: string | null;
}

export async function getMyEmergencyContacts() {
  return request<{ emergency_contacts: EmergencyContact[] }>('/me/emergency-contacts');
}

export async function getMyRecommendations() {
  return request<{ recommendations: Recommendation[] }>('/me/recommendations');
}

export interface FaqItem {
  id: string;
  question: string;
  answer: string;
  sort_order: number;
}

export interface CancellationPolicyItem {
  id: string;
  title: string;
  body: string;
  sort_order: number;
}

export async function getMyFaq() {
  return request<{ faq: FaqItem[] }>('/me/faq');
}

export async function getMyCancellationPolicy() {
  return request<{ cancellation_policy: CancellationPolicyItem[] }>('/me/cancellation-policy');
}

export async function getMyAppFeedback() {
  return request<{ feedback: string | null }>('/me/app-feedback');
}

export async function updateMyAppFeedback(feedback: string) {
  return request<{ feedback: string; updated_at: string }>('/me/app-feedback', {
    method: 'PUT',
    body: JSON.stringify({ feedback }),
  });
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
