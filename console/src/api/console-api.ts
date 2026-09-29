import { request } from './client';

export const PRE_DEPARTURE_LINK =
  'https://parrot-trips.netlify.app/profile?section=pre-departure';

export interface Trip {
  trip_uuid: string;
  title: string;
  destination: string | null;
  start_date: string | null;
  end_date: string | null;
  traveler_count: number;
  mode: string | null;
}

export function listTrips() {
  return request<{ trips: Trip[] }>('/console/trips');
}

export interface ChecklistItem {
  id: string;
  label: string;
  is_required: boolean;
  sort_order: number;
}

export interface PhaseLink {
  id: string;
  label: string;
  url: string;
  sort_order: number;
}

export interface Phase {
  id: string;
  title: string;
  subtitle: string | null;
  icon: string | null;
  short_description: string;
  detailed_description: string | null;
  sort_order: number;
  is_visible: boolean;
  starts_at: string | null;
  ends_at: string | null;
  checklist: ChecklistItem[];
  links: PhaseLink[];
}

export function getPhases(tripUuid: string) {
  return request<{ phases: Phase[] }>(`/console/trips/${tripUuid}/phases`);
}

export function createPhase(tripUuid: string, body: { title: string; short_description: string }) {
  return request<{ id: string; is_visible: boolean }>(
    `/console/trips/${tripUuid}/phases`,
    { method: 'POST', body: JSON.stringify(body) }
  );
}

export function publishPhase(phaseId: string) {
  return request<{ id: string; is_visible: boolean }>(
    `/console/phases/${phaseId}/publish`, { method: 'POST' }
  );
}

export function unpublishPhase(phaseId: string) {
  return request<{ id: string; is_visible: boolean }>(
    `/console/phases/${phaseId}/unpublish`, { method: 'POST' }
  );
}

export function deletePhase(phaseId: string) {
  return request<{ id: string; deleted: boolean }>(
    `/console/phases/${phaseId}`, { method: 'DELETE' }
  );
}

export function updatePhase(phaseId: string, body: Partial<Pick<Phase,
  'title' | 'subtitle' | 'icon' | 'short_description' | 'detailed_description'
  | 'starts_at' | 'ends_at'>>) {
  return request<{ id: string; updated: boolean }>(
    `/console/phases/${phaseId}`, { method: 'PATCH', body: JSON.stringify(body) }
  );
}

export function replaceChecklist(
  phaseId: string, items: { label: string; is_required: boolean }[]
) {
  return request<{ count: number }>(
    `/console/phases/${phaseId}/checklist`,
    { method: 'PUT', body: JSON.stringify({ items }) }
  );
}

export function replaceLinks(phaseId: string, links: { label: string; url: string }[]) {
  return request<{ count: number }>(
    `/console/phases/${phaseId}/links`,
    { method: 'PUT', body: JSON.stringify({ links }) }
  );
}

export function reorderPhases(tripUuid: string, phaseIds: string[]) {
  return request<{ count: number }>(
    `/console/trips/${tripUuid}/phases/order`,
    { method: 'PUT', body: JSON.stringify({ phase_ids: phaseIds }) }
  );
}

export type PhaseContentInput = {
  title: string;
  subtitle: string | null;
  icon: string | null;
  short_description: string;
  detailed_description: string | null;
  starts_at: string | null;
  ends_at: string | null;
  checklist: { label: string; is_required: boolean }[];
  links: { label: string; url: string }[];
};

export function savePhaseContent(phaseId: string, body: PhaseContentInput) {
  return request<{ id: string; updated: boolean }>(
    `/console/phases/${phaseId}/content`,
    { method: 'PUT', body: JSON.stringify(body) },
  );
}

export interface TripSection {
  key: string;
  label: string;
  group: string;
  group_label: string;
  count: number;
  editable: boolean;
  readonly_note: string | null;
}

export interface SectionColumn {
  key: string;
  label: string;
  required: boolean;
  kind: 'text' | 'textarea' | 'select' | 'url' | 'number';
  choices: string[];
}

export interface SectionRows {
  key: string;
  label: string;
  readonly_note: string | null;
  editable: boolean;
  columns: SectionColumn[];
  rows: Record<string, unknown>[];
}

export function listSections(tripUuid: string) {
  return request<{ sections: TripSection[] }>(`/console/trips/${tripUuid}/sections`);
}

export function getSection(tripUuid: string, sectionKey: string) {
  return request<SectionRows>(`/console/trips/${tripUuid}/sections/${sectionKey}`);
}

export function replaceSection(
  tripUuid: string,
  sectionKey: string,
  items: Record<string, unknown>[]
) {
  return request<{ key: string; count: number }>(
    `/console/trips/${tripUuid}/sections/${sectionKey}`,
    { method: 'PUT', body: JSON.stringify({ items }) }
  );
}

export const ACTIVITY_TYPES = ['included', 'optional', 'suggested', 'logistics'] as const;

export interface Activity {
  id: string;
  name: string;
  activity_type: string;
  starts_at: string | null;
  duration_minutes: number | null;
  short_description: string;
  practical_info: string;
  address: string | null;
  max_checkins: number;
  amount_brl: number | null;
  sort_order: number;
  checkin_count: number;
  scan_count: number;
}

export interface Day {
  id: string;
  title: string;
  sort_order: number;
  is_visible: boolean;
  activities: Activity[];
}

export function getDays(tripUuid: string) {
  return request<{ days: Day[] }>(`/console/trips/${tripUuid}/days`);
}

export function createDay(tripUuid: string, title: string) {
  return request<{ id: string }>(`/console/trips/${tripUuid}/days`, {
    method: 'POST',
    body: JSON.stringify({ title, short_description: '' }),
  });
}

export function createActivity(dayId: string, body: Partial<Activity>) {
  return request<{ id: string }>(`/console/days/${dayId}/activities`, {
    method: 'POST',
    body: JSON.stringify(body),
  });
}

export function updateActivity(activityId: string, body: Partial<Activity>) {
  return request<{ id: string; updated: boolean }>(`/console/activities/${activityId}`, {
    method: 'PATCH',
    body: JSON.stringify(body),
  });
}

export function deleteActivity(activityId: string) {
  return request<{ id: string; deleted: boolean }>(`/console/activities/${activityId}`, {
    method: 'DELETE',
  });
}
