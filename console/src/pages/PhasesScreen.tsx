import { useCallback, useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';

import {
  createPhase, deletePhase, getPhases, publishPhase, reorderPhases, unpublishPhase, type Phase,
} from '../api/console-api';
import { moveUp } from '../lib/move-up';
import { Alert } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';

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
    <div>
      <h1 className="mb-4 text-xl font-bold tracking-tight">Fases pré-trip</h1>
      {error && <Alert variant="destructive" className="mb-4">{error}</Alert>}

      <ul className="mb-6 space-y-2">
        {phases.map((phase, index) => (
          <li key={phase.id}>
            <Card>
              <CardContent className="flex items-center gap-3">
                <div className="flex-1">
                  <Link
                    to={`/trips/${tripUuid}/fases/${phase.id}`}
                    className="font-medium text-foreground hover:text-primary"
                  >
                    {phase.title}
                  </Link>
                  <p className="text-sm text-muted-foreground">
                    {phase.checklist.length} itens · {phase.links.length} links
                  </p>
                </div>

                <Badge variant={phase.is_visible ? 'default' : 'warning'}>
                  {phase.is_visible ? 'Publicada' : 'Rascunho'}
                </Badge>

                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    const reordered = moveUp(phases, index);
                    setPhases(reordered);
                    void act(() => reorderPhases(tripUuid, reordered.map(p => p.id)));
                  }}
                >
                  Subir
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => act(() =>
                    phase.is_visible ? unpublishPhase(phase.id) : publishPhase(phase.id)
                  )}
                >
                  {phase.is_visible ? 'Despublicar' : 'Publicar'}
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  className="text-destructive hover:text-destructive"
                  onClick={() => act(() => deletePhase(phase.id))}
                >
                  Excluir
                </Button>
              </CardContent>
            </Card>
          </li>
        ))}
      </ul>

      <Button
        onClick={() => act(() =>
          createPhase(tripUuid, { title: 'Nova fase', short_description: '' })
        )}
      >
        Nova fase
      </Button>
    </div>
  );
}
