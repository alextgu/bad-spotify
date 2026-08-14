import { learned } from "@/lib/content";

/**
 * Section 6 — what we learned.
 *
 * The Devpost field, answered honestly. Every entry is something we got wrong
 * first and had to change, not a lesson we'd have written down in advance.
 *
 * Kept adjacent to the challenges section on purpose: that one is decisions we
 * would defend, this one is decisions we reversed. A page that only contains
 * the first reads as marketing.
 */
export default function SectionLearned() {
  return (
    <section id="learned" className="section-page section-tall mx-auto max-w-5xl px-6 py-32">
      <h2 className="text-[clamp(1.75rem,4vw,3rem)] font-semibold tracking-[-0.035em]">
        What we got wrong first.
      </h2>
      <p className="mt-4 max-w-2xl text-ink-muted">
        Four things we believed at the start and had to give up on.
      </p>

      <div className="mt-16 space-y-14">
        {learned.map((l, i) => (
          <article
            key={l.heading}
            className="grid gap-4 border-t border-line pt-6 md:grid-cols-[auto_1fr] md:gap-10"
          >
            <p className="font-mono text-xs text-ink-muted md:pt-1.5">
              {String(i + 1).padStart(2, "0")}
            </p>
            <div>
              <h3 className="text-xl font-medium tracking-[-0.02em]">{l.heading}</h3>
              <p className="mt-3 max-w-3xl leading-relaxed text-ink-secondary">
                {l.body}
              </p>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}
