/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        google: {
          blue: "#4285F4",
          red: "#EA4335",
          yellow: "#FBBC05",
          green: "#34A853",
          darkBg: "#202124",
          darkSurface: "#303134",
          darkBorder: "#3c4043",
          darkText: "#bdc1c6",
          darkLink: "#8ab4f8",
          lightBg: "#ffffff",
          lightSurface: "#f8f9fa",
          lightBorder: "#dadce0",
          lightText: "#4d5156",
          lightLink: "#1a0dab",
        }
      },
      fontFamily: {
        sans: ['Roboto', 'Outfit', 'Arial', 'sans-serif'],
        product: ['Outfit', 'Google Sans', 'Roboto', 'sans-serif'],
      }
    },
  },
  plugins: [],
}