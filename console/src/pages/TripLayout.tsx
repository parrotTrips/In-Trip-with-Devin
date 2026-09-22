import { useEffect, useState } from 'react';
import { Link, NavLink, Outlet, useParams } from 'react-router-dom';

import { listSections, type TripSection } from '../api/console-api';

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
      <nav className="w-64 shrink-0 border-r bg-gray-50 p-4">
        <Link to="/" className="text-sm underline">← Viagens</Link>

        {error && <p className="mt-4 text-sm text-red-600">{error}</p>}

        {groups.map(({ group, label, items }) => (
          <div key={group} className="mt-5">
            <h2 className="mb-1 text-xs font-semibold uppercase tracking-wide text-gray-500">
              {label}
            </h2>
            <ul>
              {items.map(section => (
                <li key={section.key}>
                  <NavLink
                    to={`/trips/${tripUuid}/${section.key}`}
                    className={({ isActive }) =>
                      `flex items-center justify-between rounded px-2 py-1 text-sm ${
                        isActive ? 'bg-black text-white' : 'hover:bg-gray-200'
                      }`
                    }
                  >
                    <span>{section.label}</span>
                    <span className={section.count === 0 ? 'opacity-40' : 'opacity-70'}>
                      {section.count}
                    </span>
                  </NavLink>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </nav>

      <main className="flex-1 p-6">
        <Outlet />
      </main>
    </div>
  );
}
