/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: '#09090b', // zinc-950
        surface: '#18181b', // zinc-900
        primary: '#3b82f6', // blue-500
        textPrimary: '#fafafa', // zinc-50
        textSecondary: '#a1a1aa', // zinc-400
        critical: '#ef4444', // red-500
        okay: '#10b981', // emerald-500
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
      }
    },
  },
  plugins: [],
}
