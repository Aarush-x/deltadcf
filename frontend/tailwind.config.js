/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        surface: "#121414",
        "surface-container": "#1e2020",
        "on-surface": "#e2e2e2",
        "on-surface-variant": "#c2c6d6",
        outline: "#8c909f",
        primary: "#adc6ff",
        secondary: "#4edea3",
        tertiary: "#ffb3ad",
        background: "#000000",
        "border-terminal": "#1F1F1F",
        "nested-bg": "#0A0A0A",
        "text-dim": "#8c909f",
        critical: "#ef4444",
        warning: "#fbbf24",
        success: "#34d399",
        "action-blue": "#3B82F6",
      },
      fontFamily: {
        "body-md": ["Hanken Grotesk", "sans-serif"],
        "data-md": ["JetBrains Mono", "monospace"],
        "data-lg": ["JetBrains Mono", "monospace"],
        "data-sm": ["JetBrains Mono", "monospace"],
        "headline-sm": ["Hanken Grotesk", "sans-serif"],
        "label-xs": ["Hanken Grotesk", "sans-serif"],
      },
      fontSize: {
        "body-md": ["13px", { lineHeight: "18px", fontWeight: "400" }],
        "data-md": ["13px", { lineHeight: "16px", fontWeight: "400" }],
        "data-lg": ["24px", { lineHeight: "32px", fontWeight: "500" }],
        "data-sm": ["11px", { lineHeight: "14px", letterSpacing: "0.02em", fontWeight: "400" }],
        "headline-sm": ["18px", { lineHeight: "24px", letterSpacing: "-0.01em", fontWeight: "600" }],
        "label-xs": ["11px", { lineHeight: "14px", letterSpacing: "0.02em", fontWeight: "500" }],
      },
      borderRadius: {
        DEFAULT: "0px",
        lg: "0px",
        xl: "0px",
      },
      keyframes: {
        shimmer: {
          "0%": { backgroundPosition: "-200% 0" },
          "100%": { backgroundPosition: "200% 0" },
        },
        scanProgress: {
          "0%": { width: "0%" },
          "100%": { width: "95%" },
        },
      },
      animation: {
        shimmer: "shimmer 1.5s ease-in-out infinite",
        "scan-progress": "scanProgress 7s ease-out forwards",
      },
    },
  },
  plugins: [],
};
