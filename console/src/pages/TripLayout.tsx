import { useEffect, useState } from 'react';
import { Link, NavLink, Outlet, useParams } from 'react-router-dom';

import { listSections, type TripSection } from '../api/console-api';
import { Alert } from '@/components/ui/alert';
import { cn } from '@/lib/utils';

const GROUP_ORDER = ['conteudo', 'pessoas', 'durante', 'retorno'];

export default function TripLayout() {
  const { tripUuid = '' } = useParams();
  const [sections, setSections] = useState<TripSection[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listSections(tripUuid)
      .then(data => setSections(data.sections))
      .catch(err => setError((err as Error).message));
  }, [tripUuid]);

  const groups = GROUP_ORDER
    .map(group => ({
      group,
      label: sections.find(s => s.group === group)?.group_label ?? '',
      items: sections.filter(s => s.group === group),
    }))
    .filter(g => g.items.length > 0);

  return (
    <div className="flex min-h-screen">
      <nav className="w-64 shrink-0 border-r bg-muted/30 p-4">
        <Link
          to="/"
          className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground"
        >
          <img src="/parrot_icon.svg" alt="" className="h-5 w-5" />
          Viagens
        </Link>

        {error && <Alert variant="destructive" className="mt-4">{error}</Alert>}

        {groups.map(({ group, label, items }) => (
          <div key={group} className="mt-5">
            <h2 className="mb-1 px-2 text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
              {label}
            </h2>
            <ul>
              {items.map(section => (
                <li key={section.key}>
                  <NavLink
                    to={`/trips/${tripUuid}/${section.key}`}
                    className={({ isActive }) =>
                      cn(
                        'flex items-center justify-between rounded-md px-2 py-1.5 text-sm transition-colors',
                        isActive
                          ? 'bg-primary font-medium text-primary-foreground'
                          : 'text-foreground hover:bg-accent hover:text-accent-foreground'
                      )
                    }
                  >
                    <span>{section.label}</span>
                    <span className={cn('tabular-nums', section.count === 0 ? 'opacity-40' : 'opacity-75')}>
                      {section.count}
                    </span>
                  </NavLink>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </nav>

      <main className="flex-1 p-8">
        <Outlet />
      </main>
    </div>
  );
}
