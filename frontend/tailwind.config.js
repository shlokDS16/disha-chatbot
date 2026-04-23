/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        disha: {
          50: "#fef7ee",
          100: "#fdecd7",
          200: "#fbd5ae",
          300: "#f8b77b",
          400: "#f48e45",
          500: "#f06e22",
          600: "#e15518",
          700: "#bb4017",
          800: "#95341b",
          900: "#782c19",
          950: "#41140a",
        },
        saffron: {
          DEFAULT: "#ff9933",
          soft: "#ffb366",
        },
        leaf: {
          DEFAULT: "#138808",
          soft: "#4eac45",
        },
        ink: {
          DEFAULT: "#1c1917",
          soft: "#44403c",
          muted: "#78716c",
        },
        paper: {
          DEFAULT: "#fffdf8",
          warm: "#fef9f0",
          muted: "#f6f1e7",
        },
      },
      fontFamily: {
        sans: [
          "Inter",
          "system-ui",
          "-apple-system",
          "Segoe UI",
          "Noto Sans Devanagari",
          "sans-serif",
        ],
        display: ["Plus Jakarta Sans", "Inter", "system-ui", "sans-serif"],
      },
      borderRadius: {
        "2xl": "1rem",
        "3xl": "1.5rem",
      },
      boxShadow: {
        soft: "0 2px 20px -4px rgba(24, 16, 10, 0.08)",
        card: "0 4px 30px -8px rgba(24, 16, 10, 0.12)",
      },
      keyframes: {
        "fade-in-up": {
          "0%": { opacity: "0", transform: "translateY(6px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        pulse1: {
          "0%, 80%, 100%": { opacity: "0.3", transform: "scale(0.8)" },
          "40%": { opacity: "1", transform: "scale(1)" },
        },
      },
      animation: {
        "fade-in-up": "fade-in-up 0.25s ease-out",
        "bounce-dot": "pulse1 1.2s infinite ease-in-out",
      },
    },
  },
  plugins: [],
};
