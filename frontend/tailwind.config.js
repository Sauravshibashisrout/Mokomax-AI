/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        base: '#0d0d0f',
        surface: '#1a1a1d',
        accent: '#8b5cf6',
        'accent-hover': '#7c3aed',
        body: '#e5e5e5',
        muted: '#8a8a8f',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      lineHeight: {
        chat: '1.65',
      },
      boxShadow: {
        'accent-glow': '0 0 0 2px rgba(139,92,246,0.45)',
      },
      keyframes: {
        shimmer: {
          '0%': { backgroundPosition: '-400px 0' },
          '100%': { backgroundPosition: '400px 0' },
        },
      },
      animation: {
        shimmer: 'shimmer 1.4s ease infinite',
      },
    },
  },
  plugins: [],
}
