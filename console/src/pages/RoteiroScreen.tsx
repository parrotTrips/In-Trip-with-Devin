import { useCallback, useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';

import {
  ACTIVITY_TYPES, createActivity, createDay, deleteActivity, getDays,
  updateActivity, type Activity, type Day,
} from '../api/console-api';
import { Alert } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select } from '@/components/ui/select';
import { cn } from '@/lib/utils';

const FIELDS: { key: keyof Activity; label: string; kind?: string }[] = [
  { key: 'name', label: 'Nome' },
  { key: 'activity_type', label: 'Tipo', kind: 'select' },
  { key: 'starts_at', label: 'Início', kind: 'datetime-local' },
  { key: 'duration_minutes', label: 'Duração (min)', kind: 'number' },
  { key: 'short_description', label: 'Descrição curta' },
  { key: 'practical_info', label: 'Informação prática' },
  { key: 'address', label: 'Endereço' },
  { key: 'max_checkins', label: 'Limite de scans', kind: 'number' },
  { key: 'amount_brl', label: 'Preço (R$)', kind: 'number' },
];

/** ISO do servidor para o formato aceito por input datetime-local. */
function toLocalInput(iso: unknown): string {
  if (typeof iso !== 'string' || !iso) return '';
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return '';
  const pad = (n: number) => String(n).padStart(2, '0');
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`
    + `T${pad(date.getHours())}:${pad(date.getMinutes())}`;
}

export default function RoteiroScreen() {
  const { tripUuid = '' } = useParams();
  const [days, setDays] = useState<Day[]>([]);
  const [selected, setSelected] = useState<string | null>(null);
  const [drafts, setDrafts] = useState<Record<string, Partial<Activity>>>({});
  const [status, setStatus] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const reload = useCallback(async () => {
    try {
      const data = await getDays(tripUuid);
      setDays(data.days);
      setDrafts({});
      setSelected(current => current ?? data.days[0]?.id ?? null);
    } catch (err) {
      setError((err as Error).message);
    }
  }, [tripUuid]);

  useEffect(() => { void reload(); }, [reload]);

  const day = days.find(d => d.id === selected) ?? days[0] ?? null;

  const act = async (action: () => Promise<unknown>, done = 'Salvo') => {
    setStatus(null);
    setError(null);
    try {
      await action();
      await reload();
      setStatus(done);
    } catch (err) {
      setError((err as Error).message);
    }
  };

  const valueOf = (activity: Activity, key: keyof Activity) => {
    const draft = drafts[activity.id];
    const raw = draft && key in draft ? draft[key] : activity[key];
    return key === 'starts_at' ? toLocalInput(raw) : String(raw ?? '');
  };

  const setField = (activity: Activity, key: keyof Activity, value: string) =>
    setDrafts({ ...drafts, [activity.id]: { ...drafts[activity.id], [key]: value } });

  return (
    <div>
      <h1 className="mb-2 text-xl font-bold tracking-tight">Roteiro</h1>
      <Alert variant="info" className="mb-4">
        Alterações aqui aparecem no app dos viajantes assim que você salvar.
      </Alert>

      {error && <Alert variant="destructive" className="mb-4">{error}</Alert>}
      {status && <Alert variant="success" className="mb-4">{status}</Alert>}

      <div className="flex gap-6">
        <aside className="w-56 shrink-0">
          <ul className="space-y-1">
            {days.map(d => (
              <li key={d.id}>
                <button
                  onClick={() => setSelected(d.id)}
                  className={cn(
                    'w-full rounded-md px-2 py-1.5 text-left text-sm transition-colors',
                    d.id === day?.id
                      ? 'bg-primary font-medium text-primary-foreground'
                      : 'hover:bg-accent hover:text-accent-foreground'
                  )}
                >
                  {d.title}
                  <span className="ml-1 opacity-60">({d.activities.length})</span>
                </button>
              </li>
            ))}
          </ul>
          <Button
            variant="outline" size="sm" className="mt-3 w-full"
            onClick={() => act(
              () => createDay(tripUuid, `Dia ${days.length + 1}`), 'Dia criado'
            )}
          >
            Novo dia
          </Button>
        </aside>

        <section className="flex-1">
          {!day ? (
            <p className="rounded-lg border border-dashed p-8 text-center text-muted-foreground">
              Nenhum dia cadastrado. Comece criando um dia.
            </p>
          ) : day.activities.length === 0 ? (
            <p className="rounded-lg border border-dashed p-8 text-center text-muted-foreground">
              Nenhuma atividade neste dia.
            </p>
          ) : (
            <ul className="space-y-3">
              {day.activities.map(activity => {
                const locked = activity.checkin_count > 0 || activity.scan_count > 0;
                return (
                  <li key={activity.id}><Card><CardContent>
                    <div className="grid grid-cols-3 gap-2">
                      {FIELDS.map(field => (
                        <div key={field.key}>
                          <Label htmlFor={`${field.key}-${activity.id}`} className="mb-1 block">
                            {field.label}
                          </Label>
                          {field.kind === 'select' ? (
                            <Select
                              id={`${field.key}-${activity.id}`}
                              value={valueOf(activity, field.key)}
                              onChange={e => setField(activity, field.key, e.target.value)}
                            >
                              {ACTIVITY_TYPES.map(type => (
                                <option key={type} value={type}>{type}</option>
                              ))}
                            </Select>
                          ) : (
                            <Input
                              id={`${field.key}-${activity.id}`}
                              type={field.kind === 'number' ? 'number'
                                : field.kind === 'datetime-local' ? 'datetime-local' : 'text'}
                              value={valueOf(activity, field.key)}
                              onChange={e => setField(activity, field.key, e.target.value)}
                            />
                          )}
                        </div>
                      ))}
                    </div>

                    <div className="mt-2 flex items-center gap-2">
                      <Button size="sm" onClick={() => act(
                        () => updateActivity(activity.id, drafts[activity.id] ?? {})
                      )}>
                        Salvar
                      </Button>
                      <Button
                        variant="outline" size="sm"
                        className="text-destructive hover:text-destructive"
                        disabled={locked}
                        onClick={() => act(() => deleteActivity(activity.id), 'Excluída')}
                      >
                        Excluir
                      </Button>
                      {locked && (
                        <Badge variant="warning">
                          {activity.checkin_count} check-in(s) e {activity.scan_count} scan(s):
                          excluir apagaria o registro de quem participou.
                        </Badge>
                      )}
                    </div>
                  </CardContent></Card></li>
                );
              })}
            </ul>
          )}

          {day && (
            <Button
              variant="outline" className="mt-3"
              onClick={() => act(
                () => createActivity(day.id, { name: 'Nova atividade', activity_type: 'included' }),
                'Atividade criada'
              )}
            >
              Nova atividade
            </Button>
          )}
        </section>
      </div>
    </div>
  );
}
