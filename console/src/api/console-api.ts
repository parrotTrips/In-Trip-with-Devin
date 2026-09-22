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
  tripUuid: string, sectionKey: string, items: Record<string, unknown>[]
) {
  return request<{ key: string; count: number }>(
    `/console/trips/${tripUuid}/sections/${sectionKey}`,
    { method: 'PUT', body: JSON.stringify({ items }) }
  );
}
