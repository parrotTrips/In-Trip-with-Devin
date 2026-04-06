import { request } from '../../../shared/api/client';

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
