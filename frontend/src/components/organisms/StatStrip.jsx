import { memo } from 'react';
import StatCell from '../molecules/StatCell';

const DEFAULT_ITEMS = [
  { value: '5%',    label: 'Revenue loss per year (ACFE 2026)' },
  { value: '62.9s', label: 'Maker Agent execution time' },
  { value: '39',    label: 'Tests passing' },
];

function StatStrip({ items = DEFAULT_ITEMS }) {
  return (
    <section
      aria-label="Key statistics"
      className="border-y border-[var(--border-light)]"
    >
      <div className="max-w-7xl mx-auto grid grid-cols-1 md:grid-cols-3 divide-y md:divide-y-0 md:divide-x divide-[var(--border-light)]">
        {items.map(({ value, label, accent }) => (
          <StatCell
            key={label}
            value={value}
            label={label}
            accent={accent}
          />
        ))}
      </div>
    </section>
  );
}

export default memo(StatStrip);
