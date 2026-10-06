// In-trip days are stored as midnight in the trip's local timezone (see
// backend/scripts/import_trip_content.py TRIP_LOCAL_TZ), so format them there
// to avoid travelers in other timezones seeing the previous day.
const TRIP_TIME_ZONE = 'America/Sao_Paulo';

export function formatDayDate(startsAt: string | null): string | null {
  if (!startsAt) return null;
  const d = new Date(startsAt);
  if (Number.isNaN(d.getTime())) return null;
  const opts = { timeZone: TRIP_TIME_ZONE } as const;
  const weekday = d.toLocaleDateString('en-US', { ...opts, weekday: 'short' });
  const monthDay = d.toLocaleDateString('en-US', { ...opts, month: 'short', day: '2-digit' });
  return `${weekday} • ${monthDay}`;
}
