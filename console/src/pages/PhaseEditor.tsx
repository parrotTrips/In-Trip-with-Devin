import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';

import {
  getPhases, replaceChecklist, replaceLinks, updatePhase,
  type ChecklistItem, type Phase, type PhaseLink,
} from '../api/console-api';
import { moveUp } from '../lib/move-up';

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

  if (error) return <p className="p-6 text-red-600">{error}</p>;
  if (!phase) return <p className="p-6">Carregando…</p>;

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
    <div className="max-w-2xl mx-auto p-6">
      <Link to={`/trips/${tripUuid}/phases`} className="text-sm underline">← Fases</Link>
      <h1 className="text-xl font-bold my-4">Editar fase</h1>

      <label htmlFor="title" className="block text-sm">Título</label>
      <input
        id="title" value={phase.title}
        onChange={e => setPhase({ ...phase, title: e.target.value })}
        className="w-full border rounded px-3 py-2 mb-3"
      />

      <label htmlFor="short" className="block text-sm">Descrição curta</label>
      <input
        id="short" value={phase.short_description}
        onChange={e => setPhase({ ...phase, short_description: e.target.value })}
        className="w-full border rounded px-3 py-2 mb-3"
      />

      <label htmlFor="detailed" className="block text-sm">Descrição completa</label>
      <textarea
        id="detailed" value={phase.detailed_description ?? ''}
        onChange={e => setPhase({ ...phase, detailed_description: e.target.value })}
        className="w-full border rounded px-3 py-2 mb-3"
      />

      <div className="flex gap-3 mb-6">
        <div className="flex-1">
          <label htmlFor="starts_at" className="block text-sm">Início</label>
          <input
            id="starts_at" type="datetime-local" value={startsAt}
            onChange={e => setStartsAt(e.target.value)}
            className="w-full border rounded px-3 py-2"
          />
        </div>
        <div className="flex-1">
          <label htmlFor="ends_at" className="block text-sm">Fim</label>
          <input
            id="ends_at" type="datetime-local" value={endsAt}
            onChange={e => setEndsAt(e.target.value)}
            className="w-full border rounded px-3 py-2"
          />
        </div>
      </div>
      <p className="text-xs text-gray-500 -mt-4 mb-6">
        Datas são opcionais. Deixe em branco se a fase não tiver data.
      </p>

      <h2 className="font-bold mb-2">Checklist</h2>
      <ul className="space-y-2 mb-3">
        {checklist.map((item, index) => (
          <li key={item.id} className="flex items-center gap-2">
            <input
              aria-label={`Item ${index + 1}`} value={item.label}
              onChange={e => setChecklist(checklist.map(
                (i, idx) => idx === index ? { ...i, label: e.target.value } : i
              ))}
              className="flex-1 border rounded px-2 py-1"
            />
            <button className="border rounded px-2 py-1 text-sm"
                    onClick={() => setChecklist(moveUp(checklist, index))}>
              Subir
            </button>
            <button className="border rounded px-2 py-1 text-sm text-red-700"
                    onClick={() => setChecklist(checklist.filter((_, idx) => idx !== index))}>
              Remover
            </button>
          </li>
        ))}
      </ul>
      <button
        className="border rounded px-3 py-1 text-sm mb-6"
        onClick={() => setChecklist([
          ...checklist,
          { id: `new-${checklist.length}`, label: '', is_required: false, sort_order: checklist.length },
        ])}
      >
        Adicionar item
      </button>

      <h2 className="font-bold mb-2">Links</h2>
      <ul className="space-y-2 mb-3">
        {links.map((link, index) => (
          <li key={link.id} className="flex items-center gap-2">
            <input
              aria-label={`Link ${index + 1} rótulo`} value={link.label}
              onChange={e => setLinks(links.map(
                (l, idx) => idx === index ? { ...l, label: e.target.value } : l
              ))}
              className="flex-1 border rounded px-2 py-1"
            />
            <input
              aria-label={`Link ${index + 1} url`} value={link.url}
              onChange={e => setLinks(links.map(
                (l, idx) => idx === index ? { ...l, url: e.target.value } : l
              ))}
              className="flex-1 border rounded px-2 py-1"
            />
            <button className="border rounded px-2 py-1 text-sm text-red-700"
                    onClick={() => setLinks(links.filter((_, idx) => idx !== index))}>
              Remover
            </button>
          </li>
        ))}
      </ul>
      <button
        className="border rounded px-3 py-1 text-sm mb-6"
        onClick={() => setLinks([
          ...links,
          { id: `new-${links.length}`, label: '', url: '', sort_order: links.length },
        ])}
      >
        Adicionar link
      </button>

      <div className="flex items-center gap-3">
        <button onClick={save} className="bg-black text-white rounded px-4 py-2">Salvar</button>
        {status && <span className="text-green-700 text-sm">{status}</span>}
      </div>
    </div>
  );
}
