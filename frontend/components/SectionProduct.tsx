import PipelineDiagram from "@/components/PipelineDiagram";
import ProductRotator from "@/components/ProductRotator";
import { capabilities, stack } from "@/lib/content";

/**
 * Section 2 — what it is, what it does, what it's built on.
 *
 * The object rotates because the product is a wearable and a still picture of
 * glasses reads as a stock photo. Everything else on this screen is text: the
 * five things it does, the diagram of the loop, and the stack with a reason
 * next to each part rather than a row of logos.
 *
 * Layout is a scaffold. The visual pass comes later.
 */
export default function SectionProduct() {
  return (
    <section id="product" className="section-page mx-auto max-w-6xl px-6 py-32">
      <div className="grid items-center gap-12 lg:grid-cols-2">
        <ProductRotator />

        <div>
          <h2 className="text-[clamp(1.75rem,4vw,3rem)] font-semibold tracking-[-0.035em]">
            An agent with one feature.
          </h2>
          <p className="mt-5 text-ink-secondary">
            It rides on camera glasses, watches the moment you are in, works out
            exactly what that moment sounds like — and plays the opposite. It
            talks to you only to announce what it has done. It will not take
            requests, and it does not help with anything else.
          </p>
        </div>
      </div>

      {/* --------------------------------------------------- what it does -- */}
      <ol className="mt-24 grid gap-x-12 gap-y-10 sm:grid-cols-2 lg:grid-cols-3">
        {capabilities.map((c, i) => (
          <li key={c.title} className="border-t border-line pt-5">
            <p className="font-mono text-xs text-ink-muted">
              {String(i + 1).padStart(2, "0")}
            </p>
            <h3 className="mt-3 text-lg font-medium tracking-[-0.02em]">{c.title}</h3>
            <p className="mt-2 text-[15px] leading-relaxed text-ink-secondary">
              {c.body}
            </p>
          </li>
        ))}
      </ol>

      {/* ------------------------------------------------------- the loop -- */}
      <div className="mt-24">
        <h3 className="text-xl font-medium tracking-[-0.02em]">The loop</h3>
        <p className="mt-2 max-w-xl text-sm text-ink-muted">
          Six steps, about every five seconds, for as long as you leave it on.
        </p>
        <div className="mt-8 overflow-x-auto">
          <div className="min-w-[700px]">
            <PipelineDiagram />
          </div>
        </div>
      </div>

      {/* ---------------------------------------------------- the stack -- */}
      <div className="mt-24">
        <h3 className="text-xl font-medium tracking-[-0.02em]">Behind it</h3>
        <dl className="mt-8 grid gap-x-12 gap-y-8 sm:grid-cols-2 lg:grid-cols-3">
          {stack.map((s) => (
            <div key={s.name} className="border-t border-line pt-4">
              <dt className="font-medium">{s.name}</dt>
              <dd className="mt-1.5 text-sm leading-relaxed text-ink-muted">{s.role}</dd>
            </div>
          ))}
        </dl>
      </div>
    </section>
  );
}
