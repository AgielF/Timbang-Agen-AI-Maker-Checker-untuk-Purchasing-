import { memo } from 'react';
import Skeleton from '../molecules/Skeleton';
import EmptyState from '../molecules/EmptyState';
import Badge from '../atoms/Badge';

const STATUS_VARIANT = {
  active:   'success',
  inactive: 'muted',
  banned:   'critical',
};

const fmt = new Intl.DateTimeFormat('id-ID', {
  day: '2-digit',
  month: 'short',
  year: 'numeric',
});

function formatDate(iso) {
  if (!iso) return '—';
  try {
    return fmt.format(new Date(iso));
  } catch {
    return iso;
  }
}

/**
 * VendorTable — semantic HTML table of vendors.
 * Props:
 *   rows       {Array<{ id, name, created_at, status }>}
 *   loading    {boolean}
 *   error      {string|null}
 *   emptyState {{ title, description }} optional override
 */
function VendorTable({ rows = [], loading = false, error = null, emptyState = {} }) {
  const {
    title: emptyTitle = 'Belum ada vendor',
    description: emptyDesc = 'Tambahkan vendor untuk memulai.',
  } = emptyState;

  if (loading) {
    return (
      <div className="border border-[var(--border-light)] rounded-none overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-canvas border-b border-[var(--border-light)]">
              <th className="text-left px-4 py-3 font-medium text-[var(--color-text-mute)] uppercase tracking-wider text-xs w-1/2">Name</th>
              <th className="text-left px-4 py-3 font-medium text-[var(--color-text-mute)] uppercase tracking-wider text-xs">Created</th>
              <th className="text-left px-4 py-3 font-medium text-[var(--color-text-mute)] uppercase tracking-wider text-xs">Status</th>
            </tr>
          </thead>
          <tbody>
            {Array.from({ length: 5 }).map((_, i) => (
              <tr key={i} className="border-b border-[var(--border-light)] last:border-0">
                <td className="px-4 py-3"><Skeleton h="h-4" w="w-48" /></td>
                <td className="px-4 py-3"><Skeleton h="h-4" w="w-28" /></td>
                <td className="px-4 py-3"><Skeleton h="h-5" w="w-16" rounded /></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  }

  if (error) {
    return (
      <div className="border border-sev-critical/30 bg-sev-critical/5 rounded-none px-4 py-3 text-sm text-sev-critical">
        {error}
      </div>
    );
  }

  if (!rows.length) {
    return (
      <div className="border border-[var(--border-light)]">
        <EmptyState icon="file-text" title={emptyTitle} description={emptyDesc} />
      </div>
    );
  }

  return (
    <div className="border border-[var(--border-light)] rounded-none overflow-hidden">
      <table className="w-full text-sm">
        <thead>
          <tr className="bg-canvas border-b border-[var(--border-light)]">
            <th className="text-left px-4 py-3 font-medium text-[var(--color-text-mute)] uppercase tracking-wider text-xs w-1/2">Name</th>
            <th className="text-left px-4 py-3 font-medium text-[var(--color-text-mute)] uppercase tracking-wider text-xs">Created</th>
            <th className="text-left px-4 py-3 font-medium text-[var(--color-text-mute)] uppercase tracking-wider text-xs">Status</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr
              key={row.id}
              className="border-b border-[var(--border-light)] last:border-0 hover:bg-canvas/60 transition-colors"
            >
              <td className="px-4 py-3 font-medium text-ink">{row.name}</td>
              <td className="px-4 py-3 text-[var(--color-text-mute)] tabular-nums">
                {formatDate(row.created_at)}
              </td>
              <td className="px-4 py-3">
                <Badge variant={STATUS_VARIANT[row.status?.toLowerCase()] ?? 'muted'}>
                  {row.status ?? '—'}
                </Badge>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default memo(VendorTable);
