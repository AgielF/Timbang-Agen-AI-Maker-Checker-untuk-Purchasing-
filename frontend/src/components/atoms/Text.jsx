import { memo } from 'react';

const VARIANT_MAP = {
  display: 'text-7xl md:text-8xl font-black tracking-tighter',
  h1:      'text-5xl md:text-6xl font-bold tracking-tight',
  h2:      'text-3xl md:text-4xl font-semibold tracking-tight',
  h3:      'text-xl font-semibold',
  body:    'text-base',
  caption: 'text-sm text-[var(--color-text-mute)]',
  mono:    'font-mono text-sm tabular-nums',
};

function Text({ as: Tag = 'p', variant = 'body', className = '', children, ...rest }) {
  return (
    <Tag
      className={[VARIANT_MAP[variant] ?? VARIANT_MAP.body, className].join(' ')}
      {...rest}
    >
      {children}
    </Tag>
  );
}

export default memo(Text);
