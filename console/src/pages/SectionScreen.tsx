import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';

import { getSection, replaceSection, type SectionColumn, type SectionRows } from '../api/console-api';
import { formatCell } from '../lib/section-columns';
import { moveUp } from '../lib/move-up';
import SectionField from '../components/SectionField';
import EmptyState from '../components/EmptyState';
import PageHeader from '../components/PageHeader';
import { ArrowUp, ChevronDown, ChevronUp, Inbox, Plus, Save, Trash2 } from 'lucide-react';
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

  const addRow = () => setRows([
    ...rows,
    Object.fromEntries(columns.map(c => [c.key, ''])),
  ]);

  return (
    <div>
      <PageHeader
        title={section.label}
        actions={section.editable && (
          <>
            {status && <span className="text-sm font-medium text-primary">{status}</span>}
            <Button variant="outline" onClick={addRow}>
              <Plus className="h-4 w-4" />
              Adicionar
            </Button>
            <Button onClick={save} disabled={saving}>
              <Save className="h-4 w-4" />
              Salvar
            </Button>
          </>
        )}
      />
      <Alert variant={section.editable ? 'info' : 'warning'} className="mb-4">
        {section.editable ? IMMEDIATE_WARNING : section.readonly_note ?? EDITING_NOT_BUILT}
      </Alert>

      {error && <Alert variant="destructive" className="mb-4">{error}</Alert>}

      {!section.editable ? (
        rows.length === 0 ? (
          <EmptyState icon={Inbox} title="Nada cadastrado ainda nesta seção." />
        ) : (
          <Card className="overflow-hidden">
            <Table>
              <TableHeader>
                <TableRow className="bg-muted/50">
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
          </Card>
        )
      ) : (
        <>
          {rows.length === 0 && (
            <EmptyState icon={Inbox} title="Nada cadastrado ainda.">
              Use “Adicionar” para começar.
            </EmptyState>
          )}

          <ul className="space-y-3">
            {rows.map((row, index) => (
              <li key={index}><Card><CardContent>
                <div className="mb-3 flex items-start gap-3">
                  <span className="mt-7 flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-accent text-xs font-semibold text-accent-foreground">
                    {index + 1}
                  </span>
                  <div className="flex flex-1 flex-wrap gap-3">
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
                </div>

                {isCard && expanded.has(index) && (
                  <div className="mb-3 grid gap-3 pl-9 sm:grid-cols-2">
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

                <div className="flex flex-wrap gap-1 pl-9">
                  {isCard && (
                    <Button variant="ghost" size="sm"
                            onClick={() => setExpanded(toggle(expanded, index))}>
                      {expanded.has(index) ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                      {expanded.has(index) ? 'Menos campos' : `Mais campos (${secondary.length})`}
                    </Button>
                  )}
                  <Button variant="ghost" size="sm" onClick={() => setRows(moveUp(rows, index))}>
                    <ArrowUp className="h-4 w-4" />
                    Subir
                  </Button>
                  <Button
                    variant="ghost" size="sm"
                    className="text-destructive hover:bg-destructive/10 hover:text-destructive"
                    onClick={() => setRows(rows.filter((_, i) => i !== index))}
                  >
                    <Trash2 className="h-4 w-4" />
                    Remover
                  </Button>
                </div>
              </CardContent></Card></li>
            ))}
          </ul>
        </>
      )}
    </div>
  );
}
