import { memo } from 'react';

// All paths use viewBox="0 0 24 24", stroke="currentColor", fill="none"
const ICONS = {
  'search': (
    <g>
      <circle cx="11" cy="11" r="8" />
      <path d="M21 21l-4.35-4.35" strokeLinecap="round" />
    </g>
  ),
  'arrow-right': (
    <path d="M5 12h14M12 5l7 7-7 7" strokeLinecap="round" strokeLinejoin="round" />
  ),
  'check': (
    <path d="M20 6L9 17l-5-5" strokeLinecap="round" strokeLinejoin="round" />
  ),
  'alert-triangle': (
    <g>
      <path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z" />
      <path d="M12 9v4M12 17h.01" strokeLinecap="round" />
    </g>
  ),
  'x-circle': (
    <g>
      <circle cx="12" cy="12" r="10" />
      <path d="M15 9l-6 6M9 9l6 6" strokeLinecap="round" />
    </g>
  ),
  'loader': (
    <g>
      <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83" strokeLinecap="round" />
    </g>
  ),
  'external-link': (
    <g>
      <path d="M18 13v6a2 2 0 01-2 2H5a2 2 0 01-2-2V8a2 2 0 012-2h6" />
      <path d="M15 3h6v6M10 14L21 3" strokeLinecap="round" strokeLinejoin="round" />
    </g>
  ),
  'menu': (
    <g>
      <path d="M3 12h18M3 6h18M3 18h18" strokeLinecap="round" />
    </g>
  ),
  'chevron-down': (
    <path d="M6 9l6 6 6-6" strokeLinecap="round" strokeLinejoin="round" />
  ),
  'chevron-right': (
    <path d="M9 18l6-6-6-6" strokeLinecap="round" strokeLinejoin="round" />
  ),
  'plus': (
    <path d="M12 5v14M5 12h14" strokeLinecap="round" />
  ),
  'file-text': (
    <g>
      <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" />
      <path d="M14 2v6h6M16 13H8M16 17H8M10 9H8" strokeLinecap="round" />
    </g>
  ),
  'shield': (
    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" strokeLinejoin="round" />
  ),
  'dollar-sign': (
    <g>
      <path d="M12 1v22M17 5H9.5a3.5 3.5 0 000 7h5a3.5 3.5 0 010 7H6" strokeLinecap="round" />
    </g>
  ),
  'clock': (
    <g>
      <circle cx="12" cy="12" r="10" />
      <path d="M12 6v6l4 2" strokeLinecap="round" />
    </g>
  ),
};

function Icon({ name, size = 20, strokeWidth = 2, className = '' }) {
  const path = ICONS[name];
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={strokeWidth}
      className={className}
      aria-hidden="true"
    >
      {path ?? null}
    </svg>
  );
}

export default memo(Icon);
