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
import { CalendarDays, Clock, Plus, Save, ScanLine, Trash2 } from 'lucide-react';
import EmptyState from '../components/EmptyState';
import PageHeader from '../components/PageHeader';

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

  const TYPE_LABEL: Record<string, string> = {
    included: 'Incluída', optional: 'Opcional', suggested: 'Sugerida', logistics: 'Logística',
  };

  return (
    <div>
      <PageHeader
        title="Roteiro"
        description="Dias da viagem e suas atividades, na ordem em que acontecem."
        actions={day && (
          <Button
            onClick={() => act(
              () => createActivity(day.id, { name: 'Nova atividade', activity_type: 'included' }),
              'Atividade criada'
            )}
          >
            <Plus className="h-4 w-4" />
            Nova atividade
          </Button>
        )}
      />
      <Alert variant="info" className="mb-4">
        Alterações aqui aparecem no app dos viajantes assim que você salvar.
      </Alert>

      {error && <Alert variant="destructive" className="mb-4">{error}</Alert>}
      {status && <Alert variant="success" className="mb-4">{status}</Alert>}

      <div className="flex items-start gap-6">
        <Card className="sticky top-20 w-60 shrink-0">
          <CardContent className="p-2">
            <ul className="space-y-0.5">
              {days.map((d, index) => (
                <li key={d.id}>
                  <button
                    onClick={() => setSelected(d.id)}
                    className={cn(
                      'flex w-full items-start gap-2 rounded-md px-2 py-2 text-left text-sm transition-colors',
                      d.id === day?.id
                        ? 'bg-primary font-medium text-primary-foreground'
                        : 'hover:bg-accent hover:text-accent-foreground'
                    )}
                  >
                    <span className="mt-0.5 text-xs tabular-nums opacity-70">{index + 1}</span>
                    <span className="flex-1">
                      {d.title}
                      <span className="ml-1 opacity-60">({d.activities.length})</span>
                    </span>
                  </button>
                </li>
              ))}
            </ul>
            <Button
              variant="outline" size="sm" className="mt-2 w-full"
              onClick={() => act(
                () => createDay(tripUuid, `Dia ${days.length + 1}`), 'Dia criado'
              )}
            >
              <Plus className="h-4 w-4" />
              Novo dia
            </Button>
          </CardContent>
        </Card>

        <section className="min-w-0 flex-1">
          {!day ? (
            <EmptyState icon={CalendarDays} title="Nenhum dia cadastrado">
              Comece criando um dia.
            </EmptyState>
          ) : day.activities.length === 0 ? (
            <EmptyState icon={CalendarDays} title="Nenhuma atividade neste dia.">
              Use “Nova atividade” para adicionar a primeira.
            </EmptyState>
          ) : (
            <ul className="space-y-3">
              {day.activities.map(activity => {
                const locked = activity.checkin_count > 0 || activity.scan_count > 0;
                const time = toLocalInput(activity.starts_at).slice(11);
                return (
                  <li key={activity.id}><Card>
                    <div className="flex flex-wrap items-center gap-2 border-b px-4 py-3">
                      <span className="flex items-center gap-1 text-sm tabular-nums text-muted-foreground">
                        <Clock className="h-3.5 w-3.5" />
                        {time || '--:--'}
                      </span>
                      <span className="flex-1 truncate font-medium">{activity.name}</span>
                      <Badge variant="secondary">{TYPE_LABEL[activity.activity_type] ?? activity.activity_type}</Badge>
                      <span className="flex items-center gap-1 text-xs text-muted-foreground">
                        <ScanLine className="h-3.5 w-3.5" />
                        {activity.max_checkins} scan(s)
                      </span>
                    </div>
                    <CardContent>
                      <div className="grid gap-3 sm:grid-cols-3">
                        {FIELDS.map(field => (
                          <div key={field.key}>
                            <Label htmlFor={`${field.key}-${activity.id}`} className="mb-1 block text-xs text-muted-foreground">
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

                      <div className="mt-4 flex flex-wrap items-center gap-2">
                        <Button size="sm" onClick={() => act(
                          () => updateActivity(activity.id, drafts[activity.id] ?? {})
                        )}>
                          <Save className="h-4 w-4" />
                          Salvar
                        </Button>
                        <Button
                          variant="ghost" size="sm"
                          className="text-destructive hover:bg-destructive/10 hover:text-destructive"
                          disabled={locked}
                          onClick={() => act(() => deleteActivity(activity.id), 'Excluída')}
                        >
                          <Trash2 className="h-4 w-4" />
                          Excluir
                        </Button>
                        {locked && (
                          <Badge variant="warning">
                            {activity.checkin_count} check-in(s) e {activity.scan_count} scan(s):
                            excluir apagaria o registro de quem participou.
                          </Badge>
                        )}
                      </div>
                    </CardContent>
                  </Card></li>
                );
              })}
            </ul>
          )}
        </section>
      </div>
    </div>
  );
}
