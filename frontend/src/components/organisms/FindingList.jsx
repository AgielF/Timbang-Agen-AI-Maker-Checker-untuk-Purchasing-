import { memo } from 'react';
import Icon from '../atoms/Icon';
import SeverityBadge from '../molecules/SeverityBadge';
import IndicationBadge from '../molecules/IndicationBadge';
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

const SEVERITY_ICON = {
  critical: { name: 'x-circle', color: 'text-sev-critical' },
  high: { name: 'alert-triangle', color: 'text-sev-high' },
  medium: { name: 'alert-triangle', color: 'text-sev-medium' },
  low: { name: 'check', color: 'text-sev-low' },
};

function CitationBlock({ evidenceUrl, sopClauseCitation }) {
  if (!evidenceUrl && !sopClauseCitation) return null;

  const isExternalUrl = /^https?:\/\//i.test(evidenceUrl ?? '');

  return (
    <div className="mt-2 flex flex-col gap-1 border-l-2 border-[var(--border-light)] pl-3 text-xs text-[var(--color-text-mute)]">
      {evidenceUrl && (
        <div className="flex items-start gap-1.5 min-w-0">
          <Icon name="external-link" size={13} className="mt-0.5 shrink-0" />
          {isExternalUrl ? (
            <a
              href={evidenceUrl}
              target="_blank"
              rel="noreferrer"
              className="break-all underline decoration-[var(--border-light)] underline-offset-2 hover:text-ink"
            >
              {evidenceUrl}
            </a>
          ) : (
            <span className="break-all">{evidenceUrl}</span>
          )}
        </div>
      )}
      {sopClauseCitation && (
        <div className="flex items-start gap-1.5 min-w-0">
          <Icon name="file-text" size={13} className="mt-0.5 shrink-0" />
          <span>{sopClauseCitation}</span>
        </div>
      )}
    </div>
  );
}

/**
 * FindingList — list of audit findings.
 * Props:
 *   items    {Array<{ id, transaction_id, severity, message, indication_label, evidence_url, sop_clause_citation, created_at }>}
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

  const groups = new Map();
  for (const item of items) {
    const indication = (item.indication_label || 'UNKNOWN').toUpperCase();
    if (!groups.has(indication)) groups.set(indication, []);
    groups.get(indication).push(item);
  }

  return (
    <div className="border border-[var(--border-light)] divide-y divide-[var(--border-light)]">
      {[...groups.entries()].map(([indication, groupItems]) => (
        <section key={indication} aria-label={`Temuan: ${indication}`}>
          <header className="flex items-center justify-between gap-3 border-b border-[var(--border-light)] bg-canvas/60 px-4 py-2">
            <IndicationBadge value={indication} />
            <span className="text-xs text-[var(--color-text-mute)]">
              {groupItems.length} temuan
            </span>
          </header>
          <ul className="divide-y divide-[var(--border-light)]">
            {groupItems.map((item) => {
              const severity = (item.severity ?? '').toLowerCase();
              const severityIcon = SEVERITY_ICON[severity] ?? SEVERITY_ICON.medium;
              const description = item.description ?? item.message ?? '—';

              return (
                <li
                  key={item.id}
                  className="flex items-start gap-3 px-4 py-3 hover:bg-canvas/60 transition-colors"
                >
                  <span className={`${severityIcon.color} mt-0.5 shrink-0`} title={`Severity ${severity || 'unknown'}`}>
                    <Icon name={severityIcon.name} size={16} />
                  </span>
                  <div className="flex-1 min-w-0">
                    <div className="mb-1.5 flex flex-wrap items-center gap-2">
                      <IndicationBadge value={indication} />
                      <SeverityBadge level={severity} />
                    </div>
                    <p className="text-sm text-ink leading-snug">{description}</p>
                    {item.transaction_id && (
                      <p className="text-xs text-[var(--color-text-mute)] mt-0.5 font-mono tabular-nums">
                        {item.transaction_id}
                      </p>
                    )}
                    <CitationBlock
                      evidenceUrl={item.evidence_url}
                      sopClauseCitation={item.sop_clause_citation}
                    />
                  </div>
                  <time
                    dateTime={item.created_at}
                    className="text-xs text-[var(--color-text-mute)] tabular-nums shrink-0 pt-0.5"
                  >
                    {formatTs(item.created_at)}
                  </time>
                </li>
              );
            })}
          </ul>
        </section>
      ))}
    </div>
  );
}

export default memo(FindingList);
