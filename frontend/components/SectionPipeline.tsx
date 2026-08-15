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

        <Reveal delay={0.12} className="mt-rest overflow-x-auto">
          <div className="min-w-diagram">
            <PipelineDiagram />
          </div>
        </Reveal>
      </div>
    </Screen>
  );
}
