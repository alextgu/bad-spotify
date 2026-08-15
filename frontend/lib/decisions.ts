import type { Moment, Session } from "@/lib/types";
import { samples } from "@/lib/samples";
import { stamp } from "@/lib/types";

/**
 * Every decision the agent has actually made, flattened out of the recorded
 * sessions.
 *
 * ---------------------------------------------------------------------------
 * WHY THIS FILE EXISTS
 * ---------------------------------------------------------------------------
 * The site could describe the machinery at length and could not show, on one
 * screen, a single thing it had decided. The try-it workbench holds all of
 * this already, but one clip at a time and behind a picker — which reads as a
 * demo you have to operate rather than as a result you can check.
 *
 * ---------------------------------------------------------------------------
 * WHERE THE ROWS COME FROM, AND WHERE THEY DO NOT
 * ---------------------------------------------------------------------------
 * `samples` — the three filmed clips, each with a session produced by the live
 * model. Nothing here is typed, curated, or re-run until it looked good; a
 * decision appears on the wall exactly as it was recorded, including the two
 * separate moments that both landed on classical.
 *
 * `sessions/sample.json` is deliberately NOT among them. It is the synthetic
 * clip from before there was footage, its `model` field is null, and mixing it
 * in would put a mock read next to three real ones with nothing distinguishing
 * them. It still drives the pipeline diagram, where it is labelled.
 *
 * `results/gallery.json` — written by `scripts/run_samples.py` from typed
 * scenes — is not read here either, and should not be until it has been
 * generated on a machine with a GOOGLE_API_KEY. Without one, perception falls
 * back to a keyword reader that gets scenes wrong in ways that look fine in a
 * table: it read "a packed nightclub at 1am" as dark and quiet, and two of the
 * twelve fell through to a flat 0.5 on every axis, which makes the inversion
 * meaningless. The script says which backend it ran on in its own output; the
 * bar for appearing on this wall is that the answer be "gemini".
 */

/** One recorded decision, ready to render. */
export interface Decision {
  id: string;
  /** Which clip it came from, for the row's provenance. */
  clip: string;
  /** Where in that clip the song landed, "00:27". */
  at: string;
  /** What the model reported seeing. */
  sees: string;
  mood: string;
  confidence: number;
  /** What it played about it. */
  track: string;
  artist: string;
  /** Which theory of wrongness won. */
  strategy: string;
  /** The reasoning, with the strategy prefix stripped — the row shows it. */
  why: string;
  /** The tracks it turned down, in the order it turned them down. */
  runnersUp: string[];
  /** Measured after the fact, never set. Null when the run predates it. */
  mismatch: number | null;
}

/**
 * `"score-weighted choice via semantic_opposite: quiet, academic -> noisy"`
 * is two facts joined by a colon, and the first one is already the strategy
 * chip beside it. Keeping both prints the strategy name twice per row.
 */
function reason(raw: string | null | undefined): string {
  if (!raw) return "";
  const split = raw.indexOf(": ");
  return split === -1 ? raw : raw.slice(split + 2);
}

function fromMoment(clip: string, index: number, moment: Moment): Decision[] {
  const chosen = moment.chosen;
  const played = moment.played;
  if (!chosen?.title || !played) return [];

  return [
    {
      id: `${clip}-${index}`,
      clip,
      at: stamp(played.at_video_time ?? moment.video_time),
      sees: [moment.scene.setting, moment.scene.activity]
        .filter(Boolean)
        .join(", "),
      mood: moment.scene.mood ?? "unknown",
      confidence: moment.scene.confidence ?? 0,
      track: chosen.title,
      artist: chosen.artist ?? "Unknown artist",
      strategy: chosen.strategy ?? "unknown",
      why: reason(chosen.why),
      runnersUp: chosen.runner_ups ?? [],
      mismatch: chosen.mismatch,
    },
  ];
}

/** Every decision, in the order the clips play them. */
export const decisions: Decision[] = samples.flatMap((sample) =>
  ((sample.session as Session).moments ?? []).flatMap((moment, i) =>
    fromMoment(sample.title, i, moment),
  ),
);

/**
 * The model that produced them, or null if the clips disagree.
 *
 * They do not disagree today — all three sessions name gemini-3.5-flash-lite —
 * but the wall states the model as fact, so it has to be derived rather than
 * typed out. If someone re-runs one clip on a different model this returns
 * null and the wall says "mixed" instead of quietly naming the wrong one.
 */
export const decisionModel: string | null = (() => {
  const named = samples
    .map((s) => (s.session as Session).model)
    .filter((m): m is string => Boolean(m));
  const unique = [...new Set(named)];
  return unique.length === 1 && named.length === samples.length
    ? unique[0]
    : null;
})();

/** How many distinct tracks the wall covers — the corpus is 47. */
export const distinctTracks = new Set(decisions.map((d) => d.track)).size;
