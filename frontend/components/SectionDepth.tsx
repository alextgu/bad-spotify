import { depth } from "@/lib/content";

/**
 * Section 5 — why any of this was hard.
 *
 * The argument, in order: a useless product built properly is still built
 * properly. Everything here is a decision we would defend out loud, and each
 * one has a failure it was chosen to prevent.
 *
 * Deliberately text-heavy. This is the section for the person who has already
 * laughed and now wants to know whether we can actually build.
 */
export default function SectionDepth() {
  return (
    <section id="how" className="mx-auto max-w-5xl px-6 py-32">
      <h2 className="text-[clamp(1.75rem,4vw,3rem)] font-semibold tracking-[-0.035em]">
        A useless product, built properly.
      </h2>
      <p className="mt-4 max-w-2xl text-ink-muted">
        The joke is the specification, not the excuse. Five decisions worth
        defending, each of them a failure we designed out.
      </p>

      <div className="mt-16 space-y-14">
        {depth.map((d, i) => (
          <article key={d.heading} className="grid gap-4 border-t border-white/10 pt-6 md:grid-cols-[auto_1fr] md:gap-10">
            <p className="font-mono text-xs text-ink-muted md:pt-1.5">
              {String(i + 1).padStart(2, "0")}
            </p>
            <div>
              <h3 className="text-xl font-medium tracking-[-0.02em]">{d.heading}</h3>
              <p className="mt-3 max-w-3xl leading-relaxed text-ink-secondary">
                {d.body}
              </p>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}
