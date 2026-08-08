import type { Config } from 'tailwindcss';

/**
 * TailwindCSS configuration for ClinIQ.
 *
 * Design System:
 * - Primary: Medical Blue (#1D6FA4)
 * - Secondary: Healthcare Green (#2E9B6B)
 * - Background: Very light gray (#F8FAFC)
 * - Cards: White with soft shadow
 * - Font: Inter
 *
 * CSS variable-based colors (shadcn/ui compatible) use RGB channels
 * so they work with Tailwind's opacity modifier syntax: bg-primary/50.
 */
const config: Config = {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        // ── ClinIQ Brand ──────────────────────────────────────────
        primary: {
          DEFAULT: 'rgb(var(--color-primary) / <alpha-value>)',
          foreground: 'rgb(var(--color-primary-foreground) / <alpha-value>)',
          50:  '#EBF4FB',
          100: '#D6E9F7',
          200: '#ADD3EF',
          300: '#84BCE7',
          400: '#5BA6DF',
          500: '#1D6FA4',
          600: '#175C8A',
          700: '#114870',
          800: '#0B3556',
          900: '#06223B',
        },
        secondary: {
          DEFAULT: 'rgb(var(--color-secondary) / <alpha-value>)',
          foreground: 'rgb(var(--color-secondary-foreground) / <alpha-value>)',
          50:  '#EAF6F1',
          100: '#D5EDE3',
          200: '#AADBC7',
          300: '#80C9AB',
          400: '#55B78F',
          500: '#2E9B6B',
          600: '#257F58',
          700: '#1C6345',
          800: '#134732',
          900: '#0A2B1F',
        },
        // ── Semantic tokens (CSS variable driven) ─────────────────
        background: 'rgb(var(--color-background) / <alpha-value>)',
        foreground: 'rgb(var(--color-foreground) / <alpha-value>)',
        border:     'rgb(var(--color-border) / <alpha-value>)',
        input:      'rgb(var(--color-input) / <alpha-value>)',
        ring:       'rgb(var(--color-ring) / <alpha-value>)',
        card: {
          DEFAULT:    'rgb(var(--color-card) / <alpha-value>)',
          foreground: 'rgb(var(--color-card-foreground) / <alpha-value>)',
        },
        muted: {
          DEFAULT:    'rgb(var(--color-muted) / <alpha-value>)',
          foreground: 'rgb(var(--color-muted-foreground) / <alpha-value>)',
        },
        accent: {
          DEFAULT:    'rgb(var(--color-accent) / <alpha-value>)',
          foreground: 'rgb(var(--color-accent-foreground) / <alpha-value>)',
        },
        destructive: {
          DEFAULT:    '#ef4444',
          foreground: '#ffffff',
        },
        // ── Clinical Status Colors ─────────────────────────────────
        clinical: {
          critical:  '#DC2626',
          warning:   '#D97706',
          normal:    '#16A34A',
          info:      '#2563EB',
          pending:   '#9333EA',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      borderRadius: {
        DEFAULT: '0.5rem',
        sm:  '0.375rem',
        md:  '0.5rem',
        lg:  '0.75rem',
        xl:  '1rem',
        '2xl': '1.25rem',
      },
      boxShadow: {
        card: '0 1px 3px 0 rgb(0 0 0 / 0.07), 0 1px 2px -1px rgb(0 0 0 / 0.07)',
        'card-md': '0 4px 6px -1px rgb(0 0 0 / 0.07), 0 2px 4px -2px rgb(0 0 0 / 0.07)',
        'card-lg': '0 10px 15px -3px rgb(0 0 0 / 0.07), 0 4px 6px -4px rgb(0 0 0 / 0.07)',
      },
      animation: {
        'fade-in':     'fadeIn 0.3s ease-out',
        'slide-up':    'slideUp 0.3s ease-out',
        'slide-in-left': 'slideInLeft 0.25s ease-out',
        'pulse-slow':  'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
      keyframes: {
        fadeIn: {
          '0%':   { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%':   { opacity: '0', transform: 'translateY(8px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        slideInLeft: {
          '0%':   { opacity: '0', transform: 'translateX(-8px)' },
          '100%': { opacity: '1', transform: 'translateX(0)' },
        },
      },
    },
  },
  plugins: [],
};

export default config;
