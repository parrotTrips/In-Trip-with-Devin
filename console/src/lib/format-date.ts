const MONTHS = ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez'];

/** "2026-10-05" → "05 out 2026", sem passar por Date (sem risco de fuso). */
export function formatDay(value: string | null | undefined): string {
  const match = value?.match(/^(\d{4})-(\d{2})-(\d{2})/);
  if (!match) return value ?? '';
  return `${match[3]} ${MONTHS[Number(match[2]) - 1]} ${match[1]}`;
}

export function formatRange(start: string | null, end: string | null): string {
  if (!start && !end) return 'Sem datas';
  return `${formatDay(start)} – ${formatDay(end)}`;
}

/** Situação da viagem pelas datas: em andamento, próxima ou sem data. */
export function tripStatus(start: string | null, end: string | null, today = new Date()): 'current' | 'upcoming' | 'past' | 'unknown' {
  if (!start) return 'unknown';
  const pad = (n: number) => String(n).padStart(2, '0');
  const iso = `${today.getFullYear()}-${pad(today.getMonth() + 1)}-${pad(today.getDate())}`;
  if (start.slice(0, 10) > iso) return 'upcoming';
  if (!end || end.slice(0, 10) >= iso) return 'current';
  return 'past';
}
