import { memo } from 'react';

const VERDICT_MAP = {
  matched:     { label: 'MATCHED',     bg: 'bg-emerald/10 text-emerald border border-emerald/30' },
  discrepancy: { label: 'DISCREPANCY', bg: 'bg-amber/10 text-amber border border-amber/30' },
  failed:      { label: 'FAILED',      bg: 'bg-sev-critical/10 text-sev-critical border border-sev-critical/30' },
};

const COL_LABELS = { po: 'Purchase Order', gr: 'Goods Receipt', invoice: 'Invoice' };
const COLS = ['po', 'gr', 'invoice'];

const fmtIDR = new Intl.NumberFormat('id-ID', {
  style: 'currency',
  currency: 'IDR',
  maximumFractionDigits: 0,
});

function formatValue(key, value) {
  if (value == null) return '—';
  if (typeof value === 'number' && /amount|price|total/i.test(key)) return fmtIDR.format(value);
  return String(value);
}

/**
 * VerdictBanner — verdict strip above the grid.
 */
function VerdictBanner({ status }) {
  const key   = (status ?? '').toLowerCase();
  const { label, bg } = VERDICT_MAP[key] ?? { label: status, bg: 'bg-canvas border border-[var(--border-light)] text-ink' };
  return (
    <div className={`px-4 py-2 text-sm font-semibold uppercase tracking-wider ${bg}`}>
      {label}
    </div>
  );
}

/**
 * MatchGrid — 3-column PO / GR / Invoice comparison.
 * Props:
 *   po          {Object}   PO document fields
 *   gr          {Object}   GR document fields
 *   invoice     {Object}   Invoice document fields
 *   differences {string[]} list of field keys that have discrepancies
 *   status      {'matched'|'discrepancy'|'failed'}
 */
function MatchGrid({ po = {}, gr = {}, invoice = {}, differences = [], status }) {
  const docs = { po, gr, invoice };

  // Build a union of all field keys (exclude internal keys)
  const allKeys = [
    ...new Set(COLS.flatMap((col) => Object.keys(docs[col] ?? {}))),
  ].filter((k) => k !== 'id');

  if (!allKeys.length) {
    return (
      <div className="border border-[var(--border-light)] px-6 py-12 text-center text-sm text-[var(--color-text-mute)]">
        Tidak ada data dokumen.
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-0 border border-[var(--border-light)] overflow-hidden">
      {status && <VerdictBanner status={status} />}

      {/* Column headers */}
      <div className="grid grid-cols-3 border-b border-[var(--border-light)] bg-canvas">
        {COLS.map((col) => (
          <div
            key={col}
            className={[
              'px-4 py-3 text-xs font-semibold uppercase tracking-wider text-[var(--color-text-mute)]',
              col !== 'po' ? 'border-l border-[var(--border-light)]' : '',
            ].join(' ')}
          >
            {COL_LABELS[col]}
          </div>
        ))}
      </div>

      {/* Rows */}
      {allKeys.map((field) => {
        const isDiff = differences.includes(field);
        return (
          <div
            key={field}
            className={[
              'grid grid-cols-3 border-b border-[var(--border-light)] last:border-0',
              isDiff ? 'bg-amber/10' : '',
            ].join(' ')}
          >
            {COLS.map((col, ci) => {
              const val = docs[col]?.[field];
              return (
                <div
                  key={col}
                  className={[
                    'px-4 py-3',
                    ci !== 0 ? 'border-l border-[var(--border-light)]' : '',
                  ].join(' ')}
                >
                  <span className="block text-[10px] text-[var(--color-text-mute)] uppercase tracking-wider mb-0.5">
                    {field}
                  </span>
                  <span className={[
                    'text-sm font-mono tabular-nums',
                    isDiff ? 'text-amber font-semibold' : 'text-ink',
                  ].join(' ')}>
                    {formatValue(field, val)}
                  </span>
                </div>
              );
            })}
          </div>
        );
      })}
    </div>
  );
}

export default memo(MatchGrid);
