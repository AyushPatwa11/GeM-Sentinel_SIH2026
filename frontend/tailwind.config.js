/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#0B1A33",       // deep navy — sidebar / hero
        ink2: "#132447",
        slate: "#4B5875",
        accent: "#2F5DE8",    // signal blue — primary actions, links
        accent2: "#1B3FA6",
        pass: "#1B8A5A",
        passBg: "#E8F6EF",
        fail: "#C23B3B",
        failBg: "#FBEAEA",
        review: "#B7791F",
        reviewBg: "#FDF3E1",
        canvas: "#F6F7FB",
        card: "#FFFFFF",
        line: "#E4E8F1",
      },
      fontFamily: {
        display: ["'Space Grotesk'", "system-ui", "sans-serif"],
        body: ["'Inter'", "system-ui", "sans-serif"],
        mono: ["'JetBrains Mono'", "monospace"],
      },
      borderRadius: {
        card: "10px",
      },
    },
  },
  plugins: [],
};
