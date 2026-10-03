import type { Config } from "tailwindcss";

// Colors are bare RGB channels (see theme.css) so every token can take an
// opacity modifier — `rgb(var(--success) / <alpha-value>)`. Declaring them as
// plain `var(--success)` makes Tailwind emit nothing at all for `bg-success/10`.
const token = (name: string) => `rgb(var(--${name}) / <alpha-value>)`;

const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        bg: token("bg"),
        surface: { DEFAULT: token("surface"), subtle: token("surface-subtle"), elevated: token("surface-elevated") },
        "surface-2": token("surface-2"),
        border: { DEFAULT: token("border"), soft: token("border-soft") },
        text: { DEFAULT: token("text"), 2: token("text-2") },
        muted: token("muted"),
        accent: {
          DEFAULT: token("accent"),
          on: token("accent-on"),
          ink: token("accent-ink"),
          subtle: token("accent-subtle"),
          border: token("accent-border"),
        },
        success: {
          DEFAULT: token("success"),
          bg: token("success-bg"),
          ink: token("success-ink"),
          border: token("success-border"),
        },
        warning: {
          DEFAULT: token("warning"),
          bg: token("warning-bg"),
          ink: token("warning-ink"),
          border: token("warning-border"),
        },
        danger: {
          DEFAULT: token("danger"),
          bg: token("danger-bg"),
          ink: token("danger-ink"),
          border: token("danger-border"),
        },
      },
      fontFamily: {
        display: ["var(--font-display)"],
        body: ["var(--font-body)"],
        mono: ["var(--font-mono)"],
      },
      fontSize: {
        xs: "var(--text-xs)",
        sm: "var(--text-sm)",
        base: "var(--text-base)",
        lg: "var(--text-lg)",
        xl: "var(--text-xl)",
        "2xl": "var(--text-2xl)",
      },
      borderRadius: {
        sm: "var(--radius-sm)",
        md: "var(--radius-md)",
        lg: "var(--radius-lg)",
        pill: "var(--radius-pill)",
        console: "8px",
      },
      letterSpacing: {
        display: "var(--tracking-display)",
      },
      boxShadow: {
        raised: "var(--elev-raised)",
      },
      transitionTimingFunction: {
        standard: "var(--ease-standard)",
      },
      transitionDuration: {
        fast: "150ms",
        base: "240ms",
      },
      maxWidth: {
        console: "1480px",
      },
    },
  },
  plugins: [],
};

export default config;