import type { Config } from "tailwindcss";

/**
 * The whole design system. If a value isn't in here it doesn't go in a
 * component. One-off values are how a page ends up with eleven font sizes and
 * reads as generated.
 *
 * ---------------------------------------------------------------------------
 * TWO PALETTES LIVE HERE, ON PURPOSE, AND ONE OF THEM IS LEAVING
 * ---------------------------------------------------------------------------
 * The landing page was restarted on paper — warm off-white, serif display,
 * quiet accents. `/demo` was not: it is still the old dark surface, and its
 * components (`MomentCard`, `Timeline`) still read `plane`, `surface`,
 * `ink-primary/secondary/muted` and the old five type sizes.
 *
 * Those legacy tokens are kept below under LEGACY so a working page doesn't
 * break for a design change it wasn't part of. When `/demo` is redesigned,
 * delete that block — nothing else should be reaching for it.
 *
 * Everything above LEGACY is the new system. Use only that on new work.
 */
export default {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        /* --------------------------------------------------------- paper --
           Nothing here is pure. #FFFFFF and #000000 are the two colours that
           make a page read as unconsidered — they are what you get when
           nobody chose. Every value below is warmed a few degrees, which is
           most of the difference between "clean" and "clinical". */
        paper: "#FBFAF8",
        bone: "#F2EFE9",
        hairline: "#E3DED4",
        graphite: "#79736A",

        /* `ink` has a DEFAULT so `text-ink` is the new near-black, while
           `text-ink-muted` and friends keep working for /demo. */
        ink: {
          DEFAULT: "#1A1917",
          /* LEGACY — /demo only. */
          primary: "#ffffff",
          secondary: "#c3c2b7",
          muted: "#898781",
        },

        /* ------------------------------------------------------ the pair --
           Two colours carrying one idea:

             phase   the world as it is        (what was read)
             offset  what we do about it       (what was played)

           `offset` is green, because the product is placed against streaming
           DJs and the category reads green. It is deliberately NOT Spotify's
           #1DB954 — near enough to sit in the same family, far enough that we
           are not shipping someone else's brand colour. Ours is a degree
           cooler and a shade deeper.

           Two tints, because one green cannot do both jobs: DEFAULT is for
           fills and for type on dark, where it is bright enough to read;
           `ink` is for small type on paper, where DEFAULT would sit around
           2.3:1 and fail. Use `text-offset-ink` on the paper sections and
           `text-offset` on the dark ones. */
        phase: "#2E4A6E",
        offset: {
          DEFAULT: "#1CA85C",
          ink: "#0C7A40",
        },

        /* LEGACY — /demo only. */
        plane: "#0d0d0d",
        surface: { 1: "#1a1a19", 2: "#212120" },
        line: "#2c2c2a",
        scene: "#3987e5",
        target: "#d95926",
        critical: "#d03b3b",
        good: "#0ca30c",
      },

      /**
       * Five sizes, each carrying its own tracking, weight and leading, so
       * `text-headline` is the entire decision.
       *
       * Reweighted when the serif was dropped. A serif carries a headline at
       * weight 400; a geometric grotesk at 400 just looks unset, so display
       * and headline sit at 600 — enough to have presence, short of the 800
       * that made the original mockup shout. Tracking tightens a little too:
       * geometric faces set loose at large sizes look like a slide deck.
       */
      fontSize: {
        /* `min(vw, vh)`, not `vw` alone.
           Every section is exactly one viewport tall, so type that grows only
           with WIDTH will overflow a wide, short screen -- and `Screen` clips
           it, which is the bug you can see on a 1080p laptop: the last row of
           a section disappears behind the next one, mid-sentence. Sizing off
           whichever axis is scarcer keeps the one-screen rule true on a
           16:10 laptop and on an ultrawide alike, without shrinking the type
           on the displays where it does fit. */
        display: [
          "clamp(2.75rem, min(6.6vw, 8.6vh), 5.75rem)",
          { lineHeight: "1.02", letterSpacing: "-0.032em", fontWeight: "600" },
        ],
        headline: [
          "clamp(1.9rem, min(3.9vw, 5.2vh), 3.4rem)",
          { lineHeight: "1.08", letterSpacing: "-0.028em", fontWeight: "600" },
        ],
        title: [
          "1.3125rem",
          { lineHeight: "1.3", letterSpacing: "-0.016em", fontWeight: "600" },
        ],
        body: [
          "1.0625rem",
          { lineHeight: "1.65", letterSpacing: "0", fontWeight: "400" },
        ],
        caption: [
          "0.9375rem",
          { lineHeight: "1.5", letterSpacing: "0", fontWeight: "400" },
        ],
        /* The mono label. Small, wide, and always uppercase. */
        label: [
          "0.65625rem",
          { lineHeight: "1.4", letterSpacing: "0.2em", fontWeight: "500" },
        ],

        /* LEGACY — /demo only. */
        heading: [
          "clamp(2rem, 4.5vw, 3.25rem)",
          { lineHeight: "1.1", letterSpacing: "-0.035em", fontWeight: "600" },
        ],
        subheading: [
          "1.25rem",
          { lineHeight: "1.4", letterSpacing: "-0.02em", fontWeight: "500" },
        ],
      },

      /**
       * One rhythm. The jump from `block` to `section` is deliberately large —
       * peacefulness is mostly a function of how much room an idea is given
       * before the next one arrives, not of how slowly things animate.
       */
      spacing: {
        gutter: "1.5rem", // 24px — page edge
        /* The three vertical steps give height back on a short screen.
           Same reason as the type above: a section is one viewport, so a
           rhythm fixed in rem is a rhythm that overflows a laptop. The
           maximum is unchanged, so nothing moves on the displays where the
           page already looked right -- these only compress when there is
           genuinely no room, instead of clipping a paragraph in half. */
        block: "clamp(1.5rem, 3.2vh, 2.5rem)", // 40px — heading to its body
        rest: "clamp(2.25rem, 5.6vh, 4.5rem)", // 72px — between grouped items
        section: "13.75rem", // 220px — between sections, desktop
        "section-sm": "clamp(3rem, 8vh, 7rem)", // 112px — below md
        card: "0.75rem",
        play: "76px",
        /* LEGACY — /demo only. */
        "heading-sub": "1rem",
        "sub-content": "4rem",
      },

      letterSpacing: { eyebrow: "0.2em" },

      width: { banner: "min(92vw, 44rem)" },
      minWidth: { diagram: "700px" },
      height: { "hero-slot": "38vh" },

      maxWidth: {
        content: "1320px", // the column everything sits in
        measure: "62ch", // body text never exceeds this
        "measure-sub": "45ch",
        statement: "21ch", // a display line that is meant to break, in 3s
      },

      borderColor: {
        DEFAULT: "#E3DED4",
        hairline: "#E3DED4",
        /* LEGACY — /demo only. */
        subtle: "rgba(255,255,255,0.08)",
        strong: "rgba(255,255,255,0.14)",
      },

      borderRadius: {
        card: "1.125rem",
        frame: "1.625rem", // the inset hero card
      },

      /**
       * ONE curve, and it is the whole motion language.
       *
       * The previous pass used `expo.out` everywhere: violent start, dead
       * stop. This is the opposite shape — it leaves gently and spends most
       * of its time arriving. Nothing on this page should ever look like it
       * is in a hurry to finish.
       */
      transitionTimingFunction: {
        calm: "cubic-bezier(0.32, 0.72, 0, 1)",
        /* LEGACY — /demo only. */
        brand: "cubic-bezier(0.21, 0.47, 0.32, 0.98)",
      },
      transitionDuration: {
        reveal: "1600ms",
        slow: "2200ms",
        interaction: "600ms",
        /* LEGACY — /demo only. */
        colour: "1400ms",
      },

      fontFamily: {
        /* Set by next/font in app/layout.tsx; these are the CSS variables.
           `display` and `sans` are the same family on purpose — see the note
           in layout.tsx. `font-display` is kept as a separate name so that
           swapping the headline face later is one line here. */
        display: ["var(--font-display)", "system-ui", "sans-serif"],
        sans: ["var(--font-display)", "system-ui", "sans-serif"],
        mono: ["var(--font-mono)", "ui-monospace", "monospace"],
      },
    },
  },
  plugins: [],
} satisfies Config;
