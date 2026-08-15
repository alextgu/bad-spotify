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

          <div className="my-auto max-w-[44rem] pb-[1vh]">
            <h1 className="font-display text-[clamp(3.05rem,5vw,4.65rem)] font-semibold leading-[0.96] tracking-[-0.045em]">
              <span className="block">{hero.headline}</span>
              <span className="mt-1 block">
                {hero.headlineRest}{" "}
                <span className="text-brand-pink">{hero.headlineAccent}</span>,
              </span>
              <span className="mt-3 block text-[0.58em] leading-[1.08] tracking-[-0.025em] text-paper/90 sm:mt-4">
                {hero.headlineTail}.
              </span>
            </h1>

            <p className="mt-5 max-w-[32rem] text-[clamp(1rem,1.4vw,1.15rem)] leading-relaxed text-paper/70 sm:mt-6">
              {hero.sub}
            </p>
          </div>

          {/* The cinematic "coming soon" card is gone. It was inert -- a card
              shaped like a control with nothing behind it -- and the same
              reasoning that kept its play triangle off applies to the card
              itself: a thing that looks pressable and is not costs more trust
              than the placeholder was worth. `hero.clip` still holds its
              filename and shoot direction for when the cut exists.

              The now-playing bar moved onto the photograph, so the foot of the
              hero is now just the credit. */}
          <footer className="flex items-end justify-end">
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
