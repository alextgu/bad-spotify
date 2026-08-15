import Reveal from "@/components/Reveal";
import { statement } from "@/lib/site";

/**
 * 2 — the statement.
 *
 * One sentence, centred, with a great deal of nothing around it. This is the
 * only centred text on the page: it earns it by being a single object with no
 * second column to align to, and centring anything further down would read as
 * a page that hasn't decided where its left edge is.
 *
 * The whole section is one screen of rest between the hero and the argument.
 * If a second sentence ever appears here, this section has failed.
 */
export default function SectionStatement() {
  return (
    <section className="px-gutter py-section-sm md:py-section">
      <Reveal>
        <h2 className="mx-auto max-w-statement text-center font-display text-headline">
          {statement}
        </h2>
      </Reveal>
    </section>
  );
}
