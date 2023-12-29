/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './index.html',
    './tmx.html',
    './xliff.html',
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
      sans: ['Open Sans', 'sans-serif'],
    }
  },
  plugins: [],
}
