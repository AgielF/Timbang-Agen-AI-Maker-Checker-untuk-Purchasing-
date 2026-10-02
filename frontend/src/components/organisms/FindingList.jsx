import { memo } from 'react';
import SeverityBadge from '../molecules/SeverityBadge';
import Skeleton from '../molecules/Skeleton';
import EmptyState from '../molecules/EmptyState';

const fmt = new Intl.DateTimeFormat('id-ID', {
  day: '2-digit',
  month: 'short',
  year: 'numeric',
  hour: '2-digit',
  minute: '2-digit',
});

function formatTs(iso) {
  if (!iso) return '—';
  try {
    return fmt.format(new Date(iso));
  } catch {
    return iso;
  }
}

/**
 * FindingList — list of audit findings.
 * Props:
 *   items    {Array<{ id, transaction_id, severity, message, created_at }>}
 *   loading  {boolean}
 *   error    {string|null}
 *   emptyState {{ title, description }} optional override
 */
function FindingList({ items = [], loading = false, error = null, emptyState = {} }) {
  const {
    title: emptyTitle = 'Belum ada temuan',
    description: emptyDesc = 'Tidak ada anomali yang terdeteksi.',
  } = emptyState;

  if (loading) {
    return (
      <ul className="border border-[var(--border-light)] divide-y divide-[var(--border-light)]">
        {Array.from({ length: 5 }).map((_, i) => (
          <li key={i} className="flex items-start gap-3 px-4 py-3">
            <Skeleton h="h-5" w="w-16" rounded />
            <div className="flex-1 flex flex-col gap-1.5">
              <Skeleton h="h-4" w="w-full" />
              <Skeleton h="h-3" w="w-32" />
            </div>
          </li>
        ))}
      </ul>
    );
  }

  if (error) {
    return (
      <div className="border border-sev-critical/30 bg-sev-critical/5 px-4 py-3 text-sm text-sev-critical">
        {error}
      </div>
    );
  }

  if (!items.length) {
    return (
      <div className="border border-[var(--border-light)]">
        <EmptyState icon="shield" title={emptyTitle} description={emptyDesc} />
      </div>
    );
  }

  return (
    <ul className="border border-[var(--border-light)] divide-y divide-[var(--border-light)]">
      {items.map((item) => (
        <li
          key={item.id}
          className="flex items-start gap-3 px-4 py-3 hover:bg-canvas/60 transition-colors"
        >
          <SeverityBadge level={item.severity} />
          <div className="flex-1 min-w-0">
            <p className="text-sm text-ink leading-snug">{item.message}</p>
            {item.transaction_id && (
              <p className="text-xs text-[var(--color-text-mute)] mt-0.5 font-mono tabular-nums">
                {item.transaction_id}
              </p>
            )}
          </div>
          <time
            dateTime={item.created_at}
            className="text-xs text-[var(--color-text-mute)] tabular-nums shrink-0 pt-0.5"
          >
            {formatTs(item.created_at)}
          </time>
        </li>
      ))}
    </ul>
  );
}

export default memo(FindingList);
