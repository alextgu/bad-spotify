import SectionHeading from "@/components/SectionHeading";
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
    <section id="learned" className="section-page section-tall mx-auto max-w-content px-6 py-section-sm md:py-section">
      {/* Headline left, body right. The heading gets the width it needs and
          the explanation sits beside it rather than under it, which stops the
          section opening with two stacked blocks of text. */}
      <div className="grid gap-heading-sub md:grid-cols-2 md:gap-20">
        <SectionHeading
          index={6}
          label="WHAT WE GOT WRONG"
          lead="What we got"
          trail="wrong first."
        />
        <p className="max-w-measure text-body text-ink-muted md:self-end">
          Four things we believed at the start and had to give up on.
        </p>
      </div>

      <div className="mt-sub-content space-y-14">
        {learned.map((l, i) => (
          <article
            key={l.heading}
            className="grid gap-4 border-t border-subtle pt-6 md:grid-cols-[auto_1fr] md:gap-10"
          >
            <p className="font-mono text-xs text-ink-muted md:pt-1.5">
              {String(i + 1).padStart(2, "0")}
            </p>
            <div>
              <h3 className="text-xl font-medium">{l.heading}</h3>
              <p className="mt-3 max-w-measure text-body text-ink-secondary">
                {l.body}
              </p>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}
