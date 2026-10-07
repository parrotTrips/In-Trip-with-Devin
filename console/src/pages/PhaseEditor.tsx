import { useEffect, useState } from 'react';
import { Link, useNavigate, useParams, useSearchParams } from 'react-router-dom';
import { ArrowLeft, ArrowUp, Plus, Trash2 } from 'lucide-react';

import {
  getPhases, savePhaseContent, type ChecklistItem, type EditablePhaseType, type Phase, type PhaseLink,
} from '../api/console-api';
import { moveUp } from '../lib/move-up';
import PageHeader from '../components/PageHeader';
import { Alert } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Checkbox } from '@/components/ui/checkbox';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';

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
  const navigate = useNavigate();
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

  if (!phase && error) return <Alert variant="destructive">{error}</Alert>;
  if (!phase) return <p className="text-muted-foreground">Carregando…</p>;

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

  const disabled = readOnly || busy;
  const backTo = `/trips/${tripUuid}/${phaseType === 'post-trip' ? 'wrap-up' : 'fases'}`;

  return (
    <div className="pb-24">
      <Link to={backTo} className="mb-4 inline-flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground">
        <ArrowLeft className="h-4 w-4" />
        {phaseType === 'post-trip' ? 'Trip Wrap-up' : 'Fases'}
      </Link>
      <PageHeader
        title="Editar fase"
        description={phase.title || 'Sem título'}
        actions={
          <Badge variant={phase.is_visible ? 'success' : 'warning'}>
            {phase.is_visible ? 'Publicada' : 'Rascunho'}
          </Badge>
        }
      />
      {readOnly && (
        <Alert variant="warning" className="mb-4">
          Despublique a fase para editar seu conteúdo.
        </Alert>
      )}
      {error && <Alert variant="destructive" className="mb-4">{error}</Alert>}

      <div className="space-y-4">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Informações</CardTitle>
            <CardDescription>O que o viajante vê no card da fase e ao abri-la.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="title">Título</Label>
              <Input id="title" value={phase.title} disabled={disabled}
                onChange={event => setPhase({ ...phase, title: event.target.value })} />
            </div>
            <div className="space-y-2">
              <Label htmlFor="short">Descrição curta</Label>
              <Input id="short" value={phase.short_description} disabled={disabled}
                onChange={event => setPhase({ ...phase, short_description: event.target.value })} />
            </div>
            <div className="space-y-2">
              <Label htmlFor="detailed">Descrição completa</Label>
              <Textarea id="detailed" rows={5} value={phase.detailed_description ?? ''} disabled={disabled}
                onChange={event => setPhase({ ...phase, detailed_description: event.target.value })} />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Período</CardTitle>
            <CardDescription>Opcional. Ajuda a ordenar o que o viajante deve fazer e quando.</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="starts_at">Início</Label>
              <Input id="starts_at" type="datetime-local" value={startsAt} disabled={disabled}
                onChange={event => setStartsAt(event.target.value)} />
            </div>
            <div className="space-y-2">
              <Label htmlFor="ends_at">Fim</Label>
              <Input id="ends_at" type="datetime-local" value={endsAt} disabled={disabled}
                onChange={event => setEndsAt(event.target.value)} />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Checklist</CardTitle>
            <CardDescription>
              A fase fica concluída quando o viajante marca todos os itens obrigatórios
              (ou todos os itens, se nenhum for obrigatório).
            </CardDescription>
          </CardHeader>
          <CardContent>
            {checklist.length === 0 ? (
              <p className="mb-3 text-sm text-muted-foreground">Nenhum item ainda.</p>
            ) : (
              <ul className="mb-3 space-y-2">
                {checklist.map((item, index) => (
                  <li key={item.id} className="flex items-center gap-2">
                    <span className="w-5 text-right text-xs tabular-nums text-muted-foreground">{index + 1}</span>
                    <Input aria-label={`Item ${index + 1}`} value={item.label} disabled={disabled}
                      onChange={event => setChecklist(checklist.map(
                        (current, currentIndex) => currentIndex === index
                          ? { ...current, label: event.target.value } : current
                      ))} />
                    <label className="flex shrink-0 items-center gap-1.5 text-sm text-muted-foreground">
                      <Checkbox
                        aria-label={`Item ${index + 1} obrigatório`}
                        checked={item.is_required}
                        disabled={disabled}
                        onCheckedChange={checked => setChecklist(checklist.map(
                          (current, currentIndex) => currentIndex === index
                            ? { ...current, is_required: checked === true } : current
                        ))}
                      />
                      Obrigatório
                    </label>
                    <Button variant="ghost" size="icon" aria-label="Subir" disabled={disabled || index === 0}
                      onClick={() => setChecklist(moveUp(checklist, index))}>
                      <ArrowUp className="h-4 w-4" />
                    </Button>
                    <Button variant="ghost" size="icon" aria-label="Remover"
                      className="text-destructive hover:bg-destructive/10 hover:text-destructive"
                      disabled={disabled}
                      onClick={() => setChecklist(checklist.filter((_, current) => current !== index))}>
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </li>
                ))}
              </ul>
            )}
            <Button variant="outline" size="sm" disabled={disabled} onClick={() => setChecklist([
              ...checklist,
              { id: `new-${crypto.randomUUID()}`, label: '', is_required: false, sort_order: checklist.length },
            ])}>
              <Plus className="h-4 w-4" />
              Adicionar item
            </Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Links</CardTitle>
            <CardDescription>Aparecem como botões em “Useful Links”. Use endereços com https://.</CardDescription>
          </CardHeader>
          <CardContent>
            {links.length === 0 ? (
              <p className="mb-3 text-sm text-muted-foreground">Nenhum link ainda.</p>
            ) : (
              <ul className="mb-3 space-y-2">
                {links.map((link, index) => (
                  <li key={link.id} className="flex items-center gap-2">
                    <Input aria-label={`Link ${index + 1} rótulo`} placeholder="Texto do botão"
                      className="sm:max-w-[16rem]" value={link.label}
                      disabled={disabled} onChange={event => setLinks(links.map(
                        (current, currentIndex) => currentIndex === index
                          ? { ...current, label: event.target.value } : current
                      ))} />
                    <Input aria-label={`Link ${index + 1} url`} placeholder="https://" value={link.url}
                      disabled={disabled} onChange={event => setLinks(links.map(
                        (current, currentIndex) => currentIndex === index
                          ? { ...current, url: event.target.value } : current
                      ))} />
                    <Button variant="ghost" size="icon" aria-label="Remover"
                      className="text-destructive hover:bg-destructive/10 hover:text-destructive"
                      disabled={disabled}
                      onClick={() => setLinks(links.filter((_, current) => current !== index))}>
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </li>
                ))}
              </ul>
            )}
            <Button variant="outline" size="sm" disabled={disabled} onClick={() => setLinks([
              ...links,
              { id: `new-${crypto.randomUUID()}`, label: '', url: '', sort_order: links.length },
            ])}>
              <Plus className="h-4 w-4" />
              Adicionar link
            </Button>
          </CardContent>
        </Card>
      </div>

      <div className="fixed bottom-0 left-64 right-0 z-20 border-t bg-background/95 backdrop-blur">
        <div className="mx-auto flex max-w-5xl items-center justify-end gap-3 px-8 py-3">
          {status && <span className="text-sm font-medium text-primary">{status}</span>}
          <Button variant="outline" onClick={() => navigate(backTo)} disabled={busy}>
            Voltar
          </Button>
          <Button disabled={disabled} onClick={() => void save()}>
            {busy ? 'Salvando…' : 'Salvar'}
          </Button>
        </div>
      </div>
    </div>
  );
}
