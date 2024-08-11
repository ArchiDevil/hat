/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './index.html',
    './src/**/*.{vue,ts}',
  ],
  theme: {
    fontSize: {
      sm: '0.75rem',
      base: '0.875rem',
      lg: '1rem',
      xl: '1.25rem',
      '2xl': '1.5rem',
    },
    fontFamily: {
      ui: ['Inter', 'sans-serif'],
      text: ['Open Sans', 'sans-serif'],
    },
    container: {
      center: true,
      padding: '2rem',
    },
  },
  plugins: [require('tailwindcss-primeui')],
}
