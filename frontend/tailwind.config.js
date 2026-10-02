/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        navy:        'var(--color-navy)',
        electric:    'var(--color-electric)',
        emerald:     'var(--color-emerald)',
        amber:       'var(--color-amber)',
        ink:         'var(--color-ink)',
        canvas:      'var(--color-canvas)',
        surface:     'var(--color-surface)',
        'surface-2': 'var(--color-surface-2)',
        sev: {
          critical: 'var(--sev-critical)',
          high:     'var(--sev-high)',
          medium:   'var(--sev-medium)',
          low:      'var(--sev-low)',
        },
      },
      fontFamily: {
        sans: ['"Inter Variable"', 'system-ui', 'sans-serif'],
        mono: ['"JetBrains Mono Variable"', 'ui-monospace', 'monospace'],
      },
    },
  },
  plugins: [],
};
