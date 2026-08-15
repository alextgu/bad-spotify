import Label from "@/components/Label";
import Reveal from "@/components/Reveal";
import Screen from "@/components/Screen";
import { results } from "@/lib/site";

/**
 * 6 — results, and the three things worth being pleased about.
 *
 * The one screen that leaves the paper, which is as much about rhythm as about
 * content: six screens of off-white needs somewhere for the eye to rest, and
 * numbers are the right thing to put there because this is the only place the
 * claims are precise.
 *
 * The numbers are printed, not counted up. A number that animates from zero is
 * asking to be admired, and two of these are interesting precisely because
 * they are small — "0 images stored" is a privacy claim and it loses all of
 * its weight arriving as a flourish. It should simply already be true.
 *
 * Three boasts, not five. Every one is checkable in the repo; if a fourth ever
 * gets added, one of these comes out, because a longer list is read as a
 * shorter one.
 */
export default function SectionResults() {
  return (
    <Screen id="results" className="bg-ink text-paper">
      <div className="mx-auto w-full max-w-content">
        <Reveal>
          <Label className="!text-paper/50">Results</Label>
          <h2 className="mt-block font-display text-headline">{results.title}</h2>
        </Reveal>

        <dl className="mt-section-sm grid gap-rest sm:grid-cols-2 lg:grid-cols-4">
          {results.metrics.map((m, i) => (
            <Reveal key={m.label} delay={0.08 * i}>
              <dd className="font-display text-display leading-none">
                {m.value}
                {m.unit && (
                  <span className="text-[0.34em] text-paper/55">{m.unit}</span>
                )}
              </dd>
              <dt className="mt-3">
                <Label className="!text-paper/50">{m.label}</Label>
              </dt>
            </Reveal>
          ))}
        </dl>

        <ul className="mt-section-sm grid gap-rest md:grid-cols-3">
          {results.proud.map((item, i) => (
            <Reveal as="li" key={item.title} delay={0.08 * i}>
              <h3 className="border-t border-paper/15 pt-4 font-display text-title">
                {item.title}
              </h3>
              <p className="mt-2 text-caption text-paper/60">{item.body}</p>
            </Reveal>
          ))}
        </ul>
      </div>
    </Screen>
  );
}
