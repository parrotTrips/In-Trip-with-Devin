import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';

import {
  getPhases, replaceChecklist, replaceLinks, updatePhase,
  type ChecklistItem, type Phase, type PhaseLink,
} from '../api/console-api';
import { moveUp } from '../lib/move-up';
import { Alert } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';

/** ISO do servidor para o formato que <input type="datetime-local"> aceita. */
function toLocalInput(iso: string | null): string {
  if (!iso) return '';
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return '';
  const pad = (n: number) => String(n).padStart(2, '0');
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`
    + `T${pad(date.getHours())}:${pad(date.getMinutes())}`;
}

export default function PhaseEditor() {
  const { tripUuid = '', phaseId = '' } = useParams();
  const [phase, setPhase] = useState<Phase | null>(null);
  const [checklist, setChecklist] = useState<ChecklistItem[]>([]);
  const [links, setLinks] = useState<PhaseLink[]>([]);
  const [startsAt, setStartsAt] = useState('');
  const [endsAt, setEndsAt] = useState('');
  const [status, setStatus] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getPhases(tripUuid)
      .then(data => {
        const found = data.phases.find(p => p.id === phaseId) ?? null;
        setPhase(found);
        setChecklist(found?.checklist ?? []);
        setLinks(found?.links ?? []);
        setStartsAt(toLocalInput(found?.starts_at ?? null));
        setEndsAt(toLocalInput(found?.ends_at ?? null));
      })
      .catch(err => setError((err as Error).message));
  }, [tripUuid, phaseId]);

  if (error) return <Alert variant="destructive" className="m-6">{error}</Alert>;
  if (!phase) return <p className="p-6 text-muted-foreground">Carregando…</p>;

  const save = async () => {
    setStatus(null);
    setError(null);
    try {
      await updatePhase(phaseId, {
        title: phase.title,
        subtitle: phase.subtitle,
        icon: phase.icon,
        short_description: phase.short_description,
        detailed_description: phase.detailed_description,
        starts_at: startsAt || null,
        ends_at: endsAt || null,
      });
      await replaceChecklist(
        phaseId, checklist.map(i => ({ label: i.label, is_required: i.is_required }))
      );
      await replaceLinks(phaseId, links.map(l => ({ label: l.label, url: l.url })));
      setStatus('Salvo');
    } catch (err) {
      setError((err as Error).message);
    }
  };

  return (
    <div className="mx-auto max-w-2xl p-8">
      <Link to={`/trips/${tripUuid}/fases`} className="text-sm text-muted-foreground hover:text-foreground">← Fases</Link>
      <h1 className="my-4 text-xl font-bold tracking-tight">Editar fase</h1>

      <Label htmlFor="title" className="mb-1 block">Título</Label>
      <Input
        id="title" value={phase.title} className="mb-3"
        onChange={e => setPhase({ ...phase, title: e.target.value })}
      />

      <Label htmlFor="short" className="mb-1 block">Descrição curta</Label>
      <Input
        id="short" value={phase.short_description} className="mb-3"
        onChange={e => setPhase({ ...phase, short_description: e.target.value })}
      />

      <Label htmlFor="detailed" className="mb-1 block">Descrição completa</Label>
      <Textarea
        id="detailed" value={phase.detailed_description ?? ''} className="mb-3"
        onChange={e => setPhase({ ...phase, detailed_description: e.target.value })}
      />

      <div className="flex gap-3 mb-6">
        <div className="flex-1">
          <Label htmlFor="starts_at" className="mb-1 block">Início</Label>
          <Input
            id="starts_at" type="datetime-local" value={startsAt}
            onChange={e => setStartsAt(e.target.value)}
          />
        </div>
        <div className="flex-1">
          <Label htmlFor="ends_at" className="mb-1 block">Fim</Label>
          <Input
            id="ends_at" type="datetime-local" value={endsAt}
            onChange={e => setEndsAt(e.target.value)}
          />
        </div>
      </div>
      <p className="-mt-4 mb-6 text-xs text-muted-foreground">
        Datas são opcionais. Deixe em branco se a fase não tiver data.
      </p>

      <h2 className="mb-2 font-semibold">Checklist</h2>
      <ul className="space-y-2 mb-3">
        {checklist.map((item, index) => (
          <li key={item.id} className="flex items-center gap-2">
            <Input
              aria-label={`Item ${index + 1}`} value={item.label}
              onChange={e => setChecklist(checklist.map(
                (i, idx) => idx === index ? { ...i, label: e.target.value } : i
              ))}
              className="flex-1"
            />
            <Button variant="outline" size="sm"
                    onClick={() => setChecklist(moveUp(checklist, index))}>
              Subir
            </Button>
            <Button variant="outline" size="sm"
                    className="text-destructive hover:text-destructive"
                    onClick={() => setChecklist(checklist.filter((_, idx) => idx !== index))}>
              Remover
            </Button>
          </li>
        ))}
      </ul>
      <Button
        variant="outline" size="sm" className="mb-6"
        onClick={() => setChecklist([
          ...checklist,
          { id: `new-${checklist.length}`, label: '', is_required: false, sort_order: checklist.length },
        ])}
      >
        Adicionar item
      </Button>

      <h2 className="mb-2 font-semibold">Links</h2>
      <ul className="space-y-2 mb-3">
        {links.map((link, index) => (
          <li key={link.id} className="flex items-center gap-2">
            <Input
              aria-label={`Link ${index + 1} rótulo`} value={link.label}
              onChange={e => setLinks(links.map(
                (l, idx) => idx === index ? { ...l, label: e.target.value } : l
              ))}
              className="flex-1 border rounded px-2 py-1"
            />
            <Input
              aria-label={`Link ${index + 1} url`} value={link.url}
              onChange={e => setLinks(links.map(
                (l, idx) => idx === index ? { ...l, url: e.target.value } : l
              ))}
              className="flex-1"
            />
            <Button variant="outline" size="sm"
                    className="text-destructive hover:text-destructive"
                    onClick={() => setLinks(links.filter((_, idx) => idx !== index))}>
              Remover
            </Button>
          </li>
        ))}
      </ul>
      <Button
        variant="outline" size="sm" className="mb-6"
        onClick={() => setLinks([
          ...links,
          { id: `new-${links.length}`, label: '', url: '', sort_order: links.length },
        ])}
      >
        Adicionar link
      </Button>

      <div className="flex items-center gap-3">
        <Button onClick={save}>Salvar</Button>
        {status && <span className="text-sm font-medium text-primary">{status}</span>}
      </div>
    </div>
  );
}
