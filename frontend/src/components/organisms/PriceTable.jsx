import { memo } from 'react';
import Badge from '../atoms/Badge';
import Skeleton from '../molecules/Skeleton';
import EmptyState from '../molecules/EmptyState';

const fmtIDR = new Intl.NumberFormat('id-ID', {
  style: 'currency',
  currency: 'IDR',
  maximumFractionDigits: 0,
});

const fmtPct = (v) =>
  (v >= 0 ? '+' : '') + v.toFixed(1) + '%';

const VERDICT_MAP = {
  fair:        { label: 'Fair',        cls: 'bg-emerald/10 text-emerald border border-emerald/30' },
  overpriced:  { label: 'Overpriced',  cls: 'bg-sev-high/10 text-sev-high border border-sev-high/30' },
  underpriced: { label: 'Underpriced', cls: 'bg-electric/10 text-electric border border-electric/30' },
};

/**
 * VerdictBanner — strip above the table.
 */
function VerdictBanner({ verdict }) {
  const key = (verdict ?? '').toLowerCase();
  const { label, cls } = VERDICT_MAP[key] ?? { label: verdict, cls: 'bg-canvas border border-[var(--border-light)] text-ink' };
  return (
    <div className={`px-4 py-2 text-sm font-semibold uppercase tracking-wider flex items-center gap-2 ${cls}`}>
      {label}
    </div>
  );
}

/**
 * PriceTable — quote comparison table.
 * Props:
 *   quotes  {Array<{ vendor_id, vendor_name, price }>}
 *   median  {number}
 *   verdict {'fair'|'overpriced'|'underpriced'}
 *   loading {boolean}
 *   error   {string|null}
 */
function PriceTable({ quotes = [], median = 0, verdict, loading = false, error = null }) {
  if (loading) {
    return (
      <div className="border border-[var(--border-light)] overflow-hidden">
        <div className="h-9 bg-ink/5 animate-pulse" />
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-canvas border-b border-[var(--border-light)]">
              <th className="text-left px-4 py-3 text-xs font-medium text-[var(--color-text-mute)] uppercase tracking-wider">Vendor</th>
              <th className="text-right px-4 py-3 text-xs font-medium text-[var(--color-text-mute)] uppercase tracking-wider">Harga</th>
              <th className="text-right px-4 py-3 text-xs font-medium text-[var(--color-text-mute)] uppercase tracking-wider">Δ Median</th>
            </tr>
          </thead>
          <tbody>
            {Array.from({ length: 4 }).map((_, i) => (
              <tr key={i} className="border-b border-[var(--border-light)] last:border-0">
                <td className="px-4 py-3"><Skeleton h="h-4" w="w-40" /></td>
                <td className="px-4 py-3 text-right"><Skeleton h="h-4" w="w-28" className="ml-auto" /></td>
                <td className="px-4 py-3 text-right"><Skeleton h="h-4" w="w-16" className="ml-auto" /></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  }

  if (error) {
    return (
      <div className="border border-sev-critical/30 bg-sev-critical/5 px-4 py-3 text-sm text-sev-critical">
        {error}
      </div>
    );
  }

  if (!quotes.length) {
    return (
      <div className="border border-[var(--border-light)]">
        <EmptyState icon="dollar-sign" title="Belum ada quote" description="Tambahkan quote vendor untuk melihat perbandingan harga." />
      </div>
    );
  }

  const prices    = quotes.map((q) => q.price);
  const minPrice  = Math.min(...prices);
  const maxPrice  = Math.max(...prices);

  return (
    <div className="border border-[var(--border-light)] overflow-hidden">
      {verdict && <VerdictBanner verdict={verdict} />}
      <table className="w-full text-sm">
        <thead>
          <tr className="bg-canvas border-b border-[var(--border-light)]">
            <th className="text-left px-4 py-3 text-xs font-medium text-[var(--color-text-mute)] uppercase tracking-wider">Vendor</th>
            <th className="text-right px-4 py-3 text-xs font-medium text-[var(--color-text-mute)] uppercase tracking-wider">Harga</th>
            <th className="text-right px-4 py-3 text-xs font-medium text-[var(--color-text-mute)] uppercase tracking-wider">Δ Median</th>
          </tr>
        </thead>
        <tbody>
          {quotes.map((q) => {
            const delta    = median > 0 ? ((q.price - median) / median) * 100 : 0;
            const isMin    = q.price === minPrice;
            const isMax    = q.price === maxPrice;
            const deltaPos = delta > 0;

            return (
              <tr
                key={q.vendor_id ?? q.vendor_name}
                className={[
                  'border-b border-[var(--border-light)] last:border-0 transition-colors',
                  isMin ? 'border-l-4 border-l-emerald'      : '',
                  isMax ? 'border-l-4 border-l-sev-high'     : '',
                  !isMin && !isMax ? 'border-l-4 border-l-transparent' : '',
                ].join(' ')}
              >
                <td className="px-4 py-3 font-medium text-ink">
                  {q.vendor_name ?? q.vendor_id}
                  {isMin && <Badge variant="success" size="sm" className="ml-2">Terendah</Badge>}
                  {isMax && <Badge variant="high"    size="sm" className="ml-2">Tertinggi</Badge>}
                </td>
                <td className="px-4 py-3 text-right font-mono tabular-nums text-ink">
                  {fmtIDR.format(q.price)}
                </td>
                <td className={[
                  'px-4 py-3 text-right font-mono tabular-nums text-sm',
                  deltaPos ? 'text-sev-high' : 'text-emerald',
                ].join(' ')}>
                  {median > 0 ? fmtPct(delta) : '—'}
                </td>
              </tr>
            );
          })}
        </tbody>
        {median > 0 && (
          <tfoot>
            <tr className="border-t border-[var(--border-light)] bg-canvas">
              <td className="px-4 py-2 text-xs text-[var(--color-text-mute)] uppercase tracking-wider font-medium">Median</td>
              <td className="px-4 py-2 text-right font-mono tabular-nums text-xs text-[var(--color-text-mute)]">
                {fmtIDR.format(median)}
              </td>
              <td />
            </tr>
          </tfoot>
        )}
      </table>
    </div>
  );
}

export default memo(PriceTable);
