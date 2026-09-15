/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        // Government of India Official Colors
        govBlue: "#0052CC",      // Primary government blue
        govSaffron: "#FF9933",   // Ashoka Chakra saffron
        govGreen: "#138808",     // Ashoka Chakra green
        govLight: "#F0F0F0",     // Official light background
        govDark: "#000000",      // Official dark text
        
        // Kept for backwards compatibility / legacy UI
        ink: "#0B1A33",
        ink2: "#132447",
        slate: "#4B5875",
        accent: "#0052CC",       // Now maps to govBlue
        accent2: "#003D99",
        
        // Status/Compliance Colors (government-compatible)
        pass: "#1B8A5A",
        passBg: "#E8F6EF",
        fail: "#C23B3B",
        failBg: "#FBEAEA",
        review: "#B7791F",
        reviewBg: "#FDF3E1",
        waived: "#9333EA",
        waivedBg: "#F3E8FF",
        draft: "#6B7280",
        draftBg: "#F3F4F6",
        
        // UI Neutrals
        canvas: "#F0F0F0",       // Updated to official light gray
        card: "#FFFFFF",
        line: "#E4E8F1",
        disabled: "#D1D5DB",
      },
      fontFamily: {
        display: ["'Georgia'", "'Noto Serif'", "serif"],  // Official serif for authority
        body: ["'Inter'", "system-ui", "sans-serif"],
        mono: ["'JetBrains Mono'", "monospace"],
      },
      borderRadius: {
        card: "4px",   // Updated to subtle government style
      },
    },
  },
  plugins: [],
};
