import { memo } from 'react';

function StatCell({ value, label, accent = false }) {
  return (
    <div className="flex flex-col gap-1 py-6 px-8">
      <span
        className={[
          'text-4xl font-black font-mono tabular-nums leading-none',
          accent ? 'text-electric' : 'text-ink',
        ].join(' ')}
      >
        {value}
      </span>
      <span className="text-xs text-[var(--color-text-mute)] uppercase tracking-widest font-medium">
        {label}
      </span>
    </div>
  );
}

export default memo(StatCell);
