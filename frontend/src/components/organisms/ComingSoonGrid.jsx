import { memo } from 'react';
import { Link } from 'react-router-dom';
import Icon from '../atoms/Icon';
import Badge from '../atoms/Badge';

const DEFAULT_ITEMS = [
  {
    icon: 'alert-triangle',
    title: 'Real-time Alerts',
    caption: 'Notifikasi anomali real-time ke tim procurement.',
  },
  {
    icon: 'file-text',
    title: 'PDF Export',
    caption: 'Export laporan risiko ke PDF satu klik.',
  },
  {
    icon: 'external-link',
    title: 'Slack Integration',
    caption: 'Kirim alert langsung ke channel Slack tim.',
  },
  {
    icon: 'clock',
    title: 'Historical Analytics',
    caption: 'Dashboard tren fraud historis per kuartal.',
  },
];

function ComingSoonGrid({ items = DEFAULT_ITEMS }) {
  return (
    <section aria-label="Coming soon features" className="max-w-7xl mx-auto px-6 py-16">
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-px bg-[var(--border-light)]">
        {items.map(({ icon, title, caption, hideBadge, to }) => {
          const Content = (
            <div
              key={title}
              className={`bg-canvas flex flex-col gap-4 p-6 ${to ? 'hover:bg-black/[0.03] transition-colors' : ''} h-full`}
            >
              <div className="flex items-start justify-between gap-2">
                <span className="text-navy/40">
                  <Icon name={icon} size={22} />
                </span>
                {!hideBadge && <Badge variant="high" size="sm">Coming Soon</Badge>}
              </div>
              <div className="flex flex-col gap-1">
                <h3 className="text-base font-semibold text-ink">{title}</h3>
                <p className="text-sm text-[var(--color-text-mute)] leading-relaxed">
                  {caption}
                </p>
              </div>
            </div>
          );

          return to ? (
            <Link key={title} to={to} className="no-underline block h-full">
              {Content}
            </Link>
          ) : (
            <div key={title} className="h-full">
              {Content}
            </div>
          );
        })}
      </div>
    </section>
  );
}

export default memo(ComingSoonGrid);
