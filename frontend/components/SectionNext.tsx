import { roadmap, theAsk } from "@/lib/content";

/**
 * Section 6 — what's next, and the close.
 *
 * The close is the honest one: we designed for hardware we could not get, so
 * we built the whole agent hardware-agnostic and fed it a recording instead.
 * Stated plainly, without whining — the point is that the port is small
 * because the seam was drawn correctly on day one.
 */
export default function SectionNext() {
  return (
    <section id="next" className="mx-auto max-w-5xl px-6 py-32">
      <h2 className="text-[clamp(1.75rem,4vw,3rem)] font-semibold tracking-[-0.035em]">
        What’s next.
      </h2>

      <div className="mt-14 space-y-10">
        {roadmap.map((r) => (
          <article key={r.title} className="border-t border-white/10 pt-6">
            <div className="flex flex-wrap items-baseline gap-3">
              <h3 className="text-xl font-medium tracking-[-0.02em]">{r.title}</h3>
              <span className="rounded border border-white/15 px-2 py-0.5 font-mono text-[11px] text-ink-muted">
                {r.state}
              </span>
            </div>
            <p className="mt-3 max-w-3xl leading-relaxed text-ink-secondary">{r.body}</p>
          </article>
        ))}
      </div>

      {/* ---------------------------------------------------- the close -- */}
      <div className="mt-24 border-t border-white/10 pt-16">
        <h3 className="text-[clamp(1.5rem,3.5vw,2.5rem)] font-semibold tracking-[-0.035em]">
          {theAsk.heading}
        </h3>
        <p className="mt-5 max-w-3xl leading-relaxed text-ink-secondary">{theAsk.body}</p>
        <p className="mt-8 text-[clamp(1.25rem,2.6vw,1.75rem)] leading-snug tracking-[-0.02em] text-target">
          {theAsk.kicker}
        </p>
      </div>
    </section>
  );
}
