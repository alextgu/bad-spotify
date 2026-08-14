import type { Config } from "tailwindcss";

// Same palette as the agent's own screens, so the site and the running
// product look like one thing. Validated for contrast on the dark surface.
export default {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      // Every colour resolves to a CSS variable defined in app/globals.css.
      // Nothing here is a literal, so a redesign is one file, and the dark
      // agent screens keep working via [data-theme="dark"].
      colors: {
        plane: "var(--plane)",
        surface: { 1: "var(--surface-1)", 2: "var(--surface-2)" },
        ink: {
          primary: "var(--ink-primary)",
          secondary: "var(--ink-secondary)",
          muted: "var(--ink-muted)",
        },
        line: { DEFAULT: "var(--line)", strong: "var(--line-strong)" },
        scene: "var(--scene)",    // what the world IS
        target: "var(--target)",  // what we're about to do about it
        critical: "var(--critical)",
        good: "var(--good)",
      },
      fontFamily: {
        sans: ["system-ui", "-apple-system", "Segoe UI", "sans-serif"],
        mono: ["ui-monospace", "SFMono-Regular", "Menlo", "monospace"],
      },
    },
  },
  plugins: [],
} satisfies Config;
