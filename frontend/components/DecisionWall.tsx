import Label from "@/components/Label";
import Reveal from "@/components/Reveal";
import Screen from "@/components/Screen";
import { decisionModel, decisions, distinctTracks } from "@/lib/decisions";

/**
 * 6b — every decision it has made, on one screen.
 *
 * ---------------------------------------------------------------------------
 * WHY A TABLE AND NOT A CAROUSEL
 * ---------------------------------------------------------------------------
 * The screen before this one is four numbers and three sentences, which is a
 * claim. This is the evidence for it, and evidence is more convincing when it
 * is boring: a list you can read top to bottom in one pass, with nothing to
 * operate and nothing revealed on hover. Anything the reader has to click is
 * something they can suspect you of having curated.
 *
 * Six rows because six is what exists. It is not a sample of a larger set and
 * it is not the best six — `lib/decisions.ts` flattens the recorded sessions
 * in order and this renders all of them, so a bad one cannot be left out
 * without deleting a clip.
 *
 * The count is read off the data rather than written into the sentence. The
 * first draft of this file said "seven", because the synthetic clip was in the
 * list while the heading was being written and out of it by the time the page
 * rendered. A number typed into copy is a number that goes stale silently.
 *
 * ---------------------------------------------------------------------------
 * THE LEFT COLUMN IS THE POINT
 * ---------------------------------------------------------------------------
 * "Reads it as" carries the specificity the whole system depends on — the
 * difference between "indoor event" and "birthday celebration, cake being
 * cut". If a row's left side is vague, that row is worthless however funny
 * the right side is, and printing them side by side is the only honest way to
 * let someone check that.
 *
 * The confidence is printed for the same reason. It is the one number on this
 * page that could embarrass us, and leaving it off would make the wall a
 * highlight reel.
 */

/** Fit the row count to the screen without a scrollbar appearing at 900px. */
const ROW_TEXT = "text-[clamp(0.72rem,1.35vh,0.9375rem)]";

/** "six", not "6" — this reads as a sentence, and 1-12 belong in words. */
const WORDS = [
  "no", "one", "two", "three", "four", "five", "six",
  "seven", "eight", "nine", "ten", "eleven", "twelve",
];
const spell = (n: number) => WORDS[n] ?? String(n);

export default function DecisionWall() {
  const count = decisions.length;
  const noRepeats = distinctTracks === count && count > 1;

  return (
    <Screen id="decisions" className="bg-ink text-paper">
      <div className="mx-auto w-full max-w-content">
        <Reveal>
          <Label className="!text-paper/50">Every decision, in full</Label>
          <h2 className="mt-block font-display text-headline">
            {spell(count).replace(/^\w/, (c) => c.toUpperCase())} moments, and
            what it did about them.
          </h2>
          <p className="mt-4 max-w-[46rem] text-caption text-paper/60">
            Read out of the recorded sessions in{" "}
            <code className="text-paper/80">public/sessions/</code>, in the
            order the clips play them
            {decisionModel ? ` — every read by ${decisionModel}` : ""}. Nothing
            is filtered or reordered: this is all of them
            {noRepeats
              ? `, and ${spell(count)} different songs out of a corpus of 47`
              : ""}
            .
          </p>
        </Reveal>

        <div className="mt-rest overflow-x-auto">
          <table className={`w-full min-w-[52rem] border-collapse ${ROW_TEXT}`}>
            <thead>
              <tr className="border-b border-paper/20 text-left align-bottom">
                <th className="pb-3 pr-4 font-normal">
                  <Label className="!text-paper/45">Reads it as</Label>
                </th>
                <th className="pb-3 pr-4 font-normal">
                  <Label className="!text-paper/45">Confidence</Label>
                </th>
                <th className="pb-3 pr-4 font-normal">
                  <Label className="!text-offset">Plays</Label>
                </th>
                <th className="pb-3 font-normal">
                  <Label className="!text-paper/45">Because</Label>
                </th>
              </tr>
            </thead>

            <tbody>
              {/* No staggered reveal per row: seven rows arriving one after
                  another turns a table into a performance, and the table's
                  whole argument is that it is not one. */}
              {decisions.map((d) => (
                <tr
                  key={d.id}
                  className="border-b border-paper/10 align-top last:border-0"
                >
                  <td className="py-3 pr-4">
                    <span className="block text-paper/85">{d.sees}</span>
                    <span className="mt-1 block font-mono text-[0.82em] text-paper/40">
                      {d.clip} · {d.at} · {d.mood}
                    </span>
                  </td>

                  {/* Tabular figures, so the column reads as a column. */}
                  <td className="py-3 pr-4 font-mono tabular-nums text-paper/70">
                    {d.confidence.toFixed(2)}
                  </td>

                  <td className="py-3 pr-4">
                    <span className="block font-semibold text-offset">
                      {d.track}
                    </span>
                    <span className="mt-1 block text-paper/50">{d.artist}</span>
                  </td>

                  <td className="py-3 text-paper/60">
                    <span className="block">{d.why}</span>
                    <span className="mt-1 block font-mono text-[0.82em] text-paper/35">
                      {d.strategy}
                      {d.runnersUp.length
                        ? ` · turned down ${d.runnersUp
                            .slice(0, 2)
                            .join(", ")}`
                        : ""}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </Screen>
  );
}
