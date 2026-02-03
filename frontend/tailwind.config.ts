import type { Config } from "tailwindcss";

/**
 * VSA Tecnologia - Tailwind CSS Configuration
 * Alinhado ao design system (vsa-design-tokens, tailwind.config.js raiz)
 */
const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      fontFamily: {
        sans: ["var(--font-sans)", "Inter", "Source Sans Pro", "system-ui", "sans-serif"],
        display: ["var(--font-display)", "Poppins", "Inter", "system-ui", "sans-serif"],
        mono: ["var(--font-mono)", "JetBrains Mono", "Fira Code", "Consolas", "monospace"],
        body: ["Inter", "Source Sans Pro", "system-ui", "sans-serif"],
      },
      colors: {
        // Aliases usados no código (vsa-orange, vsa-orange-dark, etc.)
        vsa: {
          orange: {
            DEFAULT: "#F7941D",
            dark: "#E8611A",
            light: "#FB923C",
            lighter: "#FED7AA",
          },
          blue: {
            DEFAULT: "#00AEEF",
            dark: "#0077B5",
            light: "#2CBFFF",
            lighter: "#B6E5FF",
          },
        },
        // Escala completa VSA (design system)
        "vsa-orange": {
          50: "#FFF7ED",
          100: "#FFEDD5",
          200: "#FED7AA",
          300: "#FDBA74",
          400: "#FB923C",
          500: "#F7941D",
          600: "#E8611A",
          700: "#C2410C",
          800: "#9A3412",
          900: "#7C2D12",
        },
        "vsa-blue": {
          50: "#EFF9FF",
          100: "#DEF1FF",
          200: "#B6E5FF",
          300: "#75D4FF",
          400: "#2CBFFF",
          500: "#00AEEF",
          600: "#0077B5",
          700: "#0369A1",
          800: "#075985",
          900: "#0C4A6E",
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
        "vsa-brand": "linear-gradient(135deg, #F7941D 0%, #E8611A 40%, #00AEEF 100%)",
        "vsa-brand-hover": "linear-gradient(135deg, #E8611A 0%, #C2410C 40%, #0077B5 100%)",
        "vsa-soft": "linear-gradient(135deg, #FFF7ED 0%, #EFF9FF 100%)",
        "vsa-orange-gradient": "linear-gradient(135deg, #F7941D 0%, #E8611A 50%, #FDBA74 100%)",
        "vsa-blue-gradient": "linear-gradient(135deg, #00AEEF 0%, #0077B5 50%, #2CBFFF 100%)",
        "vsa-gradient": "linear-gradient(135deg, #F7941D 0%, #E8611A 25%, #00AEEF 75%, #0077B5 100%)",
        "vsa-orange": "linear-gradient(180deg, #F7941D 0%, #E8611A 100%)",
        "vsa-blue": "linear-gradient(180deg, #00AEEF 0%, #0077B5 100%)",
        "vsa-radial":
          "radial-gradient(circle at top right, rgba(247, 148, 29, 0.1), transparent 50%), radial-gradient(circle at bottom left, rgba(0, 174, 239, 0.1), transparent 50%)",
      },
      boxShadow: {
        "vsa-xs": "0 1px 2px rgba(24, 24, 27, 0.05)",
        "vsa-sm": "0 1px 3px rgba(24, 24, 27, 0.08), 0 1px 2px rgba(24, 24, 27, 0.04)",
        "vsa-md": "0 4px 6px rgba(24, 24, 27, 0.07), 0 2px 4px rgba(24, 24, 27, 0.05)",
        "vsa-lg": "0 10px 15px rgba(24, 24, 27, 0.08), 0 4px 6px rgba(24, 24, 27, 0.04)",
        "vsa-xl": "0 20px 25px rgba(24, 24, 27, 0.10), 0 8px 10px rgba(24, 24, 27, 0.04)",
        "vsa-2xl": "0 25px 50px rgba(24, 24, 27, 0.18)",
        "vsa-orange": "0 4px 14px rgba(247, 148, 29, 0.25)",
        "vsa-orange-lg": "0 8px 24px rgba(247, 148, 29, 0.35)",
        "vsa-blue": "0 4px 14px rgba(0, 174, 239, 0.25)",
        "vsa-blue-lg": "0 8px 24px rgba(0, 174, 239, 0.35)",
        "vsa-brand": "0 4px 14px rgba(247, 148, 29, 0.20), 0 4px 14px rgba(0, 174, 239, 0.15)",
        "vsa-inner": "inset 0 2px 4px rgba(24, 24, 27, 0.05)",
        "vsa-inner-lg": "inset 0 4px 8px rgba(24, 24, 27, 0.08)",
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
          "0%, 100%": { boxShadow: "0 0 0 0 rgba(247, 148, 29, 0.4)" },
          "50%": { boxShadow: "0 0 0 8px rgba(247, 148, 29, 0)" },
        },
        vsaGradient: {
          "0%, 100%": { backgroundPosition: "0% 50%" },
          "50%": { backgroundPosition: "100% 50%" },
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
          background: "linear-gradient(135deg, #F7941D 0%, #00AEEF 100%)",
          WebkitBackgroundClip: "text",
          WebkitTextFillColor: "transparent",
          backgroundClip: "text",
        },
      });
      api.addComponents({
        ".border-vsa-gradient": {
          position: "relative",
          background: "white",
          "&::before": {
            content: '""',
            position: "absolute",
            inset: "0",
            padding: "2px",
            background: "linear-gradient(135deg, #F7941D, #00AEEF)",
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
