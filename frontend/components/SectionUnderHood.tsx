import Label from "@/components/Label";
import Reveal from "@/components/Reveal";
import Slot from "@/components/Slot";
import { metrics } from "@/lib/site";

/**
 * 6 — the dark break.
 *
 * The one section that leaves the paper. It exists as much for rhythm as for
 * content: nine screens of off-white needs somewhere for the eye to rest, and
 * the numbers are the right thing to put there because they are the only
 * place on the page where the claim is precise.
 *
 * The numbers are printed, not counted up. A number that animates from zero is
 * asking to be admired, and two of these are interesting *because they are
 * small* — "0 images stored" is a privacy claim, and it loses all of its
 * weight by arriving as a flourish. It should simply already be true.
 */
export default function SectionUnderHood() {
  return (
    <section className="relative overflow-hidden bg-ink py-section-sm text-paper md:py-section">
      <Slot
        shot={{
          file: "dark-street.jpg",
          note: [
            "full bleed · sits behind the numbers at low opacity",
            "night, wet pavement, no subject",
          ],
        }}
        className="absolute inset-0 scale-110 opacity-40"
      />

      <div className="relative mx-auto max-w-content px-gutter">
        <Label className="!text-paper/50">Under the hood</Label>

        <dl className="mt-section-sm grid gap-rest sm:grid-cols-2 lg:grid-cols-4">
          {metrics.map((m, i) => (
            <Reveal key={m.label} delay={i * 0.1}>
              <dd className="font-display text-display leading-none">
                {m.value}
                {m.unit && (
                  <span className="text-[0.34em] text-paper/55">{m.unit}</span>
                )}
              </dd>
              <dt className="mt-block">
                <Label className="!text-paper/50">{m.label}</Label>
              </dt>
            </Reveal>
          ))}
        </dl>
      </div>
    </section>
  );
}
