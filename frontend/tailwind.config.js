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
        studio: {
          950: '#07090e',
          900: '#0b0f19',
          850: '#111726',
          800: '#172033',
          700: '#1f2b45',
          600: '#2d3d60',
          accent: '#06b6d4',
          accentGlow: 'rgba(6, 182, 212, 0.25)',
          purple: '#8b5cf6',
          purpleGlow: 'rgba(139, 92, 246, 0.25)',
          emerald: '#10b981',
          rose: '#f43f5e',
        }
      },
      boxShadow: {
        'glow-cyan': '0 0 25px -5px rgba(6, 182, 212, 0.3)',
        'glow-purple': '0 0 25px -5px rgba(139, 92, 246, 0.3)',
        'glow-emerald': '0 0 25px -5px rgba(16, 185, 129, 0.3)',
        'glass': '0 8px 32px 0 rgba(0, 0, 0, 0.37)',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      }
    },
  },
  plugins: [],
}

