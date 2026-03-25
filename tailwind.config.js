/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./templates/**/*.html",
    "./static/**/*.js",
    "./core/**/*.py",
    "./accounts/**/*.py",
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        "primary": "#0a0f1f",
        "accent": "#00c9a7",
        "background-light": "#f6f6f8",
        "background-dark": "#14161e",
      },
      fontFamily: {
        "display": ["Plus Jakarta Sans", "sans-serif"],
        "body": ["DM Sans", "sans-serif"]
      },
      borderRadius: {
        "DEFAULT": "1rem",
        "lg": "2rem",
        "xl": "3rem",
        "full": "9999px"
      },
    },
  },
  plugins: [
    require('@tailwindcss/forms'),
    require('@tailwindcss/container-queries'),
  ],
}
