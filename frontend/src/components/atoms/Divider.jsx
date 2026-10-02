import { memo } from 'react';

function Divider({ orientation = 'horizontal', className = '' }) {
  if (orientation === 'vertical') {
    return (
      <span
        aria-hidden="true"
        className={['w-px self-stretch bg-[var(--border-light)]', className].join(' ')}
      />
    );
  }
  return (
    <hr
      aria-hidden="true"
      className={['border-0 border-t border-[var(--border-light)]', className].join(' ')}
    />
  );
}

export default memo(Divider);
