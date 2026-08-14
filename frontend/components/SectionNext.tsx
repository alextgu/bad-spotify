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
    <section id="next" className="section-page mx-auto max-w-content px-6 py-section-sm md:py-section">
      <h2 className="text-heading font-semibold">
        What’s next.
      </h2>

      <div className="mt-sub-content space-y-10">
        {roadmap.map((r) => (
          <article key={r.title} className="border-t border-subtle pt-6">
            <div className="flex flex-wrap items-baseline gap-3">
              <h3 className="text-xl font-medium">{r.title}</h3>
              <span className="rounded border border-strong px-2 py-0.5 font-mono text-caption text-ink-muted">
                {r.state}
              </span>
            </div>
            <p className="mt-3 max-w-measure text-body text-ink-secondary">{r.body}</p>
          </article>
        ))}
      </div>

      {/* ---------------------------------------------------- the close -- */}
      <div className="mt-sub-content border-t border-subtle pt-16">
        <h3 className="text-heading font-semibold">
          {theAsk.heading}
        </h3>
        <p className="mt-5 max-w-measure text-body text-ink-secondary">{theAsk.body}</p>
        <p className="mt-8 text-subheading leading-snug text-target">
          {theAsk.kicker}
        </p>
      </div>
    </section>
  );
}
