import typography from "@tailwindcss/typography";

/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        widget: "#214469",
        hwidget: "#1d3a59",
      },
    },
  },
  plugins: [typography],
};
