import Reveal from "@/components/Reveal";
import Screen from "@/components/Screen";
import { description } from "@/lib/site";

/**
 * 2 — what it is.
 *
 * The statement and the three moves used to be two separate screens. They are
 * one now, and they are better for it: the sentence poses the problem and the
 * three answer it, so splitting them put a scroll between a question and its
 * answer for no reason other than that there was room.
 *
 * The three glyphs are built from two marks — a dot, and a ring leaving it.
 * The third is the argument of the whole product in one picture: two sources,
 * one of them the accent colour.
 */

function Glyph({ children }: { children: React.ReactNode }) {
  return (
    <div className="mb-block grid h-[58px] place-items-center">
      <svg viewBox="0 0 90 58" className="h-[58px] overflow-visible" aria-hidden>
        {children}
      </svg>
    </div>
  );
}

export default function SectionDescription() {
  return (
    <Screen id="what">
      <div className="mx-auto w-full max-w-content">
        <Reveal>
          <h2 className="mx-auto max-w-statement text-center font-display text-headline">
            {description.statement}
          </h2>
        </Reveal>

        <div className="mt-section-sm grid gap-rest md:grid-cols-3">
          <Reveal delay={0.1} className="text-center">
            <Glyph>
              <g transform="translate(45,29)">
                <circle className="ripple stroke-ink opacity-25" />
                <circle
                  className="ripple stroke-ink opacity-25"
                  style={{ animationDelay: "3.6s" }}
                />
                <circle r="2.5" className="fill-ink" />
              </g>
            </Glyph>
            <h3 className="font-display text-title">{description.points[0].title}</h3>
            <p className="mt-2 text-caption text-graphite">
              {description.points[0].body}
            </p>
          </Reveal>

          <Reveal delay={0.2} className="text-center">
            <Glyph>
              {/* Four readings and a baseline. The bars are the scene; the
                  line under them is what we do with it, so it takes the
                  accent. */}
              <g className="stroke-ink" strokeWidth="1.2" opacity="0.75">
                <line x1="24" y1="38" x2="24" y2="22" />
                <line x1="38" y1="38" x2="38" y2="10" />
                <line x1="52" y1="38" x2="52" y2="27" />
                <line x1="66" y1="38" x2="66" y2="16" />
              </g>
              <line
                x1="18"
                y1="44"
                x2="72"
                y2="44"
                className="stroke-offset"
                strokeWidth="1.2"
              />
            </Glyph>
            <h3 className="font-display text-title">{description.points[1].title}</h3>
            <p className="mt-2 text-caption text-graphite">
              {description.points[1].body}
            </p>
          </Reveal>

          <Reveal delay={0.3} className="text-center">
            <Glyph>
              <g transform="translate(34,29)">
                <circle className="ripple stroke-ink opacity-20" />
                <circle r="2.5" className="fill-ink" />
              </g>
              <g transform="translate(58,29)">
                <circle
                  className="ripple stroke-offset"
                  style={{ animationDelay: "1.4s" }}
                />
                <circle r="2.5" className="fill-offset" />
              </g>
            </Glyph>
            <h3 className="font-display text-title">{description.points[2].title}</h3>
            <p className="mt-2 text-caption text-graphite">
              {description.points[2].body}
            </p>
          </Reveal>
        </div>
      </div>
    </Screen>
  );
}
