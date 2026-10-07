import { useEffect, useState } from 'react';
import { Link, useParams, useSearchParams } from 'react-router-dom';

import {
  getPhases, savePhaseContent, type ChecklistItem, type EditablePhaseType, type Phase, type PhaseLink,
} from '../api/console-api';
import { moveUp } from '../lib/move-up';

function toLocalInput(iso: string | null): string {
  if (!iso) return '';
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return '';
  const pad = (number: number) => String(number).padStart(2, '0');
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`
    + `T${pad(date.getHours())}:${pad(date.getMinutes())}`;
}

function validHttpUrl(value: string): boolean {
  try {
    const url = new URL(value);
    return url.protocol === 'http:' || url.protocol === 'https:';
  } catch {
    return false;
  }
}

export default function PhaseEditor() {
  const { tripUuid = '', phaseId = '' } = useParams();
  const [searchParams] = useSearchParams();
  const phaseType: EditablePhaseType = searchParams.get('type') === 'post-trip' ? 'post-trip' : 'pre-trip';
  const [phase, setPhase] = useState<Phase | null>(null);
  const [checklist, setChecklist] = useState<ChecklistItem[]>([]);
  const [links, setLinks] = useState<PhaseLink[]>([]);
  const [startsAt, setStartsAt] = useState('');
  const [endsAt, setEndsAt] = useState('');
  const [status, setStatus] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    getPhases(tripUuid, phaseType)
      .then(data => {
        const found = data.phases.find(item => item.id === phaseId) ?? null;
        setPhase(found);
        setChecklist(found?.checklist ?? []);
        setLinks(found?.links ?? []);
        setStartsAt(toLocalInput(found?.starts_at ?? null));
        setEndsAt(toLocalInput(found?.ends_at ?? null));
      })
      .catch(err => setError((err as Error).message));
  }, [tripUuid, phaseId, phaseType]);

  if (!phase && error) return <p className="p-6 text-red-600">{error}</p>;
  if (!phase) return <p className="p-6">Carregando…</p>;

  const readOnly = phase.is_visible;

  const save = async () => {
    setStatus(null);
    setError(null);
    if (!phase.title.trim() || !phase.short_description.trim()) {
      setError('Título e descrição curta são obrigatórios.');
      return;
    }
    if (links.some(link => !validHttpUrl(link.url))) {
      setError('Informe uma URL válida com http:// ou https://.');
      return;
    }
    if (startsAt && endsAt && endsAt < startsAt) {
      setError('A data final não pode ser anterior à data inicial.');
      return;
    }
    setBusy(true);
    try {
      await savePhaseContent(phaseId, {
        title: phase.title.trim(),
        subtitle: phase.subtitle,
        icon: phase.icon,
        short_description: phase.short_description.trim(),
        detailed_description: phase.detailed_description,
        starts_at: startsAt || null,
        ends_at: endsAt || null,
        checklist: checklist.map(item => ({
          label: item.label.trim(), is_required: item.is_required,
        })),
        links: links.map(link => ({ label: link.label.trim(), url: link.url.trim() })),
      });
      setStatus('Salvo');
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto p-6">
      <Link
        to={`/trips/${tripUuid}/${phaseType === 'post-trip' ? 'wrap-up' : 'fases'}`}
        className="text-sm underline"
      >
        ← {phaseType === 'post-trip' ? 'Trip Wrap-up' : 'Fases'}
      </Link>
      <h1 className="text-xl font-bold my-4">Editar fase</h1>
      {readOnly && (
        <p className="border border-amber-300 bg-amber-50 text-amber-900 rounded p-3 mb-4">
          Despublique a fase para editar seu conteúdo.
        </p>
      )}
      {error && <p className="text-red-600 text-sm mb-3">{error}</p>}

      <label htmlFor="title" className="block text-sm">Título</label>
      <input id="title" value={phase.title} disabled={readOnly || busy}
        onChange={event => setPhase({ ...phase, title: event.target.value })}
        className="w-full border rounded px-3 py-2 mb-3 disabled:bg-gray-100" />

      <label htmlFor="short" className="block text-sm">Descrição curta</label>
      <input id="short" value={phase.short_description} disabled={readOnly || busy}
        onChange={event => setPhase({ ...phase, short_description: event.target.value })}
        className="w-full border rounded px-3 py-2 mb-3 disabled:bg-gray-100" />

      <label htmlFor="detailed" className="block text-sm">Descrição completa</label>
      <textarea id="detailed" value={phase.detailed_description ?? ''} disabled={readOnly || busy}
        onChange={event => setPhase({ ...phase, detailed_description: event.target.value })}
        className="w-full border rounded px-3 py-2 mb-3 disabled:bg-gray-100" />

      <div className="flex gap-3 mb-6">
        <div className="flex-1">
          <label htmlFor="starts_at" className="block text-sm">Início</label>
          <input id="starts_at" type="datetime-local" value={startsAt} disabled={readOnly || busy}
            onChange={event => setStartsAt(event.target.value)}
            className="w-full border rounded px-3 py-2 disabled:bg-gray-100" />
        </div>
        <div className="flex-1">
          <label htmlFor="ends_at" className="block text-sm">Fim</label>
          <input id="ends_at" type="datetime-local" value={endsAt} disabled={readOnly || busy}
            onChange={event => setEndsAt(event.target.value)}
            className="w-full border rounded px-3 py-2 disabled:bg-gray-100" />
        </div>
      </div>

      <h2 className="font-bold mb-2">Checklist</h2>
      <ul className="space-y-2 mb-3">
        {checklist.map((item, index) => (
          <li key={item.id} className="flex items-center gap-2">
            <input aria-label={`Item ${index + 1}`} value={item.label} disabled={readOnly || busy}
              onChange={event => setChecklist(checklist.map(
                (current, currentIndex) => currentIndex === index
                  ? { ...current, label: event.target.value } : current
              ))} className="flex-1 border rounded px-2 py-1 disabled:bg-gray-100" />
            <button disabled={readOnly || busy || index === 0}
              onClick={() => setChecklist(moveUp(checklist, index))}>Subir</button>
            <button disabled={readOnly || busy}
              onClick={() => setChecklist(checklist.filter((_, current) => current !== index))}>
              Remover
            </button>
          </li>
        ))}
      </ul>
      <button disabled={readOnly || busy} onClick={() => setChecklist([
        ...checklist,
        { id: `new-${crypto.randomUUID()}`, label: '', is_required: false, sort_order: checklist.length },
      ])}>Adicionar item</button>

      <h2 className="font-bold mt-6 mb-2">Links</h2>
      <ul className="space-y-2 mb-3">
        {links.map((link, index) => (
          <li key={link.id} className="flex items-center gap-2">
            <input aria-label={`Link ${index + 1} rótulo`} value={link.label}
              disabled={readOnly || busy} onChange={event => setLinks(links.map(
                (current, currentIndex) => currentIndex === index
                  ? { ...current, label: event.target.value } : current
              ))} />
            <input aria-label={`Link ${index + 1} url`} value={link.url}
              disabled={readOnly || busy} onChange={event => setLinks(links.map(
                (current, currentIndex) => currentIndex === index
                  ? { ...current, url: event.target.value } : current
              ))} />
            <button disabled={readOnly || busy}
              onClick={() => setLinks(links.filter((_, current) => current !== index))}>
              Remover
            </button>
          </li>
        ))}
      </ul>
      <button disabled={readOnly || busy} onClick={() => setLinks([
        ...links,
        { id: `new-${crypto.randomUUID()}`, label: '', url: '', sort_order: links.length },
      ])}>Adicionar link</button>

      <div className="flex items-center gap-3 mt-6">
        <button disabled={readOnly || busy} onClick={() => void save()}
          className="bg-black text-white rounded px-4 py-2 disabled:opacity-50">
          {busy ? 'Salvando…' : 'Salvar'}
        </button>
        {status && <span className="text-green-700 text-sm">{status}</span>}
      </div>
    </div>
  );
}
