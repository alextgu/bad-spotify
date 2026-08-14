/**
 * Section 1 — the advertisement.
 *
 * FRAMEWORK ONLY. Not designed yet.
 *
 * The brief: a full-bleed product advertisement, played completely straight —
 * high-tech, clean white, premium. The gap between how seriously the ad takes
 * itself and what it is actually advertising is the entire joke, so this must
 * never wink. No comic type, no emoji, no "lol".
 *
 * Slots this reserves, so the visual pass has somewhere to land:
 *
 *   [hero image]  the product shot. Full-bleed, edge to edge, one object.
 *   [headline]    six words at most.
 *   [subhead]     one sentence.
 *   [actions]     one primary, one secondary. Never three.
 *   [fine print]  the legal-looking line at the bottom that reads as a real
 *                 ad and is where the joke is allowed to be.
 *
 * Drop the real photograph at `/public/ad/hero.jpg` and swap the placeholder
 * block for an <Image>.
 */
import { brand } from "@/lib/brand";

export default function SectionAd() {
  return (
    <section
      id="ad"
      className="section-page relative flex flex-col items-center justify-center px-6 pt-20 text-center"
    >
      {/* [hero image] — placeholder. Replace with the product photograph. */}
      <div
        className="mb-14 flex h-[38vh] w-full max-w-4xl items-center justify-center
                   rounded-2xl border border-dashed border-line-strong bg-surface-1"
        aria-hidden
      >
        <p className="font-mono text-xs uppercase tracking-[0.2em] text-ink-muted">
          hero image — the product shot goes here
        </p>
      </div>

      {/* [headline] */}
      <h1 className="max-w-4xl text-[clamp(2.5rem,7vw,5.5rem)] font-semibold leading-[1.02] tracking-[-0.045em]">
        {brand.tagline}
      </h1>

      {/* [subhead] */}
      <p className="mt-6 max-w-xl text-[clamp(1.05rem,2vw,1.35rem)] leading-snug text-ink-secondary">
        {brand.description}
      </p>

      {/* [actions] */}
      <div className="mt-12 flex flex-wrap items-center justify-center gap-3">
        <a
          href="#logo"
          className="inline-flex items-center gap-2 rounded-full bg-ink-primary px-8 py-3.5
                     text-sm font-medium text-plane transition hover:opacity-90"
        >
          Meet it
          <span aria-hidden>→</span>
        </a>
        <a
          href="#try"
          className="inline-flex items-center gap-2 rounded-full border border-line-strong
                     px-8 py-3.5 text-sm transition hover:border-ink-muted"
        >
          Try it yourself
        </a>
      </div>

      {/* [fine print] */}
      <p className="mt-16 max-w-lg text-xs leading-relaxed text-ink-muted">
        {brand.name} does not take requests, accept feedback, or improve with
        use. Song selection is final. Not available in any store.
      </p>
    </section>
  );
}
