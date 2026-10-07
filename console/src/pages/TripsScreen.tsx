import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Calendar, Check, ChevronRight, Link2, Plane, Search, Users } from 'lucide-react';

import { listTrips, PRE_DEPARTURE_LINK, type Trip } from '../api/console-api';
import ConsoleHeader from '../components/ConsoleHeader';
import EmptyState from '../components/EmptyState';
import PageHeader from '../components/PageHeader';
import { formatRange, tripStatus } from '../lib/format-date';
import { Alert } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Skeleton } from '@/components/ui/skeleton';

const STATUS_LABEL = { current: 'Em andamento', upcoming: 'Próxima', past: 'Encerrada', unknown: 'Sem data' };

export default function TripsScreen() {
  const [trips, setTrips] = useState<Trip[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const [query, setQuery] = useState('');

  useEffect(() => {
    listTrips()
      .then(data => setTrips(data.trips ?? []))
      .catch(err => {
        setTrips([]);
        setError((err as Error).message);
      });
  }, []);

  const copyLink = async () => {
    await navigator.clipboard.writeText(PRE_DEPARTURE_LINK);
    setCopied(true);
  };

  const normalized = query.trim().toLowerCase();
  const visible = (trips ?? []).filter(trip => !normalized || trip.title.toLowerCase().includes(normalized));

  return (
    <div className="min-h-screen bg-muted/30">
      <ConsoleHeader />
      <main className="mx-auto max-w-5xl p-6">
        <PageHeader
          title="Viagens"
          description="Escolha uma viagem para editar o conteúdo que aparece no app dos viajantes."
          actions={
            <Button variant="outline" onClick={copyLink}>
              {copied ? <Check className="h-4 w-4" /> : <Link2 className="h-4 w-4" />}
              Copiar link de pré-embarque
            </Button>
          }
        />
        {copied && <p className="-mt-4 mb-4 text-right text-sm text-primary">Copiado</p>}

        <Alert variant="warning" className="mb-6">
          Não importe esta viagem pela planilha depois de editá-la aqui. O import legado pode
          substituir fases, checklist e links.
        </Alert>
        {error && <Alert variant="destructive" className="mb-4">{error}</Alert>}

        <div className="relative mb-4 max-w-sm">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            type="search"
            aria-label="Buscar viagem"
            placeholder="Buscar viagem"
            value={query}
            onChange={event => setQuery(event.target.value)}
            className="pl-9"
          />
        </div>

        {trips === null ? (
          <div className="grid gap-3 sm:grid-cols-2">
            {[0, 1, 2, 3].map(i => <Skeleton key={i} className="h-24 rounded-lg" />)}
          </div>
        ) : visible.length === 0 ? (
          <EmptyState icon={Plane} title="Nenhuma viagem encontrada">
            {normalized ? 'Tente outro nome.' : 'Viagens ativas aparecem aqui automaticamente.'}
          </EmptyState>
        ) : (
          <ul className="grid gap-3 sm:grid-cols-2">
            {visible.map(trip => {
              const status = tripStatus(trip.start_date, trip.end_date);
              return (
                <li key={trip.trip_uuid}>
                  <Link to={`/trips/${trip.trip_uuid}/fases`} className="group block focus:outline-none">
                    <Card className="h-full transition-colors group-hover:border-primary/40 group-focus-visible:ring-2 group-focus-visible:ring-ring">
                      <CardContent className="flex items-start justify-between gap-3 p-4">
                        <div className="min-w-0">
                          <p className="truncate font-medium group-hover:text-primary">{trip.title}</p>
                          <p className="mt-1 flex items-center gap-1.5 text-sm text-muted-foreground">
                            <Calendar className="h-3.5 w-3.5" />
                            {formatRange(trip.start_date, trip.end_date)}
                          </p>
                          <div className="mt-3 flex flex-wrap items-center gap-2">
                            <Badge variant={status === 'current' ? 'success' : 'secondary'}>
                              {STATUS_LABEL[status]}
                            </Badge>
                            {typeof trip.traveler_count === 'number' && (
                              <span className="flex items-center gap-1 text-xs text-muted-foreground">
                                <Users className="h-3.5 w-3.5" />
                                {trip.traveler_count} viajantes
                              </span>
                            )}
                          </div>
                        </div>
                        <ChevronRight className="mt-1 h-4 w-4 shrink-0 text-muted-foreground group-hover:text-primary" />
                      </CardContent>
                    </Card>
                  </Link>
                </li>
              );
            })}
          </ul>
        )}
      </main>
    </div>
  );
}
