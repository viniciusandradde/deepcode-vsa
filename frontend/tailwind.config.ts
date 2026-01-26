import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["var(--font-sans)"],
        display: ["var(--font-display)"],
        mono: ["var(--font-mono)"],
      },
      colors: {
        vsa: {
          orange: {
            dark: "#FF6B35",
            DEFAULT: "#FF8C42",
            light: "#FFB347",
            lighter: "#FFA726",
          },
          blue: {
            dark: "#1E3A8A",
            DEFAULT: "#3B82F6",
            light: "#60A5FA",
            lighter: "#3B9EFF",
          },
        },
      },
      backgroundImage: {
        "vsa-orange-gradient": "linear-gradient(135deg, #FF6B35 0%, #FF8C42 50%, #FFB347 100%)",
        "vsa-blue-gradient": "linear-gradient(135deg, #1E3A8A 0%, #3B82F6 50%, #60A5FA 100%)",
        "vsa-gradient": "linear-gradient(135deg, #FF6B35 0%, #FF8C42 25%, #3B82F6 75%, #60A5FA 100%)",
      },
    },
  },
  plugins: [],
};

export default config;

