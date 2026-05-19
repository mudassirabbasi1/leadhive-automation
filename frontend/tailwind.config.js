/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Inter", "ui-sans-serif", "system-ui", "Segoe UI", "sans-serif"]
      },
      colors: {
        ink: "#14213d",
        honey: "#f4b942",
        leaf: "#2a9d8f",
        coral: "#e76f51"
      }
    }
  },
  plugins: []
};

