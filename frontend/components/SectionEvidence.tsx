import Label from "@/components/Label";
import Reveal from "@/components/Reveal";
import Slot from "@/components/Slot";
import { evidence } from "@/lib/site";

/**
 * 4 — the evidence. The mockup's sections 4 and 5, now one section.
 *
 * They were a full-bleed film and then, separately, a three-up grid of
 * moments. Grouped, they read as one argument: here is the thing running,
 * and here are three moments it ran in. Apart, the grid arrived with no
 * stated relationship to the film above it and had to re-introduce itself.
 *
 * The film bleeds edge to edge; the moments sit inside the content column.
 * That change of width is what separates them without needing a heading
 * between — the grouping is done by the layout rather than announced.
 */
export default function SectionEvidence() {
  return (
    <section id="evidence">
      {/* -------------------------------------------------------- the film -- */}
      <div className="relative aspect-[4/3] overflow-hidden md:aspect-[21/9]">
        <Slot
          shot={evidence.film}
          className="absolute inset-0 scale-110"
          /* scaled so the parallax drift never exposes an edge */
        />
      </div>

      <div className="mx-auto flex max-w-content flex-wrap justify-between gap-3 px-gutter pt-rest">
        <Label tone="offset">{evidence.filmCaption.left}</Label>
        <Label>{evidence.filmCaption.right}</Label>
      </div>

      {/* ----------------------------------------------------- the moments -- */}
      <div className="mx-auto max-w-content px-gutter pt-section-sm md:pt-section">
        <div className="grid gap-rest md:grid-cols-3 md:gap-gutter">
          {evidence.moments.map((m, i) => (
            <Reveal as="article" key={m.title} delay={i * 0.12}>
              <Slot
                shot={m.shot}
                className="aspect-[4/5] rounded-card"
              />
              {/* Close to its image on purpose. A caption is part of the
                  picture; pushed 72px away it becomes a separate object and
                  the eye stops pairing them. Air belongs *between* the
                  moments, not between a moment and its own label. */}
              <div className="pt-gutter">
                <Label tone="offset" className="block">
                  {m.time}
                </Label>
                <p className="mt-2 font-serif text-title">{m.title}</p>
              </div>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
}
