import Label from "@/components/Label";
import Reveal from "@/components/Reveal";
import { broke } from "@/lib/site";

/**
 * 7 — what broke.
 *
 * Three things, struck through, with no explanation offered. The restraint is
 * the point: a page that lists its failures and then defends each one has not
 * actually admitted anything. Struck out and left alone, they read as facts
 * someone was comfortable printing.
 *
 * The strike is the accent colour — the only place it does something
 * structural rather than decorative.
 */
export default function SectionBroke() {
  return (
    <section className="mx-auto max-w-content px-gutter py-section-sm md:py-section">
      <Reveal>
        <h2 className="max-w-[13ch] font-display text-headline">{broke.title}</h2>
      </Reveal>

      <ul className="mt-rest">
        {broke.items.map((item, i) => (
          <Reveal
            as="li"
            key={item}
            delay={i * 0.1}
            className="flex items-baseline gap-rest border-t border-hairline py-block"
          >
            <Label tone="offset" className="w-8 shrink-0">
              {String(i + 1).padStart(2, "0")}
            </Label>
            <span className="font-display text-title text-graphite line-through decoration-offset decoration-2">
              {item}
            </span>
          </Reveal>
        ))}
      </ul>
    </section>
  );
}
