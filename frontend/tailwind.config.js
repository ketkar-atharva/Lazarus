/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'deep-space': '#020617',
        'cyber-cyan': '#06b6d4',
        'neon-green': '#22c55e',
        'pulse-red': '#ef4444',
        'ghost-purple': '#a855f7',
      },
      animation: {
        'blink': 'blink 1.4s ease-in-out infinite',
        'pulse-glow': 'pulse-glow 2s ease-in-out infinite',
        'fade-purple': 'fade-purple 0.6s ease-out forwards',
        'slide-in': 'slide-in 0.5s ease-out forwards',
      },
      keyframes: {
        blink: {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.2' },
        },
        'pulse-glow': {
          '0%, 100%': { boxShadow: '0 0 5px rgba(6, 182, 212, 0.3)' },
          '50%': { boxShadow: '0 0 20px rgba(6, 182, 212, 0.6)' },
        },
        'fade-purple': {
          '0%': { backgroundColor: 'transparent' },
          '100%': { backgroundColor: 'rgba(168, 85, 247, 0.15)' },
        },
        'slide-in': {
          '0%': { opacity: '0', transform: 'translateY(10px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
      },
    },
  },
  plugins: [],
}
