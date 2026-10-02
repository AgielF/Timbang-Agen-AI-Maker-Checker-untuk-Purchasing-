import { memo } from 'react';

const VARIANT_MAP = {
  default:  'bg-navy/10 text-navy border-navy/20',
  success:  'bg-emerald/10 text-emerald border-emerald/30',
  warning:  'bg-amber/10 text-amber border-amber/30',
  critical: 'bg-sev-critical/10 text-sev-critical border-sev-critical/30',
  high:     'bg-sev-high/10 text-sev-high border-sev-high/30',
  muted:    'bg-ink/5 text-[var(--color-text-mute)] border-ink/10',
};

const SIZE_MAP = {
  sm: 'text-[11px] px-1.5 py-0.5',
  md: 'text-xs px-2 py-0.5',
};

function Badge({ variant = 'default', size = 'md', className = '', children }) {
  return (
    <span
      className={[
        'inline-flex items-center border rounded-full font-medium uppercase tracking-wider',
        VARIANT_MAP[variant] ?? VARIANT_MAP.default,
        SIZE_MAP[size] ?? SIZE_MAP.md,
        className,
      ].join(' ')}
    >
      {children}
    </span>
  );
}

export default memo(Badge);
