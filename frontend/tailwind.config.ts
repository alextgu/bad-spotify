import type { Config } from "tailwindcss";

export default {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        plane: "#0d0d0d",
        surface: { 1: "#1a1a19", 2: "#212120" },
        ink: { primary: "#ffffff", secondary: "#c3c2b7", muted: "#898781" },
        line: "#2c2c2a",
        scene: "#3987e5",
        target: "#d95926",
        critical: "#d03b3b",
        good: "#0ca30c",
      },
      fontFamily: {
        sans: ["system-ui", "-apple-system", "Segoe UI", "sans-serif"],
        mono: ["ui-monospace", "SFMono-Regular", "Menlo", "monospace"],
      },
    },
  },
  plugins: [],
} satisfies Config;
