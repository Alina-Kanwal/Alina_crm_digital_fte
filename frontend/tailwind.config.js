/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: '#FDFCF9',
        surface: '#FFFFFF',
        border: 'rgba(0,0,0,0.05)',
        text: '#1A1A1A',
        accent: '#D45B45',
        muted: '#737373',
      },
      fontFamily: {
        sans: ['var(--font-inter)', 'sans-serif'],
        serif: ['var(--font-playfair)', 'serif'],
      },
      boxShadow: {
        soft: '0 4px 20px rgba(0, 0, 0, 0.03)',
      }
    },
  },
  plugins: [],
}
