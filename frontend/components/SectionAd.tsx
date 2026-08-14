/**
 * Section 1 — the advertisement.
 *
 * A full-bleed product advertisement, played completely straight. The gap
 * between how seriously the ad takes itself and what it is actually
 * advertising is the entire joke, so this must never wink. No comic type, no
 * emoji, no "lol".
 *
 * **This is the only centred section on the page.** A hero earns centring
 * because there is one object and one sentence; everything below it is
 * argument, and centred argument is the most common tell of an amateur page.
 * If you are tempted to centre something further down, don't.
 *
 * Slots:
 *
 *   [hero image]  the product shot. One object, nothing else in frame.
 *   [headline]    six words at most, `display`.
 *   [subhead]     one sentence, `subheading`, never wider than 45ch.
 *   [actions]     one primary, one secondary. Never three.
 *   [fine print]  the legal-looking line that reads as a real ad, and is the
 *                 one place the joke is allowed to be.
 *
 * The accent appears exactly once here — the rule on the palette in the
 * headline. Drop the real photograph at `/public/ad/hero.jpg` and swap the
 * placeholder block for an <Image>.
 */
import BlurFade from "@/components/BlurFade";
import { brand } from "@/lib/brand";

export default function SectionAd() {
  return (
    <section
      id="ad"
      className="section-page relative flex flex-col items-center justify-center
                 px-6 py-section-sm text-center md:py-section"
    >
      <div className="w-full max-w-content">
        {/* [hero image] — placeholder. Replace with the product photograph. */}
        <BlurFade>
          <div
            className="mx-auto flex h-hero-slot w-full items-center justify-center
                       rounded-2xl border border-dashed border-subtle bg-surface-1"
            aria-hidden
          >
            <p className="font-mono text-caption uppercase tracking-eyebrow text-ink-muted">
              hero image — the product shot goes here
            </p>
          </div>
        </BlurFade>

        {/* [headline] — the one accent on this screen */}
        <BlurFade delay={0.08}>
          <h1 className="mx-auto mt-sub-content max-w-measure text-display">
            {brand.tagline}
          </h1>
        </BlurFade>

        {/* [subhead] */}
        <BlurFade delay={0.16}>
          <p className="mx-auto mt-heading-sub max-w-measure-sub text-subheading text-ink-secondary">
            {brand.description}
          </p>
        </BlurFade>

        {/* [actions] */}
        <BlurFade delay={0.24}>
          <div className="mt-sub-content flex flex-wrap items-center justify-center gap-3">
            <a
              href="#film"
              className="inline-flex items-center gap-2 rounded-full bg-ink-primary px-8 py-3.5
                         text-caption font-medium text-plane transition
                         duration-interaction ease-brand hover:opacity-90"
            >
              Watch it work
              <span aria-hidden>→</span>
            </a>
            <a
              href="#try"
              className="inline-flex items-center gap-2 rounded-full border border-subtle
                         px-8 py-3.5 text-caption transition duration-interaction
                         ease-brand hover:border-strong"
            >
              Try it yourself
            </a>
          </div>
        </BlurFade>

        {/* [fine print] */}
        <BlurFade delay={0.32}>
          <p className="mx-auto mt-sub-content max-w-measure-sub text-caption text-ink-muted">
            {brand.name} does not take requests, accept feedback, or improve
            with use. Song selection is{" "}
            <span className="text-target">final</span>. Not available in any
            store.
          </p>
        </BlurFade>
      </div>
    </section>
  );
}
