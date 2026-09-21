import { request } from './client';

export const PRE_DEPARTURE_LINK =
  'https://parrot-trips.netlify.app/profile?section=pre-departure';

export interface Trip {
  trip_uuid: string;
  title: string;
  start_date: string | null;
  end_date: string | null;
}

export function listTrips() {
  return request<{ trips: Trip[] }>('/console/trips');
}
