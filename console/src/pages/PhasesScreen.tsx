import { useCallback, useEffect, useState, type FormEvent } from 'react';
import { Link, useParams } from 'react-router-dom';
import { ArrowUp, Eye, EyeOff, Heart, Link2, ListChecks, Pencil, Plus, Sparkles, Trash2 } from 'lucide-react';

import {
  createPhase, createWrapUp, deletePhase, getPhases, publishPhase, reorderPhases, unpublishPhase,
  type EditablePhaseType, type Phase,
} from '../api/console-api';
import EmptyState from '../components/EmptyState';
import PageHeader from '../components/PageHeader';
import { moveUp } from '../lib/move-up';
import { Alert } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Button, buttonVariants } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import {
  Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';

export default function PhasesScreen({ phaseType = 'pre-trip' }: { phaseType?: EditablePhaseType }) {
  const { tripUuid = '' } = useParams();
  const isWrapUp = phaseType === 'post-trip';
  const editorQuery = isWrapUp ? '?type=post-trip' : '';
  const [phases, setPhases] = useState<Phase[]>([]);
  const [loaded, setLoaded] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [creating, setCreating] = useState(false);
  const [newTitle, setNewTitle] = useState('');
  const [newDescription, setNewDescription] = useState('');
  const [deleteTarget, setDeleteTarget] = useState<Phase | null>(null);
  const [deleteConfirmation, setDeleteConfirmation] = useState('');

  const reload = useCallback(async () => {
    const data = await getPhases(tripUuid, phaseType);
    setPhases(data.phases ?? []);
    setLoaded(true);
  }, [tripUuid, phaseType]);

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
    }, phaseType));
    setNewTitle('');
    setNewDescription('');
    setCreating(false);
  };

  const closeDelete = () => {
    setDeleteTarget(null);
    setDeleteConfirmation('');
  };

  const hasPublished = phases.some(phase => phase.is_visible);
  const showTemplate = isWrapUp && loaded && phases.length === 0;

  return (
    <div>
      <PageHeader
        title={isWrapUp ? 'Trip Wrap-up' : 'Fases'}
        description={isWrapUp
          ? 'Fase pós-viagem: aparece no fim da jornada e vira a etapa atual no último dia da viagem. Ajuste textos e links (feedback, playlist, fotos) antes de publicar.'
          : 'Etapas que o viajante completa antes da viagem. Só fases publicadas aparecem no app.'}
        actions={
          <>
            {showTemplate && (
              <Button disabled={busy} onClick={() => void act(() => createWrapUp(tripUuid))}>
                <Sparkles className="h-4 w-4" />
                Criar com modelo padrão
              </Button>
            )}
            <Button variant={showTemplate ? 'outline' : 'default'} onClick={() => setCreating(true)}>
              <Plus className="h-4 w-4" />
              Nova fase
            </Button>
          </>
        }
      />

      {!isWrapUp && (
        <Alert variant="warning" className="mb-4">
          Não importe esta viagem pela planilha depois de editá-la aqui. O import legado pode
          substituir fases, checklist e links.
        </Alert>
      )}
      {hasPublished && (
        <p className="mb-3 text-sm text-muted-foreground">
          Despublique todas as fases antes de alterar a ordem.
        </p>
      )}
      {error && <Alert variant="destructive" className="mb-4">{error}</Alert>}

      {loaded && phases.length === 0 ? (
        <EmptyState icon={isWrapUp ? Heart : ListChecks} title={isWrapUp ? 'Nenhum Trip Wrap-up ainda' : 'Nenhuma fase ainda'}>
          {isWrapUp
            ? 'Use “Criar com modelo padrão” para começar com as ações sugeridas e depois ajuste para esta viagem.'
            : 'Crie a primeira fase com “Nova fase”.'}
        </EmptyState>
      ) : (
        <ul className="space-y-2">
          {phases.map((phase, index) => (
            <li key={phase.id}>
              <Card>
                <CardContent className="flex flex-wrap items-center gap-3 p-4">
                  <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-accent text-sm font-semibold text-accent-foreground">
                    {index + 1}
                  </span>
                  <div className="min-w-0 flex-1">
                    {phase.is_visible ? (
                      <span className="font-medium">{phase.title}</span>
                    ) : (
                      <Link
                        to={`/trips/${tripUuid}/fases/${phase.id}${editorQuery}`}
                        className="font-medium hover:text-primary hover:underline"
                      >
                        {phase.title}
                      </Link>
                    )}
                    <p className="mt-0.5 flex items-center gap-3 text-sm text-muted-foreground">
                      <span className="flex items-center gap-1"><ListChecks className="h-3.5 w-3.5" />{phase.checklist.length} itens</span>
                      <span className="flex items-center gap-1"><Link2 className="h-3.5 w-3.5" />{phase.links.length} links</span>
                    </p>
                  </div>
                  <Badge variant={phase.is_visible ? 'success' : 'warning'}>
                    {phase.is_visible ? 'Publicada' : 'Rascunho'}
                  </Badge>
                  <div className="flex items-center gap-1">
                    {!phase.is_visible && (
                      <Link
                        to={`/trips/${tripUuid}/fases/${phase.id}${editorQuery}`}
                        aria-label={`Editar ${phase.title}`}
                        className={buttonVariants({ variant: 'ghost', size: 'sm' })}
                      >
                        <Pencil className="h-4 w-4" />
                      </Link>
                    )}
                    <Button
                      variant="ghost" size="sm"
                      disabled={busy || hasPublished || index === 0}
                      onClick={() => {
                        const reordered = moveUp(phases, index);
                        setPhases(reordered);
                        void act(() => reorderPhases(tripUuid, reordered.map(item => item.id)));
                      }}
                    >
                      <ArrowUp className="h-4 w-4" />
                      Subir
                    </Button>
                    <Button
                      variant="outline" size="sm"
                      disabled={busy}
                      onClick={() => void act(() => (
                        phase.is_visible ? unpublishPhase(phase.id) : publishPhase(phase.id)
                      ))}
                    >
                      {phase.is_visible ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                      {phase.is_visible ? 'Despublicar' : 'Publicar'}
                    </Button>
                    {!phase.is_visible && (
                      <Button
                        variant="ghost" size="sm"
                        className="text-destructive hover:bg-destructive/10 hover:text-destructive"
                        disabled={busy}
                        onClick={() => {
                          setDeleteTarget(phase);
                          setDeleteConfirmation('');
                        }}
                      >
                        <Trash2 className="h-4 w-4" />
                        Excluir
                      </Button>
                    )}
                  </div>
                </CardContent>
              </Card>
            </li>
          ))}
        </ul>
      )}

      <Dialog open={creating} onOpenChange={open => !busy && setCreating(open)}>
        <DialogContent>
          <form onSubmit={submitCreate} className="space-y-4">
            <DialogHeader>
              <DialogTitle>{isWrapUp ? 'Nova fase de Wrap-up' : 'Nova fase'}</DialogTitle>
              <DialogDescription>
                A fase é criada como rascunho. Depois você completa checklist e links e publica.
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-2">
              <Label htmlFor="new-phase-title">Título da fase</Label>
              <Input
                id="new-phase-title" value={newTitle} disabled={busy}
                onChange={event => setNewTitle(event.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="new-phase-description">Descrição curta da fase</Label>
              <Input
                id="new-phase-description" value={newDescription} disabled={busy}
                onChange={event => setNewDescription(event.target.value)}
              />
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" disabled={busy} onClick={() => setCreating(false)}>
                Cancelar
              </Button>
              <Button type="submit" disabled={busy || !newTitle.trim() || !newDescription.trim()}>
                {busy ? 'Criando…' : 'Criar fase'}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      <Dialog open={deleteTarget !== null} onOpenChange={open => !open && !busy && closeDelete()}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Excluir {deleteTarget?.title}?</DialogTitle>
            <DialogDescription>
              Isso apaga a fase, o checklist e os links. Digite o título da fase para confirmar.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-2">
            <Label htmlFor="delete-confirmation">Digite o título da fase</Label>
            <Input
              id="delete-confirmation" value={deleteConfirmation} disabled={busy}
              onChange={event => setDeleteConfirmation(event.target.value)}
            />
          </div>
          <DialogFooter>
            <Button variant="outline" disabled={busy} onClick={closeDelete}>Cancelar</Button>
            <Button
              variant="destructive"
              disabled={busy || deleteConfirmation !== deleteTarget?.title}
              onClick={() => {
                if (!deleteTarget) return;
                void act(() => deletePhase(deleteTarget.id)).then(closeDelete);
              }}
            >
              Confirmar exclusão
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
