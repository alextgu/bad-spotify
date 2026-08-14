import SectionHeading from "@/components/SectionHeading";
import { faq } from "@/lib/content";

/**
 * Section 8 — the FAQ, and the only section that plays it completely straight.
 *
 * Everything above this is an advertisement for a deliberately useless
 * product. This is where someone who wants to know what it actually does gets
 * a literal answer: it reads *mood*, it inverts *mood*, and it has no notion of
 * anyone's identity. If a reader only sees this section, they should still come
 * away with the right idea.
 *
 * So: no jokes in here, no winking, no clever headings. Answers live in
 * `lib/content.ts`.
 *
 * Native <details> on purpose — it works with no JavaScript, it's keyboard
 * accessible for free, and search engines read the answers even when collapsed.
 */
export default function SectionFAQ() {
  return (
    <section id="faq" className="section-page mx-auto flex max-w-measure flex-col justify-center px-6 py-section-sm md:py-section">
      <SectionHeading
          index={8}
          label="QUESTIONS"
          lead="The part that"
          trail="isn’t a joke."
        />
      <p className="mt-heading-sub max-w-measure-sub text-ink-muted">
        The part of the page that isn’t a joke.
      </p>

      <div className="mt-sub-content">
        {faq.map((item) => (
          <details
            key={item.q}
            className="group border-t border-subtle py-5 last:border-b"
          >
            <summary
              className="flex cursor-pointer list-none items-start justify-between gap-6
                         text-lg font-medium marker:hidden"
            >
              <span className="flex flex-wrap items-baseline gap-3">
                {item.q}
                {item.pending && (
                  <span className="rounded border border-strong px-2 py-0.5
                                   font-mono text-caption font-normal text-ink-muted">
                    answer pending
                  </span>
                )}
              </span>
              <span
                aria-hidden
                className="mt-1 shrink-0 text-ink-muted transition-transform
                           group-open:rotate-45"
              >
                +
              </span>
            </summary>

            {item.pending ? (
              // Kept visibly unanswered on purpose. A confident placeholder
              // here would be worse than an honest gap — see FaqItem.pending.
              <p className="mt-heading-sub max-w-measure leading-relaxed text-ink-muted">
                We don’t have a good answer to this yet, and we’d rather say so
                than invent one. It’s a real question — the system already
                reads colour out of a scene and maps it toward sound, so what
                that means for someone who does the same thing involuntarily is
                worth thinking about properly.
              </p>
            ) : (
              <p className="mt-heading-sub max-w-measure text-body text-ink-secondary">
                {item.a}
              </p>
            )}
          </details>
        ))}
      </div>
    </section>
  );
}
