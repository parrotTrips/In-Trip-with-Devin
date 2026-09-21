import { useCallback, useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';

import {
  createPhase, deletePhase, getPhases, publishPhase, reorderPhases, unpublishPhase, type Phase,
} from '../api/console-api';
import { moveUp } from '../lib/move-up';

export default function PhasesScreen() {
  const { tripUuid = '' } = useParams();
  const [phases, setPhases] = useState<Phase[]>([]);
  const [error, setError] = useState<string | null>(null);

  const reload = useCallback(async () => {
    try {
      setPhases((await getPhases(tripUuid)).phases);
    } catch (err) {
      setError((err as Error).message);
    }
  }, [tripUuid]);

  useEffect(() => { void reload(); }, [reload]);

  const act = async (action: () => Promise<unknown>) => {
    setError(null);
    try {
      await action();
      await reload();
    } catch (err) {
      setError((err as Error).message);
    }
  };

  return (
    <div className="max-w-2xl mx-auto p-6">
      <Link to="/" className="text-sm underline">← Viagens</Link>
      <h1 className="text-xl font-bold my-4">Fases</h1>
      {error && <p className="text-red-600 text-sm mb-3">{error}</p>}

      <ul className="space-y-2 mb-6">
        {phases.map((phase, index) => (
          <li key={phase.id} className="border rounded p-3 flex items-center gap-3">
            <div className="flex-1">
              <Link to={`/trips/${tripUuid}/phases/${phase.id}`} className="font-medium underline">
                {phase.title}
              </Link>
              <p className="text-sm text-gray-600">
                {phase.checklist.length} itens · {phase.links.length} links
              </p>
            </div>
            <span className={phase.is_visible ? 'text-green-700 text-sm' : 'text-amber-700 text-sm'}>
              {phase.is_visible ? 'Publicada' : 'Rascunho'}
            </span>
            <button
              className="border rounded px-2 py-1 text-sm"
              onClick={() => {
                const reordered = moveUp(phases, index);
                setPhases(reordered);
                void act(() => reorderPhases(tripUuid, reordered.map(p => p.id)));
              }}
            >
              Subir
            </button>
            <button
              className="border rounded px-2 py-1 text-sm"
              onClick={() => act(() =>
                phase.is_visible ? unpublishPhase(phase.id) : publishPhase(phase.id)
              )}
            >
              {phase.is_visible ? 'Despublicar' : 'Publicar'}
            </button>
            <button
              className="border rounded px-2 py-1 text-sm text-red-700"
              onClick={() => act(() => deletePhase(phase.id))}
            >
              Excluir
            </button>
          </li>
        ))}
      </ul>

      <button
        className="border rounded px-3 py-2"
        onClick={() => act(() =>
          createPhase(tripUuid, { title: 'Nova fase', short_description: '' })
        )}
      >
        Nova fase
      </button>
    </div>
  );
}
