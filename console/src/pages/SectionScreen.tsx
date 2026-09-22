import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';

import { getSection, type SectionRows } from '../api/console-api';
import { formatCell, SECTION_COLUMNS } from '../lib/section-columns';

const EDITING_NOT_BUILT =
  'Somente leitura por enquanto — a edição desta seção ainda não foi construída.';

export default function SectionScreen() {
  const { tripUuid = '', sectionKey = '' } = useParams();
  const [section, setSection] = useState<SectionRows | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setSection(null);
    setError(null);
    getSection(tripUuid, sectionKey)
      .then(setSection)
      .catch(err => setError((err as Error).message));
  }, [tripUuid, sectionKey]);

  if (error) return <p className="text-red-600">{error}</p>;
  if (!section) return <p>Carregando…</p>;

  // Colunas configuradas quando existem; senão, as chaves da primeira linha —
  // assim uma seção nova no servidor já aparece antes de ganhar configuração.
  const configured = SECTION_COLUMNS[section.key];
  const columns = configured
    ? Object.entries(configured)
    : Object.keys(section.rows[0] ?? {}).map(key => [key, key] as [string, string]);

  return (
    <div>
      <h1 className="mb-1 text-xl font-bold">{section.label}</h1>
      <p className="mb-4 text-sm text-amber-700">
        {section.readonly_note ?? EDITING_NOT_BUILT}
      </p>

      {section.rows.length === 0 ? (
        <p className="rounded border border-dashed p-6 text-center text-gray-500">
          Nada cadastrado ainda nesta seção.
        </p>
      ) : (
        <table className="w-full border-collapse text-sm">
          <thead>
            <tr className="border-b text-left">
              {columns.map(([key, label]) => (
                <th key={key} className="py-2 pr-4 font-semibold">{label}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {section.rows.map((row, index) => (
              <tr key={index} className="border-b align-top">
                {columns.map(([key]) => (
                  <td key={key} className="py-2 pr-4">{formatCell(row[key])}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
