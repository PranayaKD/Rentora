/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./templates/**/*.html",
    "./static/**/*.js",
    "./core/**/*.py",
    "./accounts/**/*.py",
    "./ui_preview/**/*.py",
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        // Rentora Theme: Cream (#FDFBD6), Ink Black (#111111) & Burnt Orange (#D9541E)
        "primary": "#111111",
        "primary-dark": "#000000",
        "primary-light": "#222222",
        "on-primary": "#ffffff",
        "primary-container": "#111111",
        "on-primary-container": "#ffffff",
        "primary-fixed": "#e3e2e6",
        "primary-fixed-dim": "#c7c6ca",
        "on-primary-fixed": "#111111",
        "on-primary-fixed-variant": "#111111",
        "inverse-primary": "#c7c6ca",

        // Burnt Orange Buttons & Accents (#D9541E) with White Text
        "secondary": "#D9541E",
        "secondary-dark": "#C44714",
        "on-secondary": "#ffffff",
        "secondary-container": "#D9541E",
        "on-secondary-container": "#ffffff",
        "secondary-fixed": "#FCD8C7",
        "secondary-fixed-dim": "#C44714",
        "on-secondary-fixed": "#ffffff",
        "on-secondary-fixed-variant": "#ffffff",

        // Accent & Status
        "accent": "#D9541E",
        "accent-dark": "#C44714",
        "burnt-orange": "#D9541E",
        "go-green": "#10B981",
        "go-green-dark": "#059669",
        "tertiary": "#ffffff",
        "on-tertiary": "#111111",
        "tertiary-container": "#1a1c20",
        "on-tertiary-container": "#ffffff",

        "error": "#BA1A1A",
        "on-error": "#ffffff",
        "error-container": "#FFDAD6",
        "on-error-container": "#93000A",

        // Surfaces: All Cream (#FDFBD6) Palette - Zero Stark White Cards
        "surface": "#FDFBD6",
        "surface-dim": "#F5F1C4",
        "surface-bright": "#FEFDE0",
        "surface-container-lowest": "#FDFBD6",
        "surface-container-low": "#FAF7CE",
        "surface-container": "#F7F3C6",
        "surface-container-high": "#F1EDBE",
        "surface-container-highest": "#EBE6B6",
        "surface-variant": "#F7F3C6",
        "surface-tint": "#D9541E",

        // Ink Black Typography (#111111)
        "on-surface": "#111111",
        "on-surface-variant": "#222222",
        "inverse-surface": "#111111",
        "inverse-on-surface": "#FDFBD6",
        "outline": "#787268",
        "outline-variant": "#E5E0B0",

        "background": "#FDFBD6",
        "on-background": "#111111",
        "cream": "#FDFBD6",
        "ink-black": "#111111",

        // Backward compatibility mappings
        "background-light": "#FDFBD6",
        "background-dark": "#111111",
      },
      fontFamily: {
        "display": ["Epilogue", "sans-serif"],
        "headline": ["Epilogue", "sans-serif"],
        "headline-xl": ["Epilogue", "sans-serif"],
        "headline-lg": ["Epilogue", "sans-serif"],
        "headline-md": ["Epilogue", "sans-serif"],
        "headline-sm": ["Epilogue", "sans-serif"],
        "body": ["Plus Jakarta Sans", "sans-serif"],
        "body-lg": ["Plus Jakarta Sans", "sans-serif"],
        "body-md": ["Plus Jakarta Sans", "sans-serif"],
        "body-sm": ["Plus Jakarta Sans", "sans-serif"],
      },
      borderRadius: {
        "DEFAULT": "0.25rem",
        "md": "0.5rem",
        "lg": "0.75rem",
        "xl": "1rem",
        "2xl": "1.25rem",
        "3xl": "1.5rem",
        "full": "9999px"
      },
      spacing: {
        "margin": "1rem",
        "margin-desktop": "2.5rem",
        "margin-tablet": "1.5rem",
        "space-xs": "0.25rem",
        "space-sm": "0.5rem",
        "space-md": "1rem",
        "space-lg": "1.5rem",
        "space-xl": "2rem",
        "gutter": "1rem",
        "gutter-desktop": "1.5rem"
      }
    },
  },
  plugins: [
    require('@tailwindcss/forms'),
    require('@tailwindcss/container-queries'),
  ],
}
