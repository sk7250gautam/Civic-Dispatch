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
        navy: {
          50: '#f0f4f9',
          100: '#e1e9f2',
          200: '#c3d3e6',
          300: '#94b3d4',
          400: '#5e8fc0',
          500: '#3970a9',
          600: '#28568b',
          700: '#204571',
          800: '#1c3b5f',
          900: '#1a324f',
          950: '#0d1929',
        },
        civic: {
          teal: {
            50: '#effefb',
            100: '#c7fdf3',
            200: '#90fbe7',
            300: '#51f0d7',
            400: '#20dbc1',
            500: '#08bfa6',
            600: '#039a87',
            700: '#057a6d',
            800: '#086158',
            900: '#0c5049',
          },
          amber: {
            500: '#f59e0b',
            600: '#d97706',
          },
          rose: {
            500: '#f43f5e',
            600: '#e11d48',
          },
          emerald: {
            500: '#10b981',
            600: '#059669',
          }
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
      }
    },
  },
  plugins: [],
}
