import Label from "@/components/Label";
import Screen from "@/components/Screen";
import { brand } from "@/lib/brand";
import { faq, footer } from "@/lib/site";

/**
 * 7 — the awkward questions, and the end of the page.
 *
 * Native `<details>`, not a JavaScript accordion. It works with no JS, it is
 * keyboard accessible for free, search engines read the answers while
 * collapsed, and it cannot get stuck half-open on a resize.
 *
 * Seven questions collapsed fit one screen with the footer under them. Opening
 * one pushes the rest down inside a fixed-height screen, so the last answer
 * can clip — which is the correct trade here: closed is the state the screen
 * is designed for, and anyone opening the fifth question can close the others.
 *
 * Second question down is the one that gives the whole thing away. It is left
 * exactly as plain as the others.
 */
export default function SectionFAQ() {
  return (
    <Screen id="faq">
      <div className="mx-auto w-full max-w-content">
        <Label className="block">The awkward questions</Label>

        <div className="mt-rest">
          {faq.map((item) => (
            <details
              key={item.q}
              className="group border-t border-hairline last:border-b"
            >
              <summary className="flex cursor-pointer list-none items-baseline gap-gutter py-5 font-display text-title marker:hidden">
                {item.q}
                <span
                  aria-hidden
                  className="ml-auto font-mono text-lg text-offset-ink transition-transform duration-interaction ease-calm group-open:rotate-45"
                >
                  +
                </span>
              </summary>
              <p className="max-w-measure pb-5 text-body text-graphite">{item.a}</p>
            </details>
          ))}
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
