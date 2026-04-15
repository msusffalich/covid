/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        brand: {
          50:  '#eef4fd',
          100: '#d6e4f7',
          200: '#adc9ef',
          300: '#84adde',
          400: '#5b92cc',
          500: '#3477BD',
          600: '#2a5f98',
          700: '#1f4773',
          800: '#152f4e',
          900: '#1A3A6E',
        },
        gold: '#FFBA00',
      },
      animation: {
        'pulse-slow': 'pulse 2s cubic-bezier(0.4,0,0.6,1) infinite',
        'slide-in': 'slideIn 0.35s ease-out',
      },
      keyframes: {
        slideIn: {
          '0%':   { opacity: '0', transform: 'translateY(12px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
      },
    },
  },
  plugins: [],
}
