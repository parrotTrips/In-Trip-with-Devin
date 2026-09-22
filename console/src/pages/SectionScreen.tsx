import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';

import { getSection, replaceSection, type SectionColumn, type SectionRows } from '../api/console-api';
import { formatCell } from '../lib/section-columns';
import { moveUp } from '../lib/move-up';
import SectionField from '../components/SectionField';

const EDITING_NOT_BUILT =
  'Somente leitura por enquanto — a edição desta seção ainda não foi construída.';
const IMMEDIATE_WARNING =
  'Alterações aqui aparecem no app dos viajantes assim que você salvar.';

type Row = Record<string, unknown>;

function toggle(set: Set<number>, value: number): Set<number> {
  const next = new Set(set);
  if (!next.delete(value)) next.add(value);
  return next;
}

export default function SectionScreen() {
  const { tripUuid = '', sectionKey = '' } = useParams();
  const [section, setSection] = useState<SectionRows | null>(null);
  const [rows, setRows] = useState<Row[]>([]);
  const [status, setStatus] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [expanded, setExpanded] = useState<Set<number>>(new Set());

  useEffect(() => {
    setSection(null);
    setError(null);
    setStatus(null);
    getSection(tripUuid, sectionKey)
      .then(data => {
        setSection(data);
        setRows(data.rows);
      })
      .catch(err => setError((err as Error).message));
  }, [tripUuid, sectionKey]);

  if (error && !section) return <p className="text-red-600">{error}</p>;
  if (!section) return <p>Carregando…</p>;

  // Colunas vêm do servidor; sem elas, as chaves da primeira linha servem de guia.
  const columns: SectionColumn[] = section.columns?.length
    ? section.columns
    : Object.keys(rows[0] ?? {}).map(key => ({
        key, label: key, required: false, kind: 'text' as const, choices: [],
      }));

  // Até quatro campos cabem numa linha (é o caso das seções simples); daí em
  // diante vira cartão, com os dois principais à vista e o resto sob demanda.
  const isCard = columns.length > 4;
  const primary = isCard ? columns.slice(0, 2) : columns;
  const secondary = isCard ? columns.slice(2) : [];

  const save = async () => {
    setStatus(null);
    setError(null);

    for (const [index, row] of rows.entries()) {
      for (const column of columns) {
        if (column.required && !String(row[column.key] ?? '').trim()) {
          setError(`Item ${index + 1}: ${column.label} é obrigatório.`);
          return;
        }
      }
    }

    setSaving(true);
    try {
      await replaceSection(tripUuid, sectionKey, rows);
      setStatus('Salvo');
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div>
      <h1 className="mb-1 text-xl font-bold">{section.label}</h1>
      <p className={`mb-4 text-sm ${section.editable ? 'text-blue-700' : 'text-amber-700'}`}>
        {section.editable
          ? IMMEDIATE_WARNING
          : section.readonly_note ?? EDITING_NOT_BUILT}
      </p>

      {error && <p className="mb-3 text-sm text-red-600">{error}</p>}

      {!section.editable ? (
        rows.length === 0 ? (
          <p className="rounded border border-dashed p-6 text-center text-gray-500">
            Nada cadastrado ainda nesta seção.
          </p>
        ) : (
          <table className="w-full border-collapse text-sm">
            <thead>
              <tr className="border-b text-left">
                {columns.map(column => (
                  <th key={column.key} className="py-2 pr-4 font-semibold">{column.label}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((row, index) => (
                <tr key={index} className="border-b align-top">
                  {columns.map(column => (
                    <td key={column.key} className="py-2 pr-4">{formatCell(row[column.key])}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        )
      ) : (
        <>
          {rows.length === 0 && (
            <p className="mb-3 rounded border border-dashed p-6 text-center text-gray-500">
              Nada cadastrado ainda. Use “Adicionar” para começar.
            </p>
          )}

          <ul className="mb-3 space-y-3">
            {rows.map((row, index) => (
              <li key={index} className="rounded border p-3">
                <div className="mb-2 flex gap-2">
                  {primary.map(column => (
                    <SectionField
                      key={column.key} column={column} index={index}
                      value={row[column.key]}
                      onChange={value => setRows(rows.map(
                        (r, i) => i === index ? { ...r, [column.key]: value } : r
                      ))}
                    />
                  ))}
                </div>

                {isCard && expanded.has(index) && (
                  <div className="mb-2 grid grid-cols-2 gap-2">
                    {secondary.map(column => (
                      <SectionField
                        key={column.key} column={column} index={index}
                        value={row[column.key]}
                        onChange={value => setRows(rows.map(
                          (r, i) => i === index ? { ...r, [column.key]: value } : r
                        ))}
                      />
                    ))}
                  </div>
                )}

                <div className="flex gap-2">
                  {isCard && (
                    <button
                      className="rounded border px-2 py-1 text-xs"
                      onClick={() => setExpanded(toggle(expanded, index))}
                    >
                      {expanded.has(index) ? 'Menos campos' : `Mais campos (${secondary.length})`}
                    </button>
                  )}
                  <button
                    className="rounded border px-2 py-1 text-xs"
                    onClick={() => setRows(moveUp(rows, index))}
                  >
                    Subir
                  </button>
                  <button
                    className="rounded border px-2 py-1 text-xs text-red-700"
                    onClick={() => setRows(rows.filter((_, i) => i !== index))}
                  >
                    Remover
                  </button>
                </div>
              </li>
            ))}
          </ul>

          <div className="flex items-center gap-3">
            <button
              className="rounded border px-3 py-1 text-sm"
              onClick={() => setRows([
                ...rows,
                Object.fromEntries(columns.map(c => [c.key, ''])),
              ])}
            >
              Adicionar
            </button>
            <button
              className="rounded bg-black px-4 py-2 text-white disabled:opacity-50"
              onClick={save}
              disabled={saving}
            >
              Salvar
            </button>
            {status && <span className="text-sm text-green-700">{status}</span>}
          </div>
        </>
      )}
    </div>
  );
}
