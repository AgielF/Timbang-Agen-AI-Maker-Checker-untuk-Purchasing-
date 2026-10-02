import { forwardRef, memo } from 'react';
import Spinner from './Spinner';

const VARIANT_MAP = {
  primary: 'bg-electric text-white hover:bg-electric/90 border-transparent',
  ghost:   'border border-[var(--border-light)] text-ink hover:bg-navy/5',
  danger:  'bg-sev-critical text-white hover:bg-sev-critical/90 border-transparent',
};

const SIZE_MAP = {
  sm: 'text-sm px-3 py-1.5 gap-1.5',
  md: 'text-base px-4 py-2 gap-2',
  lg: 'text-lg px-6 py-3 gap-2',
};

const Button = forwardRef(function Button(
  {
    variant = 'primary',
    size = 'md',
    loading = false,
    disabled = false,
    type = 'button',
    className = '',
    children,
    ...rest
  },
  ref,
) {
  return (
    <button
      ref={ref}
      type={type}
      disabled={disabled || loading}
      className={[
        'inline-flex items-center justify-center rounded-md font-medium',
        'transition-colors focus-visible:outline-none focus-visible:ring-2',
        'focus-visible:ring-electric/50 disabled:opacity-50 disabled:pointer-events-none',
        VARIANT_MAP[variant] ?? VARIANT_MAP.primary,
        SIZE_MAP[size] ?? SIZE_MAP.md,
        className,
      ].join(' ')}
      {...rest}
    >
      {loading ? <Spinner size="sm" /> : children}
    </button>
  );
});

export default memo(Button);
