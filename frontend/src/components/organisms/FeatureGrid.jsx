import { memo } from 'react';
import FeatureCell from '../molecules/FeatureCell';

const DEFAULT_ITEMS = [
  {
    title: 'Maker Agent',
    caption: 'Analisis vendor + cross-validate harga via Langflow.',
  },
  {
    title: 'Checker Agent',
    caption: 'Three-way matching PO/GR/Invoice.',
  },
  {
    title: 'Risk Report',
    caption: 'Laporan risiko otomatis per transaksi.',
  },
  {
    title: 'Real-time Monitoring',
    caption: 'Notifikasi anomali real-time.',
    comingSoon: true,
  },
];

function FeatureGrid({ items = DEFAULT_ITEMS }) {
  return (
    <section aria-label="Features" className="max-w-7xl mx-auto px-6 py-16">
      <div className="grid grid-cols-1 md:grid-cols-2 divide-y md:divide-y-0 divide-[var(--border-light)]">
        {items.map(({ title, caption, comingSoon }) => (
          <FeatureCell
            key={title}
            title={title}
            caption={caption}
            comingSoon={comingSoon}
          />
        ))}
      </div>
    </section>
  );
}

export default memo(FeatureGrid);
