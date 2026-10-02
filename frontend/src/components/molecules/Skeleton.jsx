import { memo } from 'react';

function Skeleton({ w = 'w-full', h = 'h-4', rounded = false, className = '' }) {
  return (
    <div
      aria-hidden="true"
      className={[
        'animate-pulse bg-ink/10',
        typeof w === 'string' ? w : '',
        typeof h === 'string' ? h : '',
        rounded ? 'rounded-full' : 'rounded-sm',
        className,
      ].join(' ')}
      style={{
        width: typeof w === 'number' ? w : undefined,
        height: typeof h === 'number' ? h : undefined,
      }}
    />
  );
}

export default memo(Skeleton);
