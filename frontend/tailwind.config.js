/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: '#FAF9F7',
        surface: '#FFFFFF',
        text: '#1A1C20',
        muted: '#63656A',
        accent: '#262626',
        border: 'rgba(0,0,0,0.08)',
        brand: {
          50: '#fcfaf8',
          100: '#f5efeb',
          200: '#eeded5',
          300: '#e1c6b5',
          400: '#d0a991',
          500: '#c19275',
          600: '#b47e5f',
          700: '#97654c',
          800: '#7a5240',
          900: '#644436',
          950: '#35221b',
        },
      },
      fontFamily: {
        sans: ['var(--font-inter)', 'sans-serif'],
        serif: ['var(--font-playfair)', 'serif'],
      },
      animation: {
        'fade-in-up': 'fade-in-up 0.8s cubic-bezier(0.16, 1, 0.3, 1) forwards',
        'soft-pulse': 'soft-pulse 4s ease-in-out infinite',
      }
    },
  },
  plugins: [],
}
