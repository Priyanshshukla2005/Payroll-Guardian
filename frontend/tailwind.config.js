/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        obsidian: {
          950: '#04060a',
          900: '#070a12',
          850: '#0b101d',
          800: '#101626',
        },
        charcoal: {
          900: '#131929',
          800: '#182137',
          700: '#1f2b48',
          600: '#28375c',
        },
        cyan: {
          400: '#22d3ee',
          500: '#06b6d4',
          accent: '#00f0ff',
        },
        brand: {
          50: '#f0f9ff',
          100: '#e0f2fe',
          200: '#bae6fd',
          300: '#7dd3fc',
          400: '#38bdf8',
          500: '#0ea5e9',
          600: '#0284c7',
          700: '#0369a1',
          800: '#075985',
          900: '#0c4a6e',
          950: '#082f49',
        },
        risk: {
          low: '#10b981',
          medium: '#f59e0b',
          high: '#f97316',
          critical: '#f43f5e',
        },
        slate: {
          850: '#121829',
          900: '#0a0f1d',
          950: '#05070c',
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      animation: {
        'pulse-slow': 'pulse 4s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'spin-slow': 'spin 20s linear infinite',
      },
    },
  },
  plugins: [],
}
