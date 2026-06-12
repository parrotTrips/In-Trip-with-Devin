import { request } from '../../../shared/api/client';

export interface StaffActivity {
  id: string;
  name: string;
  activity_type: string;
  starts_at: string | null;
  duration_minutes: number | null;
  short_description: string;
  practical_info: string | null;
  amount_brl: number | null;
  sort_order: number;
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
