import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';

import { listTrips, PRE_DEPARTURE_LINK, type Trip } from '../api/console-api';
import { useAuth } from '../auth/auth-context';
import { Alert } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Button, buttonVariants } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';

const DIA_MS = 24 * 60 * 60 * 1000;

/** Dias inteiros entre hoje e uma data ISO. Negativo quando já passou. */
function diasAte(iso: string | null): number | null {
  if (!iso) return null;
  const alvo = new Date(`${iso}T00:00:00`);
  if (Number.isNaN(alvo.getTime())) return null;
  const hoje = new Date();
  hoje.setHours(0, 0, 0, 0);
  return Math.round((alvo.getTime() - hoje.getTime()) / DIA_MS);
}

/** "5–12 out" quando no mesmo mês, "28 nov – 3 dez" quando cruza. */
function periodo(inicio: string | null, fim: string | null): string {
  if (!inicio) return '';
  const de = new Date(`${inicio}T00:00:00`);
  const ate = fim ? new Date(`${fim}T00:00:00`) : null;
  const mes = (d: Date) => d.toLocaleDateString('pt-BR', { month: 'short' }).replace('.', '');
  if (!ate) return `${de.getDate()} ${mes(de)}`;
  return de.getMonth() === ate.getMonth()
    ? `${de.getDate()}–${ate.getDate()} ${mes(ate)}`
    : `${de.getDate()} ${mes(de)} – ${ate.getDate()} ${mes(ate)}`;
}

function quando(trip: Trip): string | null {
  const dias = diasAte(trip.start_date);
  if (dias === null) return null;
  if (dias < 0) return null;
  if (dias === 0) return 'começa hoje';
  if (dias === 1) return 'em 1 dia';
  return `em ${dias} dias`;
}

const GRUPOS = [
  {
    titulo: 'Acontecendo agora',
    inclui: (t: Trip) => (diasAte(t.start_date) ?? 1) <= 0,
  },
  {
    titulo: 'Próximas',
    inclui: (t: Trip) => {
      const dias = diasAte(t.start_date);
      return dias !== null && dias > 0 && dias <= 60;
    },
  },
  {
    titulo: 'Mais adiante',
    inclui: (t: Trip) => (diasAte(t.start_date) ?? 0) > 60,
  },
];

export default function TripsScreen() {
  const { logout, user } = useAuth();
  const [trips, setTrips] = useState<Trip[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    listTrips()
      .then(data => setTrips(data.trips))
      .catch(err => setError((err as Error).message));
  }, []);

  const copyLink = async () => {
    await navigator.clipboard.writeText(PRE_DEPARTURE_LINK);
    setCopied(true);
  };

  const grupos = GRUPOS
    .map(g => ({ ...g, itens: trips.filter(g.inclui) }))
    .filter(g => g.itens.length > 0);

  return (
    <div className="mx-auto max-w-3xl p-8">
      <header className="mb-8 flex items-center gap-3">
        <img src="/parrot_icon.svg" alt="" className="h-8 w-8" />
        <div className="flex-1">
          <h1 className="text-2xl font-bold tracking-tight">Parrot Trips — Console</h1>
          {user && <p className="text-sm text-muted-foreground">{user.name ?? user.phone}</p>}
        </div>
        <Button variant="outline" size="sm" onClick={logout}>Sair</Button>
      </header>

      <section className="mb-8 rounded-lg border bg-muted/30 p-4">
        <Label htmlFor="pre-departure" className="mb-2 block">
          Link para pré-embarque
        </Label>
        <div className="flex gap-2">
          <Input
            id="pre-departure"
            readOnly
            value={PRE_DEPARTURE_LINK}
            onFocus={e => e.currentTarget.select()}
            className="flex-1 font-mono text-xs"
          />
          <Button variant="outline" size="sm" onClick={copyLink}>Copiar</Button>
          {/* Link de verdade, com a aparência de botão: <button> não pode conter <a>. */}
          <a
            href={PRE_DEPARTURE_LINK}
            target="_blank"
            rel="noreferrer"
            className={buttonVariants({ variant: 'outline', size: 'sm' })}
          >
            Abrir
          </a>
        </div>
        <p className="mt-2 text-xs text-muted-foreground">
          {copied
            ? 'Copiado. Abre direto na seção Pre Departure Information.'
            : 'Abre direto na seção Pre Departure Information, para quem já tem cadastro.'}
        </p>
      </section>

      {error && <Alert variant="destructive" className="mb-4">{error}</Alert>}

      {grupos.map(grupo => (
        <section key={grupo.titulo} className="mb-8">
          <h2 className="mb-2 border-b pb-1 text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
            {grupo.titulo}
          </h2>
          <ul className="divide-y">
            {grupo.itens.map(trip => (
              <li key={trip.trip_uuid}>
                <Link
                  to={`/trips/${trip.trip_uuid}/fases`}
                  className="flex items-baseline gap-3 py-3 transition-colors hover:bg-accent/40"
                >
                  <div className="flex-1">
                    <p className="font-medium text-foreground">{trip.title}</p>
                    <p className="text-sm text-muted-foreground">
                      {[
                        trip.destination,
                        periodo(trip.start_date, trip.end_date),
                        `${trip.traveler_count} viajantes`,
                      ].filter(Boolean).join(' · ')}
                    </p>
                  </div>
                  {trip.mode === 'in-trip' && <Badge>em viagem</Badge>}
                  <span className="text-sm tabular-nums text-muted-foreground">
                    {quando(trip)}
                  </span>
                </Link>
              </li>
            ))}
          </ul>
        </section>
      ))}

      {!error && trips.length === 0 && (
        <p className="rounded-lg border border-dashed p-8 text-center text-muted-foreground">
          Nenhuma viagem ativa.
        </p>
      )}
    </div>
  );
}
