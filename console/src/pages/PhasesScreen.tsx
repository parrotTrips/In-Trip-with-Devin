import { useCallback, useEffect, useState, type FormEvent } from 'react';
import { Link, useParams } from 'react-router-dom';

import {
  createPhase, deletePhase, getPhases, publishPhase, reorderPhases, unpublishPhase, type Phase,
} from '../api/console-api';
import { moveUp } from '../lib/move-up';

export default function PhasesScreen() {
  const { tripUuid = '' } = useParams();
  const [phases, setPhases] = useState<Phase[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [creating, setCreating] = useState(false);
  const [newTitle, setNewTitle] = useState('');
  const [newDescription, setNewDescription] = useState('');
  const [deleteTarget, setDeleteTarget] = useState<Phase | null>(null);
  const [deleteConfirmation, setDeleteConfirmation] = useState('');

  const reload = useCallback(async () => {
    const data = await getPhases(tripUuid);
    setPhases(data.phases ?? []);
  }, [tripUuid]);

  useEffect(() => {
    reload().catch(err => setError((err as Error).message));
  }, [reload]);

  const act = async (action: () => Promise<unknown>) => {
    setError(null);
    setBusy(true);
    try {
      await action();
      await reload();
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  };

  const submitCreate = async (event: FormEvent) => {
    event.preventDefault();
    if (!newTitle.trim() || !newDescription.trim()) return;
    await act(() => createPhase(tripUuid, {
      title: newTitle.trim(), short_description: newDescription.trim(),
    }));
    setNewTitle('');
    setNewDescription('');
    setCreating(false);
  };

  const hasPublished = phases.some(phase => phase.is_visible);

  return (
    <div className="max-w-3xl mx-auto p-6">
      <Link to="/" className="text-sm underline">← Viagens</Link>
      <h1 className="text-xl font-bold my-4">Fases</h1>
      <p className="border border-amber-300 bg-amber-50 text-amber-900 rounded p-3 text-sm mb-4">
        Não importe esta viagem pela planilha depois de editá-la aqui. O import legado pode
        substituir fases, checklist e links.
      </p>
      {hasPublished && (
        <p className="text-sm text-gray-600 mb-3">
          Despublique todas as fases antes de alterar a ordem.
        </p>
      )}
      {error && <p className="text-red-600 text-sm mb-3">{error}</p>}

      <ul className="space-y-2 mb-6">
        {phases.map((phase, index) => (
          <li key={phase.id} className="border rounded p-3 flex items-center gap-3">
            <div className="flex-1">
              {phase.is_visible ? (
                <span className="font-medium">{phase.title}</span>
              ) : (
                <Link
                  to={`/trips/${tripUuid}/phases/${phase.id}`}
                  className="font-medium underline"
                >
                  {phase.title}
                </Link>
              )}
              <p className="text-sm text-gray-600">
                {phase.checklist.length} itens · {phase.links.length} links
              </p>
            </div>
            <span className={phase.is_visible ? 'text-green-700 text-sm' : 'text-amber-700 text-sm'}>
              {phase.is_visible ? 'Publicada' : 'Rascunho'}
            </span>
            <button
              className="border rounded px-2 py-1 text-sm disabled:opacity-50"
              disabled={busy || hasPublished || index === 0}
              onClick={() => {
                const reordered = moveUp(phases, index);
                setPhases(reordered);
                void act(() => reorderPhases(tripUuid, reordered.map(item => item.id)));
              }}
            >
              Subir
            </button>
            <button
              className="border rounded px-2 py-1 text-sm disabled:opacity-50"
              disabled={busy}
              onClick={() => void act(() => (
                phase.is_visible ? unpublishPhase(phase.id) : publishPhase(phase.id)
              ))}
            >
              {phase.is_visible ? 'Despublicar' : 'Publicar'}
            </button>
            {!phase.is_visible && (
              <button
                className="border rounded px-2 py-1 text-sm text-red-700 disabled:opacity-50"
                disabled={busy}
                onClick={() => {
                  setDeleteTarget(phase);
                  setDeleteConfirmation('');
                }}
              >
                Excluir
              </button>
            )}
          </li>
        ))}
      </ul>

      {!creating ? (
        <button className="border rounded px-3 py-2" onClick={() => setCreating(true)}>
          Nova fase
        </button>
      ) : (
        <form onSubmit={submitCreate} className="border rounded p-4 space-y-3">
          <label htmlFor="new-phase-title" className="block text-sm">Título da fase</label>
          <input
            id="new-phase-title" value={newTitle} onChange={event => setNewTitle(event.target.value)}
            disabled={busy} className="w-full border rounded px-3 py-2"
          />
          <label htmlFor="new-phase-description" className="block text-sm">
            Descrição curta da fase
          </label>
          <input
            id="new-phase-description" value={newDescription}
            onChange={event => setNewDescription(event.target.value)} disabled={busy}
            className="w-full border rounded px-3 py-2"
          />
          <div className="flex gap-2">
            <button
              type="submit" disabled={busy || !newTitle.trim() || !newDescription.trim()}
              className="bg-black text-white rounded px-3 py-2 disabled:opacity-50"
            >
              {busy ? 'Criando…' : 'Criar fase'}
            </button>
            <button type="button" disabled={busy} onClick={() => setCreating(false)}>
              Cancelar
            </button>
          </div>
        </form>
      )}

      {deleteTarget && (
        <div role="dialog" aria-modal="true" aria-labelledby="delete-title"
             className="fixed inset-0 bg-black/40 flex items-center justify-center p-4">
          <div className="bg-white rounded p-5 max-w-md w-full">
            <h2 id="delete-title" className="font-bold">Excluir {deleteTarget.title}?</h2>
            <p className="text-sm my-3">Digite o título da fase para confirmar.</p>
            <label htmlFor="delete-confirmation" className="block text-sm">
              Digite o título da fase
            </label>
            <input
              id="delete-confirmation" value={deleteConfirmation}
              onChange={event => setDeleteConfirmation(event.target.value)}
              disabled={busy} className="w-full border rounded px-3 py-2 my-2"
            />
            <div className="flex gap-2">
              <button
                disabled={busy || deleteConfirmation !== deleteTarget.title}
                className="bg-red-700 text-white rounded px-3 py-2 disabled:opacity-50"
                onClick={() => void act(() => deletePhase(deleteTarget.id)).then(() => {
                  setDeleteTarget(null);
                  setDeleteConfirmation('');
                })}
              >
                Confirmar exclusão
              </button>
              <button disabled={busy} onClick={() => setDeleteTarget(null)}>Cancelar</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
