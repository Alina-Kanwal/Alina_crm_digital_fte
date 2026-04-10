/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: '#020203',
        surface: '#0A0A0B',
        accent: '#6366F1',
        muted: '#475569',
      },
      animation: {
        'spin-slow': 'spin-slow 12s linear infinite',
        'float': 'float 6s ease-in-out infinite',
        'reveal': 'reveal 0.8s cubic-bezier(0.16, 1, 0.3, 1) forwards',
      },
      keyframes: {
        'spin-slow': {
          from { transform: rotate(0deg) },
          to { transform: rotate(360deg) },
        },
        'float': {
          '0%, 100%': { transform: translateY(0px) },
          '50%': { transform: translateY(-15px) },
        },
        'reveal': {
          from { opacity: '0', transform: 'translateY(20px)' },
          to { opacity: '1', transform: 'translateY(0)' },
        },
      },
    },
  },
  plugins: [],
}
