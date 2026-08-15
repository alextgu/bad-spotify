"use client";

import { useState } from "react";

import Label from "@/components/Label";
import Screen from "@/components/Screen";
import { brand } from "@/lib/brand";
import { faq, footer } from "@/lib/site";

/**
 * 7 — the awkward questions, and the end of the page.
 *
 * One controlled accordion keeps at most one answer open. The button and
 * region attributes preserve disclosure semantics while a grid-row transition
 * reveals each answer at its natural height.
 *
 * Seven collapsed questions fit one screen with the footer under them. Keeping
 * at most one answer open also bounds the extra height inside that fixed screen.
 *
 * Second question down is the one that gives the whole thing away. It is left
 * exactly as plain as the others.
 */
export default function SectionFAQ() {
  const [openIndex, setOpenIndex] = useState<number | null>(null);

  return (
    <Screen id="faq">
      <div className="mx-auto w-full max-w-content">
        <Label className="block">The awkward questions</Label>

        <div className="mt-rest">
          {faq.map((item, index) => {
            const isOpen = openIndex === index;
            const buttonId = "faq-question-" + index;
            const answerId = "faq-answer-" + index;

            return (
              <div
                key={item.q}
                className="border-t border-hairline last:border-b"
              >
                <button
                  id={buttonId}
                  type="button"
                  aria-expanded={isOpen}
                  aria-controls={answerId}
                  onClick={() => setOpenIndex(isOpen ? null : index)}
                  className="flex w-full cursor-pointer items-baseline gap-gutter py-5 text-left font-display text-title"
                >
                  <span>{item.q}</span>
                  <span
                    aria-hidden
                    className={[
                      "ml-auto font-mono text-lg text-offset-ink transition-transform",
                      "duration-interaction ease-calm motion-reduce:transition-none",
                      isOpen ? "rotate-45" : "rotate-0",
                    ].join(" ")}
                  >
                    +
                  </span>
                </button>

                <div
                  id={answerId}
                  role="region"
                  aria-labelledby={buttonId}
                  aria-hidden={!isOpen}
                  className={[
                    "grid transition-[grid-template-rows,opacity]",
                    "duration-interaction ease-calm motion-reduce:transition-none",
                    isOpen
                      ? "grid-rows-[1fr] opacity-100"
                      : "grid-rows-[0fr] opacity-0",
                  ].join(" ")}
                >
                  <div className="overflow-hidden">
                    <p
                      className={[
                        "max-w-measure pb-5 text-body text-graphite",
                        "transition-transform duration-interaction ease-calm",
                        "motion-reduce:transition-none",
                        isOpen ? "translate-y-0" : "-translate-y-1",
                      ].join(" ")}
                    >
                      {item.a}
                    </p>
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        <footer className="mt-rest flex flex-wrap items-baseline justify-between gap-4">
          <span className="font-display text-[1.0625rem] font-semibold tracking-[-0.03em]">
            {brand.name}
          </span>
          <Label>{footer.right}</Label>
        </footer>
      </div>
    </Screen>
  );
}
