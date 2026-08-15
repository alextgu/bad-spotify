import Label from "@/components/Label";
import { brand } from "@/lib/brand";
import { faq, footer } from "@/lib/site";

/**
 * 9 — the awkward questions.
 *
 * Native `<details>`, not a JavaScript accordion. It works with no JS, it is
 * keyboard accessible for free, search engines read the answers while
 * collapsed, and it cannot get stuck half-open on a resize.
 *
 * The mockup animated the height with GSAP and refreshed ScrollTrigger on
 * every toggle — which, under a pinned section further up the page, is a
 * full layout recalculation for the sake of a 500ms slide. The `+` still
 * rotates; that is enough acknowledgement.
 *
 * Second question down is the one that gives the whole thing away. It is left
 * exactly as plain as the others.
 */
export default function SectionFAQ() {
  return (
    <section
      id="faq"
      className="mx-auto max-w-content px-gutter py-section-sm md:py-section"
    >
      <Label className="block">The awkward questions</Label>

      <div className="mt-rest">
        {faq.map((item) => (
          <details
            key={item.q}
            className="group border-t border-hairline last:border-b"
          >
            <summary className="flex cursor-pointer list-none items-baseline gap-gutter py-block font-serif text-title marker:hidden">
              {item.q}
              <span
                aria-hidden
                className="ml-auto font-mono text-lg text-offset transition-transform duration-interaction ease-calm group-open:rotate-45"
              >
                +
              </span>
            </summary>
            <p className="max-w-measure pb-block text-body text-graphite">
              {item.a}
            </p>
          </details>
        ))}
      </div>

      <footer className="flex flex-wrap justify-between gap-4 pt-section-sm">
        <Label>{brand.name}</Label>
        <Label>{footer.right}</Label>
      </footer>
    </section>
  );
}
