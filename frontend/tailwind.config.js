/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        saathi: {
          50: "#e8f4f2",
          100: "#d4ebe8",
          200: "#a9d5cf",
          300: "#7dbbb3",
          500: "#2d8d87",
          600: "#267873",
          700: "#1f6864",
          800: "#194f50",
          900: "#123f4c"
        },
        ink: "#17232b",
        muted: "#66757e",
        line: "#dfe7ea"
      },
      boxShadow: {
        card: "0 12px 35px rgba(20,45,55,0.08)",
        float: "0 18px 45px rgba(20,45,55,0.16)"
      },
      borderRadius: {
        card: "18px"
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "-apple-system", "BlinkMacSystemFont", "Segoe UI", "sans-serif"]
      }
    }
  },
  plugins: []
};
