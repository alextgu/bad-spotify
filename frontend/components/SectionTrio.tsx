import Reveal from "@/components/Reveal";
import { trio } from "@/lib/site";

/**
 * 3 — what it does, in three moves.
 *
 * Drawn rather than illustrated: three small SVGs built from the same two
 * marks — a dot, and a ring leaving it. The third glyph is the argument of the
 * whole product in one picture, two sources emitting where one of them is the
 * accent colour.
 *
 * The rings breathe at 11 seconds (see `.ripple` in globals.css). At the
 * mockup's 4.6s they read as a signal-strength indicator; this slow they read
 * as something listening.
 */

function Glyph({ children }: { children: React.ReactNode }) {
  return (
    <div className="mb-rest grid h-[74px] place-items-center">
      <svg viewBox="0 0 90 74" className="h-[74px] overflow-visible" aria-hidden>
        {children}
      </svg>
    </div>
  );
}

export default function SectionTrio() {
  return (
    <section className="mx-auto max-w-content px-gutter pb-section-sm md:pb-section">
      <div className="grid gap-section-sm md:grid-cols-3 md:gap-rest">
        <Reveal className="text-center">
          <Glyph>
            <g transform="translate(45,37)">
              <circle className="ripple stroke-ink opacity-25" />
              <circle
                className="ripple stroke-ink opacity-25"
                style={{ animationDelay: "3.6s" }}
              />
              <circle r="2.5" className="fill-ink" />
            </g>
          </Glyph>
          <h3 className="font-display text-title">{trio[0].title}</h3>
          <p className="mt-2 text-caption text-graphite">{trio[0].body}</p>
        </Reveal>

        <Reveal delay={0.12} className="text-center">
          <Glyph>
            {/* Four readings and a baseline. The bars are the scene; the line
                under them is what we do with it, so it takes the accent. */}
            <g className="stroke-ink" strokeWidth="1.2" opacity="0.75">
              <line x1="24" y1="46" x2="24" y2="28" />
              <line x1="38" y1="46" x2="38" y2="14" />
              <line x1="52" y1="46" x2="52" y2="34" />
              <line x1="66" y1="46" x2="66" y2="22" />
            </g>
            <line
              x1="18"
              y1="52"
              x2="72"
              y2="52"
              className="stroke-offset"
              strokeWidth="1.2"
            />
          </Glyph>
          <h3 className="font-display text-title">{trio[1].title}</h3>
          <p className="mt-2 text-caption text-graphite">{trio[1].body}</p>
        </Reveal>

        <Reveal delay={0.24} className="text-center">
          <Glyph>
            <g transform="translate(34,37)">
              <circle className="ripple stroke-ink opacity-20" />
              <circle r="2.5" className="fill-ink" />
            </g>
            <g transform="translate(58,37)">
              <circle
                className="ripple stroke-offset"
                style={{ animationDelay: "1.4s" }}
              />
              <circle r="2.5" className="fill-offset" />
            </g>
          </Glyph>
          <h3 className="font-display text-title">{trio[2].title}</h3>
          <p className="mt-2 text-caption text-graphite">{trio[2].body}</p>
        </Reveal>
      </div>
    </section>
  );
}
