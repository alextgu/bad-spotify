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
    <section id="build" className="section-page mx-auto max-w-5xl px-6 py-32">
      <h2 className="text-[clamp(1.75rem,4vw,3rem)] font-semibold tracking-[-0.035em]">
        How a moment gets ruined.
      </h2>
      <p className="mt-4 max-w-2xl text-ink-muted">
        Six steps, about every five seconds, for as long as you leave it on.
      </p>

      <ol className="mt-16 grid gap-x-12 gap-y-12 sm:grid-cols-2 lg:grid-cols-3">
        {steps.map((s) => (
          <li key={s.n} className="border-t border-line pt-5">
            <p className="font-mono text-xs text-ink-muted">{s.n}</p>
            <h3 className="mt-3 text-xl font-medium tracking-[-0.02em]">{s.title}</h3>
            <p className="mt-2 leading-relaxed text-ink-secondary">{s.body}</p>
          </li>
        ))}
      </ol>

      <div className="mt-24 border-t border-line pt-10">
        <h3 className="text-sm uppercase tracking-[0.16em] text-ink-muted">
          What it runs on
        </h3>
        <dl className="mt-8 grid gap-x-12 gap-y-8 md:grid-cols-2">
          {stack.map((s) => (
            <div key={s.name}>
              <dt className="font-medium tracking-[-0.01em]">{s.name}</dt>
              <dd className="mt-1.5 leading-relaxed text-ink-muted">{s.role}</dd>
            </div>
          ))}
        </dl>
      </div>
    </section>
  );
}
