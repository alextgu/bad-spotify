import Label from "@/components/Label";
import HeroCollage from "@/components/HeroCollage";
import LogoMark from "@/components/LogoMark";
import Slot from "@/components/Slot";
import { brand } from "@/lib/brand";
import { hero } from "@/lib/site";

/**
 * 1 — the hero.
 *
 * One frame and one hierarchy. The brand occupies a compact header, the
 * promise sits on a stable left edge through the middle, and the only thing at
 * the foot is the next action. Keeping all three on the same grid removes the
 * floating-card composition that previously made the type compete with itself.
 *
 * The hero media still fills the inset frame. While it is a placeholder its
 * internal shoot notes are hidden here: they remain in lib/site.ts as the
 * production brief, but they are not part of the customer-facing hierarchy.
 */
export default function SectionHero() {
  return (
    <section id="hero" className="h-svh p-3 sm:p-[15px]">
      <div className="relative h-full w-full overflow-hidden rounded-frame bg-[#111114]">
        <Slot shot={hero.shot} className="absolute inset-0 [&>span]:hidden" />

        {/* A single directional feather protects the copy while leaving the
            right side available for the eventual film. The vertical wash
            keeps the top and bottom controls readable without turning the
            whole frame into a flat black panel. */}
        <div
          aria-hidden
          className="pointer-events-none absolute inset-0
                     bg-[linear-gradient(90deg,rgba(5,5,7,.94)_0%,rgba(5,5,7,.84)_30%,rgba(5,5,7,.48)_55%,rgba(5,5,7,.1)_78%),linear-gradient(180deg,rgba(5,5,7,.42)_0%,transparent_28%,transparent_72%,rgba(5,5,7,.52)_100%)]"
        />

        <HeroCollage />

        <div className="pointer-events-none absolute inset-0 z-10 flex flex-col px-6 py-6 text-paper sm:px-10 sm:py-8 lg:px-14 lg:py-10">
          <header>
            <div className="flex items-center gap-3">
              <LogoMark size={48} />
              <span className="font-display text-[clamp(1.4rem,2vw,1.9rem)] font-semibold leading-none tracking-[-0.035em]">
                {brand.name}
              </span>
            </div>
          </header>

          <div className="my-auto max-w-[52rem] pb-[2vh]">
            <h1 className="font-display text-[clamp(3.15rem,5.25vw,4.8rem)] font-semibold leading-[0.96] tracking-[-0.045em]">
              <span className="block">{hero.headline}</span>
              <span className="mt-1 block">
                {hero.headlineRest}{" "}
                <span className="text-offset">{hero.headlineAccent}</span>.
              </span>
            </h1>

            <p className="mt-7 max-w-[34rem] text-[clamp(1rem,1.45vw,1.1875rem)] leading-relaxed text-paper/70">
              {hero.sub}
            </p>
          </div>

          <footer className="flex items-end justify-between gap-6">
            {/* The cinematic, bottom left. A card rather than a line of text,
                because it is a placeholder for a piece of film and should
                occupy roughly the space that film will.

                No play triangle, and the border is dimmed: there is nothing
                behind it yet. A play button with nothing to play is the same
                trap as the gated upload on the try-it screen — the click is
                the moment someone finds out, and it costs more than the
                affordance is worth. When the cut exists this goes back to
                rendering a `Slot` from `hero.clip`, which still carries its
                filename and direction. */}
            <div className="w-[min(272px,34vw)] overflow-hidden rounded-card border border-paper/20 bg-[rgba(8,8,10,.5)] backdrop-blur-[2px]">
              <div className="grid aspect-[16/10] place-items-center px-4 text-center">
                <span>
                  {/* Plain spans rather than `Label`: this file no longer
                      imports it, and a card in the hero is not worth adding a
                      dependency back for. */}
                  <span className="block font-mono text-label uppercase text-paper/80">
                    Cinematic demo
                  </span>
                  <p className="mt-2 font-mono text-[0.6875rem] uppercase tracking-[0.18em] text-paper/45">
                    Coming soon
                  </p>
                </span>
              </div>
            </div>

            <a
              href="https://devpost.com/software/spotify-cj"
              target="_blank"
              rel="noopener noreferrer"
              className="pointer-events-auto pb-1 font-mono text-label uppercase text-paper/60 transition-colors duration-interaction ease-calm hover:text-paper"
            >
              CUTC hackathon
            </a>
          </footer>
        </div>
      </div>
    </section>
  );
}
