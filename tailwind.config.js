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
        // Rentora Theme: Cream (#F3EEE3), Ink Black (#111111) & Burnt Orange (#D9541E)
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

        // Surfaces: Cream (#F3EEE3) Background with Crisp White Cards
        "surface": "#F3EEE3",
        "surface-dim": "#EAE4D7",
        "surface-bright": "#FAF7F2",
        "surface-container-lowest": "#ffffff",
        "surface-container-low": "#EFE9DC",
        "surface-container": "#EAE3D4",
        "surface-container-high": "#E4DCCC",
        "surface-container-highest": "#DED4C3",
        "surface-variant": "#EAE3D4",
        "surface-tint": "#D9541E",

        // Ink Black Typography (#111111)
        "on-surface": "#111111",
        "on-surface-variant": "#222222",
        "inverse-surface": "#111111",
        "inverse-on-surface": "#F3EEE3",
        "outline": "#787268",
        "outline-variant": "#DCD4C6",

        "background": "#F3EEE3",
        "on-background": "#111111",
        "cream": "#F3EEE3",
        "ink-black": "#111111",

        // Backward compatibility mappings
        "background-light": "#F3EEE3",
        "background-dark": "#111111",
      },
      fontFamily: {
        "display": ["Plus Jakarta Sans", "sans-serif"],
        "body": ["DM Sans", "sans-serif"],
        "headline-xl": ["Plus Jakarta Sans", "sans-serif"],
        "headline-lg": ["Plus Jakarta Sans", "sans-serif"],
        "headline-md": ["Plus Jakarta Sans", "sans-serif"],
        "headline-sm": ["Plus Jakarta Sans", "sans-serif"],
        "body-lg": ["DM Sans", "sans-serif"],
        "body-md": ["DM Sans", "sans-serif"],
        "body-sm": ["DM Sans", "sans-serif"],
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
