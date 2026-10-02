/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        navy:        'rgb(var(--color-navy-rgb) / <alpha-value>)',
        electric:    'rgb(var(--color-electric-rgb) / <alpha-value>)',
        emerald:     'rgb(var(--color-emerald-rgb) / <alpha-value>)',
        amber:       'rgb(var(--color-amber-rgb) / <alpha-value>)',
        ink:         'rgb(var(--color-ink-rgb) / <alpha-value>)',
        canvas:      'rgb(var(--color-canvas-rgb) / <alpha-value>)',
        surface:     'rgb(var(--color-surface-rgb) / <alpha-value>)',
        'surface-2': 'rgb(var(--color-surface-2-rgb) / <alpha-value>)',
        sev: {
          critical: 'rgb(var(--sev-critical-rgb) / <alpha-value>)',
          high:     'rgb(var(--sev-high-rgb) / <alpha-value>)',
          medium:   'rgb(var(--sev-medium-rgb) / <alpha-value>)',
          low:      'rgb(var(--sev-low-rgb) / <alpha-value>)',
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
