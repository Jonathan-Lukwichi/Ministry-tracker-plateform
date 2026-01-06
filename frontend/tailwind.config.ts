import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: ["class"],
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        // Dark Theme - Primary Navy Background
        dark: {
          DEFAULT: "#0a1628",
          50: "#1a2942",
          100: "#152238",
          200: "#111c30",
          300: "#0d1624",
          400: "#0a1219",
          500: "#080f14",
          600: "#060b10",
          700: "#04080c",
          800: "#020408",
          900: "#000204",
        },
        // Accent - Cyan/Teal
        accent: {
          DEFAULT: "#00d4ff",
          light: "#5ce1ff",
          dark: "#00a8cc",
          50: "#e6fbff",
          100: "#ccf7ff",
          200: "#99efff",
          300: "#66e7ff",
          400: "#33dfff",
          500: "#00d4ff",
          600: "#00a8cc",
          700: "#007f99",
          800: "#005566",
          900: "#002a33",
        },
        // Pink/Magenta for markers
        marker: {
          DEFAULT: "#ff3e7f",
          light: "#ff6b9d",
          dark: "#cc2a5f",
        },
        // Primary Colors - Deep Purple (kept for compatibility)
        primary: {
          DEFAULT: "#00d4ff",
          light: "#5ce1ff",
          dark: "#00a8cc",
          50: "#e6fbff",
          100: "#ccf7ff",
          200: "#99efff",
          300: "#66e7ff",
          400: "#33dfff",
          500: "#00d4ff",
          600: "#00a8cc",
          700: "#007f99",
          800: "#005566",
          900: "#002a33",
        },
        // Secondary Colors - Gold/Yellow
        secondary: {
          DEFAULT: "#ffd700",
          light: "#ffe44d",
          dark: "#ccac00",
          50: "#fffde7",
          100: "#fff9c4",
          200: "#fff59d",
          300: "#fff176",
          400: "#ffee58",
          500: "#ffeb3b",
          600: "#fdd835",
          700: "#fbc02d",
          800: "#f9a825",
          900: "#f57f17",
        },
        // Platform Colors
        youtube: "#FF0000",
        facebook: "#1877F2",
        // Status Colors (adjusted for dark theme)
        success: "#10b981",
        warning: "#f59e0b",
        danger: "#ef4444",
        info: "#3b82f6",
        // Health Score Colors
        health: {
          good: "#10b981",
          moderate: "#f59e0b",
          high: "#ef4444",
        },
        // Dark Theme Surfaces
        surface: "#0f1f35",
        background: "#0a1628",
        border: "#1e3a5f",
        // Text colors
        "text-primary": "#e2e8f0",
        "text-secondary": "#94a3b8",
        "text-muted": "#64748b",
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
      },
      boxShadow: {
        card: "0 4px 20px rgba(0, 0, 0, 0.3)",
        "card-hover": "0 8px 30px rgba(0, 212, 255, 0.15)",
        glow: "0 0 20px rgba(0, 212, 255, 0.3)",
        "glow-pink": "0 0 15px rgba(255, 62, 127, 0.5)",
      },
      borderRadius: {
        xl: "12px",
        "2xl": "16px",
      },
      backgroundImage: {
        "gradient-radial": "radial-gradient(var(--tw-gradient-stops))",
        "dark-gradient": "linear-gradient(135deg, #0a1628 0%, #0f1f35 50%, #1a2942 100%)",
      },
    },
  },
  plugins: [],
};

export default config;
