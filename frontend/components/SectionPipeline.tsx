import Label from "@/components/Label";
import PipelineDiagram from "@/components/PipelineDiagram";
import Reveal from "@/components/Reveal";
import Screen from "@/components/Screen";
import { pipeline } from "@/lib/site";

/**
 * 5 — a closer look.
 *
 * This is the screen that decides whether the whole thing reads as an agent or
 * as a shuffle button, so it shows the actual mechanism rather than describing
 * it: `PipelineDiagram` is a drawing of the real graph, including the two
 * places the line bends — the gate that skips a model call when nothing has
 * changed, and the fan-out where six strategies argue and a judge picks.
 *
 * The diagram had been sitting unreferenced since the page was rebuilt around
 * a mockup that had no room for it. This is the home it was waiting for.
 *
 * It is wrapped in `overflow-x-auto` with a legible floor: below about 900px
 * the diagram scrolls sideways rather than shrinking its type into nothing.
 */
export default function SectionPipeline() {
  return (
    <Screen id="pipeline">
      <div className="mx-auto w-full max-w-content">
        <Reveal>
          <Label tone="offset" className="block">
            The loop
          </Label>
          {/* Two lines, not four. The heading carries the whole claim and the
              line under it carries the cost of making it, so the diagram can
              start high enough on the screen to be read as the subject.

              Split on the sentence rather than left to wrap: the title is two
              halves of one trade, and letting the column edge decide where it
              breaks put "out." alone on the second line. */}
          <h2 className="mt-block font-display text-headline">
            {pipeline.title
              .split(". ")
              .map((line, i, all) => (
                <span key={line} className="block">
                  {i === all.length - 1 ? line : `${line}.`}
                </span>
              ))}
          </h2>
          <p className="mt-4 max-w-measure text-title font-normal text-graphite">
            {pipeline.body}
          </p>
        </Reveal>

        <Reveal delay={0.12} className="mt-block overflow-x-auto">
          <div className="min-w-diagram">
            <PipelineDiagram />
          </div>
        </Reveal>

        {/* The three facts the drawing can't draw. Three, not four — the
            diagram is the subject of this screen and these are its caption;
            a fourth column pushes the section past one viewport.

            The heading is the fact and is set at title size; the sentence
            under it is the evidence and stays small. That ordering is the
            whole edit: at a glance the reader gets three checkable claims,
            and only on a second pass the proof of each. */}
        <dl className="mt-rest grid gap-x-10 gap-y-6 md:grid-cols-3">
          {pipeline.notes.map((note, i) => (
            <Reveal key={note.title} delay={0.2 + i * 0.08}>
              <dt className="border-t border-hairline pt-4 font-display text-title">
                {note.title}
              </dt>
              <dd className="mt-2 text-caption text-graphite">{note.body}</dd>
            </Reveal>
          ))}
        </dl>
      </div>
    </Screen>
  );
}
