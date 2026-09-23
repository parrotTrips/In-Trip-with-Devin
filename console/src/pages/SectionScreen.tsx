import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';

import { getSection, replaceSection, type SectionColumn, type SectionRows } from '../api/console-api';
import { formatCell } from '../lib/section-columns';
import { moveUp } from '../lib/move-up';
import SectionField from '../components/SectionField';
import { Alert } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from '@/components/ui/table';

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

  if (error && !section) return <Alert variant="destructive">{error}</Alert>;
  if (!section) return <p className="text-muted-foreground">Carregando…</p>;

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
      <h1 className="mb-2 text-xl font-bold tracking-tight">{section.label}</h1>
      <Alert variant={section.editable ? 'info' : 'warning'} className="mb-4">
        {section.editable ? IMMEDIATE_WARNING : section.readonly_note ?? EDITING_NOT_BUILT}
      </Alert>

      {error && <Alert variant="destructive" className="mb-4">{error}</Alert>}

      {!section.editable ? (
        rows.length === 0 ? (
          <p className="rounded-lg border border-dashed p-8 text-center text-muted-foreground">
            Nada cadastrado ainda nesta seção.
          </p>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                {columns.map(column => (
                  <TableHead key={column.key}>{column.label}</TableHead>
                ))}
              </TableRow>
            </TableHeader>
            <TableBody>
              {rows.map((row, index) => (
                <TableRow key={index}>
                  {columns.map(column => (
                    <TableCell key={column.key}>{formatCell(row[column.key])}</TableCell>
                  ))}
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )
      ) : (
        <>
          {rows.length === 0 && (
            <p className="mb-3 rounded-lg border border-dashed p-8 text-center text-muted-foreground">
              Nada cadastrado ainda. Use “Adicionar” para começar.
            </p>
          )}

          <ul className="mb-3 space-y-3">
            {rows.map((row, index) => (
              <li key={index}><Card><CardContent>
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
                    <Button variant="ghost" size="sm"
                            onClick={() => setExpanded(toggle(expanded, index))}>
                      {expanded.has(index) ? 'Menos campos' : `Mais campos (${secondary.length})`}
                    </Button>
                  )}
                  <Button variant="outline" size="sm" onClick={() => setRows(moveUp(rows, index))}>
                    Subir
                  </Button>
                  <Button
                    variant="outline" size="sm"
                    className="text-destructive hover:text-destructive"
                    onClick={() => setRows(rows.filter((_, i) => i !== index))}
                  >
                    Remover
                  </Button>
                </div>
              </CardContent></Card></li>
            ))}
          </ul>

          <div className="flex items-center gap-3">
            <Button
              variant="outline"
              onClick={() => setRows([
                ...rows,
                Object.fromEntries(columns.map(c => [c.key, ''])),
              ])}
            >
              Adicionar
            </Button>
            <Button onClick={save} disabled={saving}>Salvar</Button>
            {status && <span className="text-sm font-medium text-primary">{status}</span>}
          </div>
        </>
      )}
    </div>
  );
}
