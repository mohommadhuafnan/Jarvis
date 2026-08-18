/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        jarvis: {
          bg: "#050508",
          card: "#0A0608",
          panel: "#0D0B0E",
          maroon: "#1A050B",
          red: "#FF1E42",
          crimson: "#E11D48",
          glow: "#FF2B56",
          darkred: "#4A0812",
          text: "#F5F5F5",
          muted: "#8F8F98",
          border: "rgba(255, 30, 66, 0.25)",
        }
      },
      fontFamily: {
        mono: ['"JetBrains Mono"', '"IBM Plex Mono"', 'Consolas', 'monospace'],
        sans: ['Rajdhani', 'Inter', 'system-ui', 'sans-serif'],
      },
      boxShadow: {
        'hud-red': '0 0 20px rgba(255, 30, 66, 0.35)',
        'hud-red-lg': '0 0 35px rgba(255, 30, 66, 0.55)',
        'hud-inner': 'inset 0 0 15px rgba(255, 30, 66, 0.25)',
      },
      animation: {
        'spin-slow': 'spin 20s linear infinite',
        'spin-reverse': 'spin-reverse 25s linear infinite',
        'pulse-glow': 'pulse-glow 3s ease-in-out infinite',
        'radar-sweep': 'radar-sweep 4s linear infinite',
        'scanline': 'scanline 8s linear infinite',
      },
      keyframes: {
        'spin-reverse': {
          '0%': { transform: 'rotate(0deg)' },
          '100%': { transform: 'rotate(-360deg)' },
        },
        'pulse-glow': {
          '0%, 100%': { opacity: '0.4', filter: 'drop-shadow(0 0 10px rgba(255, 30, 66, 0.4))' },
          '50%': { opacity: '0.9', filter: 'drop-shadow(0 0 25px rgba(255, 30, 66, 0.8))' },
        },
        'radar-sweep': {
          '0%': { transform: 'rotate(0deg)' },
          '100%': { transform: 'rotate(360deg)' },
        },
        'scanline': {
          '0%': { transform: 'translateY(-100%)' },
          '100%': { transform: 'translateY(1000%)' },
        }
      }
    },
  },
  plugins: [],
}
