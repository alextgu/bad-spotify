import Label from "@/components/Label";
import Screen from "@/components/Screen";
import { tryIt } from "@/lib/site";

/**
 * 4 — try it. The one screen you can operate.
 *
 * STRUCTURE ONLY at this stage. Every panel below is laid out and sized, and
 * the video element is real, but nothing is wired: the timeline does not scrub
 * yet, the process column is stubbed, and the source controls do not load
 * anything. That is deliberate — the layout is the part that has to survive
 * contact with a 693px-tall laptop, and it is much cheaper to find out now
 * than after the playback logic is threaded through it.
 *
 * ---------------------------------------------------------------------------
 * The four regions
 * ---------------------------------------------------------------------------
 *
 *   ┌───────────────────────────────────────────────┐
 *   │ source            change the clip · add own   │  auto height
 *   ├──────────────────────────┬────────────────────┤
 *   │ the video                │ what it is doing   │  flex-1
 *   │                          │ (the reasoning)    │
 *   ├──────────────────────────┴────────────────────┤
 *   │ timeline — horizontal scroll, drag to scrub   │  fixed, skinny
 *   └───────────────────────────────────────────────┘
 *
 * The reasoning column is the reason this screen exists. Watching it choose is
 * the difference between an agent and a shuffle button, and a video on its own
 * shows the result while hiding the argument — so the two sit side by side at
 * the same size rather than the reasoning being a caption under the picture.
 *
 * ---------------------------------------------------------------------------
 * Why it has its own background
 * ---------------------------------------------------------------------------
 * `bg-bone` and `data-strings="off"` on the wrapper in page.tsx, both on
 * purpose: this is the one screen with fine detail and a draggable control on
 * it, and drifting lines behind a timeline you are trying to aim at is noise
 * exactly where precision is wanted. The opaque panel also gives the controls
 * an edge to sit against.
 */

/** Placeholder cue marks until the session file drives them. */
const CUES = [
  { at: "00:04", label: "Kitchen, warm light" },
  { at: "00:18", label: "Someone leaves" },
  { at: "00:31", label: "Lights down" },
  { at: "00:47", label: "Room empties" },
  { at: "01:06", label: "Quiet" },
];

/** Placeholder rows for the reasoning column. */
const STEPS = [
  { step: "01", title: "Look", body: "Frame plus the last few seconds of sound." },
  { step: "02", title: "Notice", body: "Enough changed to be worth a model call." },
  { step: "03", title: "Understand", body: "Waiting on the read." },
  { step: "04", title: "Invert", body: "—" },
  { step: "05", title: "Choose", body: "—" },
  { step: "06", title: "Commit", body: "—" },
];

export default function SectionTryIt() {
  return (
    <Screen id="try" className="bg-bone">
      <div className="mx-auto flex h-full w-full max-w-content flex-col gap-4 py-2">
        {/* ------------------------------------------------------- source -- */}
        <header className="flex flex-wrap items-baseline justify-between gap-3">
          <div>
            <Label tone="offset">Try it</Label>
            <h2 className="mt-1 font-display text-title">{tryIt.title}</h2>
          </div>

          {/* The small section for changing the clip. Buttons are inert until
              the player is wired. */}
          <div className="flex items-center gap-2">
            <button
              type="button"
              className="rounded-full border border-hairline px-4 py-2 font-mono text-label uppercase text-graphite transition-colors duration-interaction ease-calm hover:border-ink hover:text-ink"
            >
              Sample clip
            </button>
            <button
              type="button"
              className="rounded-full border border-hairline px-4 py-2 font-mono text-label uppercase text-graphite transition-colors duration-interaction ease-calm hover:border-ink hover:text-ink"
            >
              Use your own
            </button>
          </div>
        </header>

        {/* ------------------------------------------- video · reasoning -- */}
        <div className="grid min-h-0 flex-1 gap-4 lg:grid-cols-[1.35fr_1fr]">
          {/* left — the video */}
          <div className="relative min-h-0 overflow-hidden rounded-card bg-ink">
            <video
              className="h-full w-full object-cover"
              src="/videos/sample.mp4"
              muted
              playsInline
              preload="metadata"
            />
            <div className="pointer-events-none absolute inset-x-0 bottom-0 flex items-center justify-between p-4">
              <Label className="!text-paper/70">sample.mp4</Label>
              <Label className="!text-paper/70">00:00</Label>
            </div>
          </div>

          {/* right — what it is doing */}
          <div className="flex min-h-0 flex-col overflow-hidden rounded-card border border-hairline bg-paper">
            <div className="flex items-baseline justify-between border-b border-hairline px-4 py-3">
              <Label>What it is doing</Label>
              <Label tone="offset">live</Label>
            </div>

            <ol className="min-h-0 flex-1 overflow-y-auto">
              {STEPS.map((s) => (
                <li
                  key={s.step}
                  className="flex gap-3 border-b border-hairline px-4 py-3 last:border-b-0"
                >
                  <Label className="shrink-0 pt-1">{s.step}</Label>
                  <div className="min-w-0">
                    <p className="font-display text-[0.95rem] font-semibold">
                      {s.title}
                    </p>
                    <p className="mt-0.5 text-caption text-graphite">{s.body}</p>
                  </div>
                </li>
              ))}
            </ol>

            <div className="border-t border-hairline px-4 py-3">
              <Label>Now playing</Label>
              <p className="mt-1 font-display text-[0.95rem] font-semibold text-graphite">
                Nothing yet
              </p>
            </div>
          </div>
        </div>

        {/* ----------------------------------------------------- timeline --
            Skinny, horizontally scrollable, and wider than the screen on
            purpose: the whole point is that you drag along it. The inner track
            is `min-w` rather than `w-full` so it always overflows and always
            has somewhere to scroll to. */}
        <div className="shrink-0 rounded-card border border-hairline bg-paper">
          <div className="flex items-baseline justify-between px-4 pt-3">
            <Label>Timeline</Label>
            <Label>drag to scrub</Label>
          </div>

          <div className="overflow-x-auto px-4 pb-3 pt-2">
            <div className="relative min-w-[1400px]">
              {/* the track */}
              <div className="h-px w-full bg-hairline" />

              {/* the playhead */}
              <div className="absolute left-0 top-0 h-6 w-px -translate-y-2.5 bg-offset-ink" />

              {/* cue marks */}
              <ul className="relative mt-2 flex">
                {CUES.map((cue, i) => (
                  <li
                    key={cue.at}
                    className="shrink-0"
                    style={{ width: `${100 / CUES.length}%` }}
                  >
                    <span
                      aria-hidden
                      className={`block h-2 w-px ${
                        i === 0 ? "bg-offset-ink" : "bg-hairline"
                      }`}
                    />
                    <Label className="mt-1 block">{cue.at}</Label>
                    <p className="truncate text-caption text-graphite">{cue.label}</p>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      </div>
    </Screen>
  );
}
