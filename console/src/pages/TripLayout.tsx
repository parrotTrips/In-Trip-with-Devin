import { useEffect, useState } from 'react';
import { Link, NavLink, Outlet, useParams } from 'react-router-dom';
import { ArrowLeft, Calendar } from 'lucide-react';

import { listSections, listTrips, type Trip, type TripSection } from '../api/console-api';
import ConsoleHeader from '../components/ConsoleHeader';
import { formatRange } from '../lib/format-date';
import { sectionIcon } from '../lib/section-icons';
import { Alert } from '@/components/ui/alert';
import { Separator } from '@/components/ui/separator';
import { cn } from '@/lib/utils';

const GROUP_ORDER = ['conteudo', 'pessoas', 'durante', 'retorno'];

export default function TripLayout() {
  const { tripUuid = '' } = useParams();
  const [sections, setSections] = useState<TripSection[]>([]);
  const [trip, setTrip] = useState<Trip | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listSections(tripUuid)
      .then(data => setSections(data.sections))
      .catch(err => setError((err as Error).message));
    // Só para o cabeçalho da barra lateral; a tela funciona sem isso.
    listTrips()
      .then(data => setTrip(data.trips?.find(t => t.trip_uuid === tripUuid) ?? null))
      .catch(() => {});
  }, [tripUuid]);

  const groups = GROUP_ORDER
    .map(group => ({
      group,
      label: sections.find(s => s.group === group)?.group_label ?? '',
      items: sections.filter(s => s.group === group),
    }))
    .filter(g => g.items.length > 0);

  return (
    <div className="min-h-screen bg-muted/30">
      <ConsoleHeader />
      <div className="flex">
        <nav className="sticky top-14 h-[calc(100vh-3.5rem)] w-64 shrink-0 overflow-y-auto border-r bg-background p-4">
          <Link
            to="/"
            className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground"
          >
            <ArrowLeft className="h-4 w-4" />
            Viagens
          </Link>

          <div className="mt-4 px-2">
            <p className="font-semibold leading-tight">{trip?.title ?? tripUuid}</p>
            {trip && (
              <p className="mt-1 flex items-center gap-1.5 text-xs text-muted-foreground">
                <Calendar className="h-3 w-3" />
                {formatRange(trip.start_date, trip.end_date)}
              </p>
            )}
          </div>
          <Separator className="my-4" />

          {error && <Alert variant="destructive" className="mb-4">{error}</Alert>}

          {groups.map(({ group, label, items }) => (
            <div key={group} className="mb-5">
              <h2 className="mb-1 px-2 text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
                {label}
              </h2>
              <ul className="space-y-0.5">
                {items.map(section => {
                  const Icon = sectionIcon(section.key);
                  return (
                    <li key={section.key}>
                      <NavLink
                        to={`/trips/${tripUuid}/${section.key}`}
                        className={({ isActive }) =>
                          cn(
                            'flex items-center gap-2 rounded-md px-2 py-1.5 text-sm transition-colors',
                            isActive
                              ? 'bg-primary font-medium text-primary-foreground'
                              : 'text-foreground hover:bg-accent hover:text-accent-foreground'
                          )
                        }
                      >
                        <Icon className="h-4 w-4 shrink-0 opacity-80" />
                        <span className="flex-1 truncate">{section.label}</span>
                        <span className={cn('text-xs tabular-nums', section.count === 0 ? 'opacity-40' : 'opacity-75')}>
                          {section.count}
                        </span>
                      </NavLink>
                    </li>
                  );
                })}
              </ul>
            </div>
          ))}
        </nav>

        <main className="min-w-0 flex-1 p-8">
          <div className="mx-auto max-w-5xl">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
}
