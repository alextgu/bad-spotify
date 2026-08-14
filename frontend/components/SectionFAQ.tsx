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
    <section id="faq" className="section-page mx-auto flex max-w-3xl flex-col justify-center px-6 py-32">
      <h2 className="text-[clamp(1.75rem,4vw,3rem)] font-semibold tracking-[-0.035em]">
        Questions.
      </h2>
      <p className="mt-4 max-w-xl text-ink-muted">
        The part of the page that isn’t a joke.
      </p>

      <div className="mt-14">
        {faq.map((item) => (
          <details
            key={item.q}
            className="group border-t border-line py-5 last:border-b"
          >
            <summary
              className="flex cursor-pointer list-none items-start justify-between gap-6
                         text-lg font-medium tracking-[-0.02em] marker:hidden"
            >
              {item.q}
              <span
                aria-hidden
                className="mt-1 shrink-0 text-ink-muted transition-transform
                           group-open:rotate-45"
              >
                +
              </span>
            </summary>
            <p className="mt-4 max-w-2xl leading-relaxed text-ink-secondary">
              {item.a}
            </p>
          </details>
        ))}
      </div>
    </section>
  );
}
