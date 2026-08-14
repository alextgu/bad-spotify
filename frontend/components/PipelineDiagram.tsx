/**
 * TODO(team): the diagram judges will actually read.
 *
 * The six steps, in order. Keep it plain enough that someone who has never
 * seen the project understands it without narration:
 *
 *   1. Look          take a picture, listen for a few seconds
 *   2. Anything new? if not, skip the expensive thinking and reuse the last
 *                    read -- but still carry on to step 6
 *   3. Understand    one question describes the whole moment
 *   4. Flip it       compute the opposite of that feeling
 *   5. Pick          three theories of "worst" compete, funniest wins
 *   6. Queue or cut  line it up, or interrupt if the room really changed
 *
 * An inline SVG is probably right -- it scales on a projector and needs no
 * dependency.
 */
export default function PipelineDiagram() {
  return (
    <div className="rounded-xl border border-dashed border-white/15 p-8 text-center text-sm text-ink-muted">
      TODO(team): pipeline diagram
    </div>
  );
}
