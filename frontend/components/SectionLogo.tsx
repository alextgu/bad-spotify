/**
 * Section 2 — the mark, rippling.
 *
 * FRAMEWORK ONLY. Not designed yet.
 *
 * The brief: the DJ orb, the way a streaming service animates its own DJ —
 * a mark that pulses and ripples as if it is listening. Premium and clean
 * everywhere except the character itself, which should be *slightly derpy*.
 * The product is an idiot; the packaging is not. That contrast is the joke,
 * and it only works if exactly one of the two is silly.
 *
 * Slots this reserves:
 *
 *   [orb]      the mark. Rings ripple outward on a slow loop.
 *   [face]     where the derp lives — eyes, a tilt, whatever reads as
 *              "eager and wrong". Currently two dots as a stand-in.
 *   [caption]  one line of character, in its own voice.
 *   [creed]    the three-beat statement.
 *
 * Ripple animation is `.orb-*` in globals.css: pure CSS, no dependency, and it
 * stops under prefers-reduced-motion.
 */
import { brand } from "@/lib/brand";

export default function SectionLogo() {
  return (
    <section
      id="logo"
      className="section-page flex flex-col items-center justify-center px-6 text-center"
    >
      {/* [orb] + [face] */}
      <div className="orb-stage" aria-hidden>
        <span className="orb-ripple" />
        <span className="orb-ripple orb-ripple-2" />
        <span className="orb-ripple orb-ripple-3" />
        <span className="orb-core">
          {/* [face] — placeholder derp. Two eyes, slightly off-centre. */}
          <span className="orb-eye orb-eye-l" />
          <span className="orb-eye orb-eye-r" />
        </span>
      </div>

      {/* [caption] */}
      <p className="mt-16 max-w-lg text-[clamp(1.25rem,2.6vw,1.75rem)] leading-snug tracking-[-0.02em]">
        “I’ve read the room. I’m ignoring it.”
      </p>

      {/* [creed] */}
      <div className="mt-10 space-y-1.5">
        {brand.creed.map((line, i) => (
          <p
            key={line}
            className={`text-sm ${
              i === brand.creed.length - 1 ? "text-ink-primary" : "text-ink-muted"
            }`}
          >
            {line}
          </p>
        ))}
      </div>
    </section>
  );
}
