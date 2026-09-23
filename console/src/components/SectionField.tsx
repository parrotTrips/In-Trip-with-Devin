import type { SectionColumn } from '../api/console-api';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select } from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';

interface Props {
  column: SectionColumn;
  index: number;
  value: unknown;
  onChange: (value: string) => void;
}

/** Desenha um campo conforme o `kind` que o servidor declarou para a coluna. */
export default function SectionField({ column, index, value, onChange }: Props) {
  const id = `${column.key}-${index}`;
  const label = `${column.label} ${index + 1}`;
  const current = String(value ?? '');

  return (
    <div className="flex-1">
      <Label htmlFor={id} className="mb-1 block">
        {column.label}{column.required && <span className="text-destructive"> *</span>}
      </Label>

      {column.kind === 'select' ? (
        <Select id={id} aria-label={label} value={current} onChange={e => onChange(e.target.value)}>
          <option value="">—</option>
          {/* Valor legado fora da lista aparece para não ser perdido ao salvar. */}
          {current && !column.choices.includes(current) && (
            <option value={current}>{current} (valor antigo)</option>
          )}
          {column.choices.map(choice => (
            <option key={choice} value={choice}>{choice}</option>
          ))}
        </Select>
      ) : column.kind === 'textarea' ? (
        <Textarea
          id={id} aria-label={label} value={current} rows={3}
          onChange={e => onChange(e.target.value)}
        />
      ) : (
        <Input
          id={id}
          aria-label={label}
          value={current}
          type={column.kind === 'number' ? 'number' : 'text'}
          inputMode={column.kind === 'number' ? 'decimal' : undefined}
          onChange={e => onChange(e.target.value)}
        />
      )}
    </div>
  );
}
