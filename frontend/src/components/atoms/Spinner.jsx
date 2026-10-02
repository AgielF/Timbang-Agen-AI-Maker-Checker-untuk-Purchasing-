import { memo } from 'react';

const SIZE_MAP = {
  sm: 'w-4 h-4 border-2',
  md: 'w-6 h-6 border-2',
  lg: 'w-8 h-8 border-[3px]',
};

function Spinner({ size = 'md', className = '' }) {
  return (
    <span
      role="status"
      aria-label="Memuat..."
      className={[
        'inline-block rounded-full border-current border-r-transparent animate-spin',
        SIZE_MAP[size] ?? SIZE_MAP.md,
        className,
      ].join(' ')}
    />
  );
}

export default memo(Spinner);
