import type { Config } from "tailwindcss";

/**
 * VSA Tecnologia - Tailwind CSS Configuration
 * Design System "Obsidian v2.0" - Dark-first
 */
const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      fontFamily: {
        sans: ["var(--font-sans)", "Inter", "system-ui", "sans-serif"],
        display: ["var(--font-sans)", "Inter", "system-ui", "sans-serif"],
        mono: ["var(--font-mono)", "JetBrains Mono", "Fira Code", "Consolas", "monospace"],
      },
      colors: {
        obsidian: {
          950: "#050505",
          900: "#0a0a0a",
          800: "#121212",
          700: "#1a1a1a",
          600: "#262626",
          500: "#404040",
        },
        brand: {
          primary: "#F97316",
          "primary-dark": "#EA580C",
          "primary-light": "#FB923C",
          secondary: "#3B82F6",
          "secondary-dark": "#2563EB",
          "secondary-light": "#60A5FA",
        },
        // Aliases usados no código (vsa-orange, vsa-orange-dark, etc.)
        vsa: {
          orange: {
            DEFAULT: "#F97316",
            dark: "#EA580C",
            light: "#FB923C",
            lighter: "#FED7AA",
          },
          blue: {
            DEFAULT: "#3B82F6",
            dark: "#2563EB",
            light: "#60A5FA",
            lighter: "#BFDBFE",
          },
        },
        // Escala completa VSA (design system)
        "vsa-orange": {
          50: "#FFF7ED",
          100: "#FFEDD5",
          200: "#FED7AA",
          300: "#FDBA74",
          400: "#FB923C",
          500: "#F97316",
          600: "#EA580C",
          700: "#C2410C",
          800: "#9A3412",
          900: "#7C2D12",
        },
        "vsa-blue": {
          50: "#EFF6FF",
          100: "#DBEAFE",
          200: "#BFDBFE",
          300: "#93C5FD",
          400: "#60A5FA",
          500: "#3B82F6",
          600: "#2563EB",
          700: "#1D4ED8",
          800: "#1E40AF",
          900: "#1E3A8A",
        },
        "vsa-success": {
          light: "#D1FAE5",
          DEFAULT: "#10B981",
          dark: "#059669",
        },
        "vsa-error": {
          light: "#FEE2E2",
          DEFAULT: "#EF4444",
          dark: "#DC2626",
        },
      },
      backgroundImage: {
        "vsa-brand": "linear-gradient(135deg, #F97316 0%, #EA580C 40%, #3B82F6 100%)",
        "vsa-brand-hover": "linear-gradient(135deg, #EA580C 0%, #C2410C 40%, #2563EB 100%)",
        "vsa-soft": "linear-gradient(135deg, rgba(249, 115, 22, 0.1) 0%, rgba(59, 130, 246, 0.1) 100%)",
        "vsa-orange-gradient": "linear-gradient(135deg, #F97316 0%, #EA580C 50%, #FDBA74 100%)",
        "vsa-blue-gradient": "linear-gradient(135deg, #3B82F6 0%, #2563EB 50%, #60A5FA 100%)",
        "vsa-gradient": "linear-gradient(135deg, #F97316 0%, #EA580C 25%, #3B82F6 75%, #2563EB 100%)",
        "vsa-orange": "linear-gradient(180deg, #F97316 0%, #EA580C 100%)",
        "vsa-blue": "linear-gradient(180deg, #3B82F6 0%, #2563EB 100%)",
        "vsa-radial":
          "radial-gradient(circle at top right, rgba(249, 115, 22, 0.08), transparent 50%), radial-gradient(circle at bottom left, rgba(59, 130, 246, 0.06), transparent 50%)",
      },
      boxShadow: {
        "vsa-xs": "0 1px 2px rgba(0, 0, 0, 0.3)",
        "vsa-sm": "0 1px 3px rgba(0, 0, 0, 0.4), 0 1px 2px rgba(0, 0, 0, 0.2)",
        "vsa-md": "0 4px 6px rgba(0, 0, 0, 0.4), 0 2px 4px rgba(0, 0, 0, 0.3)",
        "vsa-lg": "0 10px 15px rgba(0, 0, 0, 0.5), 0 4px 6px rgba(0, 0, 0, 0.3)",
        "vsa-xl": "0 20px 25px rgba(0, 0, 0, 0.5), 0 8px 10px rgba(0, 0, 0, 0.3)",
        "vsa-2xl": "0 25px 50px rgba(0, 0, 0, 0.6)",
        "vsa-orange": "0 4px 14px rgba(249, 115, 22, 0.25)",
        "vsa-orange-lg": "0 8px 24px rgba(249, 115, 22, 0.35)",
        "vsa-blue": "0 4px 14px rgba(59, 130, 246, 0.25)",
        "vsa-blue-lg": "0 8px 24px rgba(59, 130, 246, 0.35)",
        "vsa-brand": "0 4px 14px rgba(249, 115, 22, 0.20), 0 4px 14px rgba(59, 130, 246, 0.15)",
        "vsa-inner": "inset 0 2px 4px rgba(0, 0, 0, 0.3)",
        "vsa-inner-lg": "inset 0 4px 8px rgba(0, 0, 0, 0.4)",
        "glow-brand": "0 0 40px -10px rgba(249, 115, 22, 0.4)",
        "glow-orange": "0 0 30px -5px rgba(249, 115, 22, 0.3)",
        "glow-orange-lg": "0 0 40px -10px rgba(249, 115, 22, 0.4)",
        "glow-blue": "0 0 30px -5px rgba(59, 130, 246, 0.3)",
        "glow-blue-lg": "0 0 40px -10px rgba(59, 130, 246, 0.4)",
        "glass-panel": "0 8px 32px 0 rgba(0, 0, 0, 0.37)",
      },
      borderRadius: {
        "vsa-sm": "0.25rem",
        "vsa-md": "0.375rem",
        "vsa-lg": "0.5rem",
        "vsa-xl": "0.75rem",
        "vsa-2xl": "1rem",
        "vsa-3xl": "1.5rem",
      },
      transitionDuration: {
        fast: "150ms",
        base: "200ms",
        slow: "300ms",
        slower: "500ms",
      },
      transitionTimingFunction: {
        "vsa-ease": "cubic-bezier(0.4, 0, 0.2, 1)",
        "vsa-bounce": "cubic-bezier(0.68, -0.55, 0.265, 1.55)",
      },
      animation: {
        "vsa-fade-in": "vsaFadeIn 0.3s ease-out",
        "vsa-slide-up": "vsaSlideUp 0.3s ease-out",
        "vsa-slide-down": "vsaSlideDown 0.3s ease-out",
        "vsa-scale": "vsaScale 0.2s ease-out",
        "vsa-pulse-orange": "vsaPulseOrange 2s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        "vsa-gradient": "vsaGradient 3s ease infinite",
        float: "float 6s ease-in-out infinite",
        "pulse-slow": "pulse-slow 4s cubic-bezier(0.4, 0, 0.6, 1) infinite",
      },
      keyframes: {
        vsaFadeIn: {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
        vsaSlideUp: {
          "0%": { opacity: "0", transform: "translateY(10px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        vsaSlideDown: {
          "0%": { opacity: "0", transform: "translateY(-10px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        vsaScale: {
          "0%": { opacity: "0", transform: "scale(0.95)" },
          "100%": { opacity: "1", transform: "scale(1)" },
        },
        vsaPulseOrange: {
          "0%, 100%": { boxShadow: "0 0 0 0 rgba(249, 115, 22, 0.4)" },
          "50%": { boxShadow: "0 0 0 8px rgba(249, 115, 22, 0)" },
        },
        vsaGradient: {
          "0%, 100%": { backgroundPosition: "0% 50%" },
          "50%": { backgroundPosition: "100% 50%" },
        },
        float: {
          "0%, 100%": { transform: "translateY(0)" },
          "50%": { transform: "translateY(-15px)" },
        },
        "pulse-slow": {
          "0%, 100%": { opacity: "0.4" },
          "50%": { opacity: "0.8" },
        },
      },
      zIndex: {
        dropdown: "1000",
        sticky: "1020",
        fixed: "1030",
        "modal-backdrop": "1040",
        modal: "1050",
        popover: "1060",
        tooltip: "1070",
      },
    },
  },
  plugins: [
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    function (api: any) {
      api.addUtilities({
        ".text-vsa-gradient": {
          background: "linear-gradient(135deg, #F97316 0%, #3B82F6 100%)",
          WebkitBackgroundClip: "text",
          WebkitTextFillColor: "transparent",
          backgroundClip: "text",
        },
      });
      api.addComponents({
        ".border-vsa-gradient": {
          position: "relative",
          background: "#0a0a0a",
          "&::before": {
            content: '""',
            position: "absolute",
            inset: "0",
            padding: "1px",
            background: "linear-gradient(135deg, #F97316, #3B82F6)",
            borderRadius: "inherit",
            WebkitMask: "linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0)",
            WebkitMaskComposite: "xor",
            maskComposite: "exclude",
            pointerEvents: "none",
          },
        },
      });
    },
  ],
};

export default config;
