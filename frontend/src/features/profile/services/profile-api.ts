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
  roommate_user_id: string | null;
  arrival_date: string | null;
  arrival_time: string | null;
  arrival_flight: string | null;
  departure_date: string | null;
  departure_time: string | null;
  departure_flight: string | null;
  avatar_url: string | null;
  visa_status: string | null;
  checked_bags: string | null;
  travel_insurance_status: string | null;
  travel_insurance_brazil_medical_coverage: string | null;
  travel_insurance_provider: string | null;
  travel_insurance_policy_number: string | null;
  travel_insurance_notes: string | null;
  roommate_status: string | null;
  roommate_email: string | null;
  room_configuration: string | null;
  roommate_gender_preference: string | null;
  extended_stay_help: string | null;
  extended_stay_help_details: string | null;
  early_check_in_preference: string | null;
  emergency_contact: string | null;
  instagram_handle: string | null;
  trip_mood: string | null;
  social_topic: string | null;
  always_up_for: string | null;
  home_address: string | null;
  final_considerations: string | null;
}

export interface ProfileResponse {
  user_id: string;
  wetravel_trip_uuid: string;
  phone: string;
  name: string | null;
  profile: ProfileData | null;
  roommate: { id: string; name: string | null; phone: string } | null;
}

export async function getProfile(userId: string) {
  return request<ProfileResponse>(`/profile/${userId}`);
}

export async function updateProfile(userId: string, data: Partial<ProfileData>) {
  return request<{ message: string }>(`/profile/${userId}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  });
}
