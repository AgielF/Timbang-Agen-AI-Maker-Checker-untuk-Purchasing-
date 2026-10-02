import { memo } from 'react';

function Circle({ size = 80, filled = false, className = '', children }) {
  return (
    <div
      className={[
        'rounded-full flex items-center justify-center shrink-0',
        filled
          ? 'bg-navy text-[var(--color-text-inv)]'
          : 'border border-[var(--border-light)]',
        className,
      ].join(' ')}
      style={{ width: size, height: size }}
    >
      {children}
    </div>
  );
}

export default memo(Circle);
