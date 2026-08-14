"use client";

import SectionHeading from "@/components/SectionHeading";
import { useEffect, useRef, useState } from "react";
import BlurFade from "@/components/BlurFade";
import { depth } from "@/lib/content";

/**
 * Section 5 — why any of this was hard.
 *
 * The argument: a useless product built properly is still built properly.
 * Every entry is a decision we would defend out loud, and each names the
 * failure it was chosen to prevent.
 *
 * **Sticky scroll.** This was five stacked paragraphs — a wall, and the place
 * a reader leaves. Now the index pins to the left and the entries move past
 * it, so the section reads as one argument with five parts rather than five
 * things in a row. The pinned column also gives the eye somewhere to rest,
 * which is most of what makes a long section feel deliberate instead of long.
 *
 * The active entry comes from IntersectionObserver rather than scroll maths:
 * it doesn't fire on every frame, and it degrades to "nothing highlighted"
 * rather than to "wrong thing highlighted".
 *
 * On mobile the pinned column is hidden entirely — sticky anything in a 375px
 * column is just lost width.
 */
export default function SectionDepth() {
  const [active, setActive] = useState(0);
  const refs = useRef<(HTMLElement | null)[]>([]);

  useEffect(() => {
    if (typeof IntersectionObserver === "undefined") return;

    const observer = new IntersectionObserver(
      (entries) => {
        const visible = entries
          .filter((e) => e.isIntersecting)
          .sort((a, b) => a.boundingClientRect.top - b.boundingClientRect.top)[0];
        if (!visible) return;
        const i = refs.current.indexOf(visible.target as HTMLElement);
        if (i >= 0) setActive(i);
      },
      // The band is the middle of the viewport: an entry is "current" when
      // it's what you're actually reading, not when it first appears.
      { rootMargin: "-45% 0px -45% 0px" },
    );

    refs.current.forEach((el) => el && observer.observe(el));
    return () => observer.disconnect();
  }, []);

  return (
    <section
      id="how"
      className="section-page mx-auto max-w-content px-6 py-section-sm md:py-section"
    >
      <BlurFade>
        <SectionHeading
          index={5}
          label="THE DECISIONS"
          lead="A useless product,"
          trail="built properly."
        />
      </BlurFade>
      <BlurFade delay={0.08}>
        <p className="mt-heading-sub max-w-measure-sub text-body text-ink-muted">
          The joke is the specification, not the excuse. Five decisions worth
          defending, each of them a failure we designed out.
        </p>
      </BlurFade>

      <div className="mt-sub-content grid gap-10 md:grid-cols-[14rem_1fr] md:gap-20">
        {/* The pinned index. Hidden on mobile — see the note above. */}
        <div className="hidden md:block">
          <div className="sticky top-1/3">
            <ol className="space-y-3">
              {depth.map((d, i) => (
                <li key={d.heading}>
                  <button
                    type="button"
                    onClick={() =>
                      refs.current[i]?.scrollIntoView({
                        behavior: "smooth",
                        block: "center",
                      })
                    }
                    className={`flex w-full items-baseline gap-3 text-left text-caption
                                transition-colors duration-colour ease-brand ${
                                  i === active
                                    ? "text-ink-primary"
                                    : "text-ink-muted hover:text-ink-secondary"
                                }`}
                  >
                    <span className="font-mono">
                      {String(i + 1).padStart(2, "0")}
                    </span>
                    <span>{d.heading}</span>
                  </button>
                </li>
              ))}
            </ol>
          </div>
        </div>

        {/* The entries themselves. */}
        <div className="space-y-24 md:space-y-40">
          {depth.map((d, i) => (
            <article
              key={d.heading}
              ref={(el) => {
                refs.current[i] = el;
              }}
              className="border-t border-subtle pt-6"
            >
              <p className="font-mono text-caption text-ink-muted">
                {String(i + 1).padStart(2, "0")}
              </p>
              <h3 className="mt-heading-sub text-subheading">{d.heading}</h3>
              <p className="mt-heading-sub max-w-measure text-body text-ink-secondary">
                {d.body}
              </p>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}
