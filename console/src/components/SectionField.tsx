import type { SectionColumn } from '../api/console-api';

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
  const className = 'w-full rounded border px-2 py-1 text-sm';

  return (
    <div className="flex-1">
      <label htmlFor={id} className="block text-xs text-gray-600">
        {column.label}{column.required && ' *'}
      </label>

      {column.kind === 'select' ? (
        <select
          id={id} aria-label={label} value={current} className={className}
          onChange={e => onChange(e.target.value)}
        >
          <option value="">—</option>
          {/* Valor legado fora da lista aparece para não ser perdido ao salvar. */}
          {current && !column.choices.includes(current) && (
            <option value={current}>{current} (valor antigo)</option>
          )}
          {column.choices.map(choice => (
            <option key={choice} value={choice}>{choice}</option>
          ))}
        </select>
      ) : column.kind === 'textarea' ? (
        <textarea
          id={id} aria-label={label} value={current} rows={3} className={className}
          onChange={e => onChange(e.target.value)}
        />
      ) : (
        <input
          id={id}
          aria-label={label}
          value={current}
          type={column.kind === 'number' ? 'number' : 'text'}
          inputMode={column.kind === 'number' ? 'decimal' : undefined}
          className={className}
          onChange={e => onChange(e.target.value)}
        />
      )}
    </div>
  );
}
