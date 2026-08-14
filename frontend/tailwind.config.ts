import type { Config } from "tailwindcss";

/**
 * The whole design system. If a value isn't in here it doesn't go in a
 * component — see DESIGN_RULES.md. One-off values are how a page ends up with
 * eleven font sizes and reads as generated.
 */
export default {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        plane: "#0d0d0d",
        surface: { 1: "#1a1a19", 2: "#212120" },
        // Three greys. Not four.
        ink: { primary: "#ffffff", secondary: "#c3c2b7", muted: "#898781" },
        line: "#2c2c2a",
        scene: "#3987e5", // the world as it is
        target: "#d95926", // what we do about it
        critical: "#d03b3b",
        good: "#0ca30c",
      },

      /**
       * Five sizes. Nothing between them. Each carries its own tracking,
       * weight and leading, so `text-heading` is the entire decision and one
       * section heading cannot drift a step away from another.
       */
      fontSize: {
        display: [
          "clamp(3rem, 8vw, 6rem)",
          { lineHeight: "1", letterSpacing: "-0.04em", fontWeight: "600" },
        ],
        heading: [
          "clamp(2rem, 4.5vw, 3.25rem)",
          { lineHeight: "1.1", letterSpacing: "-0.035em", fontWeight: "600" },
        ],
        subheading: [
          "1.25rem",
          { lineHeight: "1.4", letterSpacing: "-0.02em", fontWeight: "500" },
        ],
        body: ["1rem", { lineHeight: "1.65", letterSpacing: "0", fontWeight: "400" }],
        caption: [
          "0.8125rem",
          { lineHeight: "1.5", letterSpacing: "0", fontWeight: "400" },
        ],
      },

      /** One rhythm. Each gap has exactly one correct value. */
      spacing: {
        section: "10rem", // 160px — vertical section padding, desktop
        "section-sm": "6rem", // 96px — below md
        "heading-sub": "1rem", // 16px — heading to its subline
        "sub-content": "4rem", // 64px — subline to content
        card: "0.75rem", // 12px — inside a card
        play: "76px", // the play affordance on a video poster
      },

      /** Eyebrow type is letter-spaced; that is a decision, so it is a token. */
      letterSpacing: {
        eyebrow: "0.2em",
      },

      width: { banner: "min(92vw, 44rem)" },
      minWidth: { diagram: "700px" }, // the pipeline SVG's legible floor
      height: { "hero-slot": "38vh" }, // the hero image slot, until there's art

      maxWidth: {
        content: "1120px", // the column everything sits in
        measure: "65ch", // body text never exceeds this
        "measure-sub": "45ch", // sublines never exceed this
      },

      /** If you can see the border, it's too strong. */
      borderColor: {
        DEFAULT: "rgba(255,255,255,0.08)",
        subtle: "rgba(255,255,255,0.08)",
        strong: "rgba(255,255,255,0.14)",
      },

      /** One curve, three durations. Nothing else, anywhere. */
      transitionTimingFunction: {
        brand: "cubic-bezier(0.21, 0.47, 0.32, 0.98)",
      },
      transitionDuration: {
        reveal: "700ms",
        interaction: "250ms",
        colour: "1400ms",
      },

      fontFamily: {
        sans: ["system-ui", "-apple-system", "Segoe UI", "sans-serif"],
        mono: ["ui-monospace", "SFMono-Regular", "Menlo", "monospace"],
      },
    },
  },
  plugins: [],
} satisfies Config;
