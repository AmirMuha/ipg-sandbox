import type { Config } from "tailwindcss";

/**
 * Tailwind runs at the defaults, with one job: layout and spacing utilities.
 *
 * There is deliberately NO colour or type extension here. The design is a plain
 * CSS layer (styles/tokens.css + ui.css + console.css + marketing.css) whose
 * classes are applied directly in JSX, so Tailwind never needs to know a colour
 * name. The previous config mirrored the whole palette as
 * `rgb(var(--x) / <alpha-value>)`, which meant two palettes to keep in sync and
 * no build error when they drifted — and a token that stopped existing emitted
 * nothing, silently.
 *
 * If you add a Tailwind colour here, it will not follow tokens.css. Prefer a
 * design class.
 */
const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {},
  },
  plugins: [],
};

export default config;
