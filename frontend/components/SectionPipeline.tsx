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
 * It is wrapped in `overflow-x-auto` with a legible floor: below about 700px
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
          <h2 className="mt-block max-w-[14ch] font-display text-headline">
            {pipeline.title}
          </h2>
          <p className="mt-block max-w-measure text-body text-graphite">
            {pipeline.body}
          </p>
        </Reveal>

        <Reveal delay={0.12} className="mt-block overflow-x-auto">
          <div className="min-w-diagram">
            <PipelineDiagram />
          </div>
        </Reveal>

        {/* The three decisions the drawing can't show. Three, not four —
            the diagram is the subject of this screen and these are its
            caption; a fourth column pushes the section past one viewport. */}
        <dl className="mt-block grid gap-x-8 gap-y-5 md:grid-cols-3">
          {pipeline.notes.map((note, i) => (
            <Reveal key={note.title} delay={0.2 + i * 0.08}>
              <dt className="border-t border-hairline pt-3 font-display text-[0.95rem] font-semibold">
                {note.title}
              </dt>
              <dd className="mt-1.5 text-caption text-graphite">{note.body}</dd>
            </Reveal>
          ))}
        </dl>
      </div>
    </Screen>
  );
}
