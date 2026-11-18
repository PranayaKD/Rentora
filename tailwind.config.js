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
        // Rentora Unified Design System: Signature Warm Orange & Crisp Pure White
        // Primary Brand: Rentora Warm Orange (#FF5F00)
        "primary": "#FF5F00",
        "primary-dark": "#E05300",
        "primary-light": "#FF7A29",
        "on-primary": "#ffffff",
        "primary-container": "#FFF2EA",
        "on-primary-container": "#9E3400",
        "primary-fixed": "#FFDBCF",
        "primary-fixed-dim": "#FFB59A",
        "on-primary-fixed": "#380D00",
        "on-primary-fixed-variant": "#7A2700",
        "inverse-primary": "#FFB59A",

        // Secondary: Neutral Slate & Charcoal
        "charcoal": "#0F172A",
        "cool-gray": "#64748B",
        "secondary": "#64748B",
        "on-secondary": "#ffffff",
        "secondary-container": "#F1F5F9",
        "on-secondary-container": "#0F172A",
        "secondary-fixed": "#E2E8F0",
        "secondary-fixed-dim": "#CBD5E1",
        "on-secondary-fixed": "#0F172A",
        "on-secondary-fixed-variant": "#334155",

        // Accent: Pure Rentora Orange & Subtle Emerald Status
        "accent": "#FF5F00",
        "accent-dark": "#E05300",
        "go-green": "#10B981",
        "go-green-dark": "#059669",
        "tertiary": "#10B981",
        "on-tertiary": "#ffffff",
        "tertiary-container": "#DCFCE7",
        "on-tertiary-container": "#14532D",

        "error": "#EF4444",
        "on-error": "#ffffff",
        "error-container": "#FEE2E2",
        "on-error-container": "#991B1B",

        // Surfaces: Pure White by default with crisp 1px borders
        "surface": "#ffffff",
        "surface-dim": "#f8fafc",
        "surface-bright": "#ffffff",
        "surface-container-lowest": "#ffffff",
        "surface-container-low": "#ffffff",
        "surface-container": "#f8fafc",
        "surface-container-high": "#f1f5f9",
        "surface-container-highest": "#e2e8f0",
        "surface-variant": "#f1f5f9",
        "surface-tint": "#FF5F00",

        "on-surface": "#0F172A",
        "on-surface-variant": "#475569",
        "inverse-surface": "#0F172A",
        "inverse-on-surface": "#ffffff",
        "outline": "#CBD5E1",
        "outline-variant": "#E2E8F0",

        "background": "#ffffff",
        "on-background": "#0F172A",

        // Backward compatibility mappings
        "background-light": "#ffffff",
        "background-dark": "#0F172A",
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
