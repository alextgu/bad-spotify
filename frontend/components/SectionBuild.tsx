import SectionHeading from "@/components/SectionHeading";
import { stack } from "@/lib/content";
import { steps } from "@/lib/brand";

/**
 * Section 3 — how we built it.
 *
 * Covers the Devpost "How we built it" field without ever saying so. The
 * six-step loop first, because it's the thing that's actually ours, then the
 * parts list — in that order deliberately. Leading with a logo wall says "we
 * wired together four APIs"; leading with the loop says "we designed a system
 * and used four APIs to run it."
 */
export default function SectionBuild() {
  return (
    <section id="build" className="section-page section-tall mx-auto max-w-content px-6 py-section-sm md:py-section">
      <div className="grid gap-heading-sub md:grid-cols-2 md:gap-20">
        <SectionHeading
          index={3}
          label="THE LOOP"
          lead="How a moment"
          trail="gets ruined."
        />
        <p className="max-w-measure text-body text-ink-muted md:self-end">
          Six steps, about every five seconds, for as long as you leave it on.
        </p>
      </div>

      <ol className="mt-sub-content grid gap-x-12 gap-y-12 sm:grid-cols-2 lg:grid-cols-3">
        {steps.map((s) => (
          <li key={s.n} className="border-t border-subtle pt-5">
            <p className="font-mono text-xs text-ink-muted">{s.n}</p>
            <h3 className="mt-3 text-xl font-medium">{s.title}</h3>
            <p className="mt-2 text-body text-ink-secondary">{s.body}</p>
          </li>
        ))}
      </ol>

      <div className="mt-sub-content border-t border-subtle pt-10">
        <h3 className="text-sm uppercase tracking-eyebrow text-ink-muted">
          What it runs on
        </h3>
        <dl className="mt-8 grid gap-x-12 gap-y-8 md:grid-cols-2">
          {stack.map((s) => (
            <div key={s.name}>
              <dt className="font-medium">{s.name}</dt>
              <dd className="mt-1.5 leading-relaxed text-ink-muted">{s.role}</dd>
            </div>
          ))}
        </dl>
      </div>
    </section>
  );
}
