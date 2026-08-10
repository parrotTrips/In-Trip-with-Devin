import { request } from '../../../shared/api/client';

export interface StaffTask {
  id: string;
  title: string;
  description: string | null;
  sort_order: number;
}

export interface StaffActivity {
  id: string;
  name: string;
  activity_type: string;
  starts_at: string | null;
  duration_minutes: number | null;
  short_description: string;
  practical_info: string | null;
  address: string | null;
  max_checkins: number;
  amount_brl: number | null;
  sort_order: number;
  checkin_steps: CheckinStep[];
  absent_travelers: string[];
  traveler_count: number;
  staff_tasks: StaffTask[];
}

export interface ActivityScanResponse {
  status: 'checked_in' | 'already_checked_in';
  traveler_name?: string | null;
  scanned_by_name?: string | null;
  checked_in_at?: string | null;
  scan_number?: number | null;
  max_checkins?: number | null;
}

export interface CheckinDetail {
  name: string;
  checked_in_at: string | null;
}

export interface CheckinStep {
  step: number;
  count: number;
  travelers: string[];
  details: CheckinDetail[];
}

export interface StaffDay {
  id: string;
  title: string;
  subtitle: string | null;
  icon: string | null;
  sort_order: number;
  starts_at: string | null;
  activities: StaffActivity[];
}

export interface StaffTrip {
  wetravel_trip_uuid: string;
  title: string;
  start_date: string | null;
  end_date: string | null;
  days: StaffDay[];
}

export async function getStaffTrip() {
  return request<StaffTrip>('/me/staff/trip');
}

export async function scanActivityTraveler(activityId: string, qrPayload: string) {
  return request<ActivityScanResponse>(`/me/staff/activities/${activityId}/checkins/scan`, {
    method: 'POST',
    body: JSON.stringify({ qr_payload: qrPayload }),
  });
}

export interface StaffContact {
  id: string;
  name: string;
  role: string | null;
  phone: string | null;
  sort_order: number;
}

export interface StaffContactGroup {
  category: string;
  contacts: StaffContact[];
}

export interface StaffContactsResponse {
  wetravel_trip_uuid: string;
  contacts: StaffContactGroup[];
}

export async function getStaffContacts() {
  return request<StaffContactsResponse>('/me/staff/trip/contacts');
}

export interface StaffAnnouncement {
  id: string;
  title: string;
  body: string;
  sent_by: string;
  sent_by_user_id: string;
  is_anonymous: boolean;
  created_at: string;
}

export interface ActivityTraveler {
  id: string;
  name: string;
  qr_payload: string;
}

export async function getActivityTravelers(activityId: string) {
  return request<{ travelers: ActivityTraveler[] }>(`/me/staff/activities/${activityId}/travelers`);
}

export async function getStaffAnnouncements() {
  return request<{ announcements: StaffAnnouncement[] }>('/me/staff/announcements');
}

export async function sendAnnouncement(title: string, body: string, is_anonymous = false) {
  return request<{ id: string; created_at: string }>('/me/staff/announcements', {
    method: 'POST',
    body: JSON.stringify({ title, body, is_anonymous }),
  });
}

export async function updateAnnouncement(id: string, title: string, body: string) {
  return request<{ id: string; title: string; body: string }>(`/me/staff/announcements/${id}`, {
    method: 'PUT',
    body: JSON.stringify({ title, body }),
  });
}

export async function deleteAnnouncement(id: string) {
  return request<{ status: string }>(`/me/staff/announcements/${id}`, {
    method: 'DELETE',
  });
}
