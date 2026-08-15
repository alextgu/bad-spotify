"use client";

import { useLayoutEffect, useRef, useState } from "react";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import Label from "@/components/Label";
import { cueAt, cues } from "@/lib/cues";
import { tryIt } from "@/lib/site";

gsap.registerPlugin(ScrollTrigger);

/**
 * 4 — try it. The screen you scroll *through* rather than past.
 *
 * The page scroll is the transport. This section pins itself, and the next few
 * screens of scrolling move the clip: each gesture advances to the next
 * checkpoint, the video seeks there, the timeline playhead moves there, and
 * the right-hand column shows what the agent was doing at that moment.
 *
 * That is the argument of the screen. A play button gives you a video to
 * watch; this gives you one you are driving, and it means the reasoning beside
 * it can never get ahead of what you are looking at.
 *
 * ---------------------------------------------------------------------------
 * Checkpoints, not free scrub
 * ---------------------------------------------------------------------------
 * The stops are the cues themselves — the moments where the agent actually did
 * something — not evenly spaced screenfuls. So the section reads as a sequence
 * of decisions rather than as a video with a scrubber attached, and you cannot
 * land between two states and see a reasoning panel describing neither.
 *
 * `ScrollController` is told about them by `data-stops` on the wrapper in
 * page.tsx: a comma-separated list of fractions of this section's scroll
 * length. Those override its usual one-screen-per-gesture stepping for this
 * block only.
 *
 * ---------------------------------------------------------------------------
 * What this costs
 * ---------------------------------------------------------------------------
 * This section is NOT one viewport. It is one viewport of content pinned while
 * `SCRUB_SCREENS` worth of scroll passes through it, so the page is seven
 * sections, one of which is long. Scrubbing needs scroll to spend and there is
 * nowhere else to get it.
 *
 * ---------------------------------------------------------------------------
 * Still placeholder
 * ---------------------------------------------------------------------------
 * The cue data is `lib/cues.ts`, not `public/sessions/sample.json`. The shape
 * mirrors the session file and the live HUD, so wiring it is a swap rather
 * than a rewrite. The two source buttons are inert.
 */

/** Screens of scrolling spent inside the section. */
const SCRUB_SCREENS = 3;

const clock = (seconds: number) => {
  if (!Number.isFinite(seconds)) return "00:00";
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
};

export default function SectionTryIt() {
  const root = useRef<HTMLElement>(null);
  const video = useRef<HTMLVideoElement>(null);
  const track = useRef<HTMLDivElement>(null);
  const [progress, setProgress] = useState(0);
  const [stamp, setStamp] = useState("00:00");

  /**
   * The section opens on a chooser and only becomes the workbench once a clip
   * is picked. That is not just presentation: **until it starts, this section
   * does not pin and does not take the scroll.**
   *
   * Otherwise the section would be four screens long and eat three gestures of
   * scrubbing from anybody who has no intention of using it, which is a toll
   * booth on the way to the rest of the page. Unstarted, it is one ordinary
   * screen you pass in one gesture. Started, it grows to four and takes them.
   */
  const [started, setStarted] = useState(false);

  const cue = cueAt(progress);

  useLayoutEffect(() => {
    if (!started) return;

    const mm = gsap.matchMedia();

    mm.add("(min-width: 1000px)", () => {
      const ctx = gsap.context(() => {
        ScrollTrigger.create({
          trigger: root.current,
          start: "top top",
          end: () => "+=" + window.innerHeight * SCRUB_SCREENS,
          pin: true,
          scrub: 0.5,
          invalidateOnRefresh: true,
          onUpdate: (self) => {
            const p = self.progress;
            setProgress(p);

            const el = video.current;
            if (el && Number.isFinite(el.duration) && el.duration > 0) {
              // Seeking rather than playing: the scroll position IS the
              // playhead, so the picture and the reasoning can never disagree.
              el.currentTime = Math.min(el.duration * p, el.duration - 0.01);
              setStamp(clock(el.duration * p));
            }

            const strip = track.current;
            if (strip) {
              const overflow = Math.max(
                0,
                strip.scrollWidth - (strip.parentElement?.clientWidth ?? 0),
              );
              gsap.set(strip, { x: -overflow * p });
            }
          },
        });
      }, root);

      return () => ctx.revert();
    });

    // The pin changes the document height, so the page's stop positions are
    // now wrong. Refreshing makes ScrollController re-measure — see the
    // `refresh` listener there.
    ScrollTrigger.refresh();

    return () => mm.revert();
  }, [started]);

  /* ------------------------------------------------------------ chooser --
     One screen, three ways out: take the sample, bring your own, or leave.
     The skip is a plain text link rather than a third button on purpose —
     it should be findable and not competitive. A demo you cannot decline is
     a demo people resent. */
  if (!started) {
    return (
      <section
        ref={root}
        id="try"
        className="flex h-svh flex-col justify-center overflow-hidden bg-bone px-gutter"
      >
        <div className="mx-auto w-full max-w-content text-center">
          <Label tone="offset">Try it</Label>
          <h2 className="mx-auto mt-block max-w-[18ch] font-display text-headline">
            {tryIt.title}
          </h2>
          <p className="mx-auto mt-block max-w-measure-sub text-body text-graphite">
            {tryIt.body}
          </p>

          <div className="mt-section-sm flex flex-wrap items-center justify-center gap-3">
            <button
              type="button"
              onClick={() => setStarted(true)}
              className="rounded-full bg-ink px-8 py-4 font-mono text-label uppercase text-paper
                         transition-[transform,background-color] duration-interaction ease-calm
                         hover:-translate-y-0.5 hover:bg-offset-ink"
            >
              Use the sample clip
            </button>

            {/* Gated, and gated visibly. It could have been wired to start the
                sample run so the button did *something*, but a control that
                silently does the other thing is worse than one that is plainly
                switched off — the first time someone uploads a clip and
                watches the kitchen footage play, they stop trusting the rest
                of the screen. */}
            <button
              type="button"
              disabled
              aria-disabled
              title="Not wired up yet"
              className="cursor-not-allowed rounded-full border border-ink/15 px-8 py-4
                         font-mono text-label uppercase text-graphite/60"
            >
              Upload your own
            </button>
          </div>

          <p className="mt-block font-mono text-label uppercase text-graphite/70">
            Uploading is not wired up yet
          </p>

          <p className="mt-rest">
            <a
              href="#pipeline"
              className="font-mono text-label uppercase text-graphite underline decoration-hairline underline-offset-4 transition-colors duration-interaction ease-calm hover:text-ink"
            >
              Skip this →
            </a>
          </p>
        </div>
      </section>
    );
  }

  return (
    <section
      ref={root}
      id="try"
      className="flex h-svh flex-col overflow-hidden bg-bone px-gutter py-6"
    >
      {/* ---------------------------------------------------------- source -- */}
      <header className="flex shrink-0 flex-wrap items-baseline justify-between gap-3 pb-4">
        <div className="flex items-baseline gap-4">
          <Label tone="offset">Try it</Label>
          <h2 className="font-display text-title">{tryIt.title}</h2>
        </div>

        <div className="flex items-center gap-2">
          {/* Goes back to the chooser. That is also the way out of the
              section, which is why there is no separate close: two controls
              that both mean "stop looking at this" is one too many. */}
          <button
            type="button"
            onClick={() => setStarted(false)}
            className="rounded-full border border-hairline px-4 py-2 font-mono text-label uppercase text-graphite transition-colors duration-interaction ease-calm hover:border-ink hover:text-ink"
          >
            Change sample clip
          </button>

          <button
            type="button"
            disabled
            aria-disabled
            title="Not wired up yet"
            className="cursor-not-allowed rounded-full border border-hairline/60 px-4 py-2 font-mono text-label uppercase text-graphite/50"
          >
            Upload your own
          </button>
        </div>
      </header>

      {/* ------------------------------------------- video · reasoning --
          2.05fr against 1fr, full window width rather than the 1320px column.
          The video is the subject of this screen; the previous split gave it
          barely half and then centred the result, which made it look like an
          illustration of a video rather than one. */}
      <div className="grid min-h-0 flex-1 gap-4 lg:grid-cols-[2.05fr_1fr]">
        <div className="relative min-h-0 overflow-hidden rounded-card bg-ink">
          <video
            ref={video}
            className="h-full w-full object-cover"
            src="/videos/sample.mp4"
            muted
            playsInline
            preload="auto"
          />
          <div className="pointer-events-none absolute inset-x-0 bottom-0 flex items-center justify-between p-4">
            <Label className="!text-paper/70">sample.mp4</Label>
            <Label className="!text-paper/70">{stamp}</Label>
          </div>
        </div>

        {/* One card, read top to bottom in the order the agent works: what it
            saw, what it thought, and then — last, at the foot — what it put
            on. The live HUD keeps these as two separate panels, but the
            conclusion belongs under its own evidence rather than floating
            above it in a box of its own.

            Not a checklist of the six steps: those are identical at every
            checkpoint and say nothing about this moment. Everything here
            changes as you scroll, which is the only reason to look at the
            column at all. */}
        <div className="flex min-h-0 flex-col overflow-hidden rounded-card border border-hairline bg-paper">
          {/* ------------------------------------------------ what it sees -- */}
          <div className="shrink-0 p-4 pb-3">
            <Label>What it sees</Label>
            <p className="mt-2 text-body leading-snug">{cue.sees}</p>

            <p className="mt-3 font-mono text-label lowercase tracking-normal text-graphite">
              {cue.register} · confidence {cue.confidence.toFixed(2)} ·{" "}
              {cue.latency}ms via {cue.model}
            </p>

            {/* The palette pulled out of the frame. */}
            <div className="mt-3 flex gap-1.5">
              {cue.palette.map((colour) => (
                <span
                  key={colour}
                  className="h-6 w-6 rounded-sm border border-hairline"
                  style={{ backgroundColor: colour }}
                  title={colour}
                />
              ))}
            </div>
          </div>

          {/* The decision log, newest first, exactly as the HUD prints it. */}
          <div className="min-h-0 flex-1 overflow-y-auto border-t border-hairline px-4 py-3">
            <ul className="space-y-1.5">
              {cue.log.map((line) => (
                <li
                  key={line}
                  className="whitespace-pre font-mono text-[0.6875rem] leading-relaxed tracking-normal text-graphite"
                >
                  {line}
                </li>
              ))}
            </ul>
          </div>

          {/* ------------------------------------------------- now playing --
              The conclusion, at the foot of the evidence. Slightly darker
              ground so it reads as the answer rather than as one more row. */}
          <div className="shrink-0 border-t border-hairline bg-bone p-4">
            <Label>Now playing</Label>
            <p className="mt-2 font-display text-title leading-tight">{cue.track}</p>
            <p className="text-caption text-graphite">{cue.artist}</p>
            <p className="mt-2 text-caption italic text-graphite">{cue.why}</p>
          </div>
        </div>
      </div>

      {/* -------------------------------------------------------- timeline --
          No scrollbar of its own. The page scroll moves it, so the track is
          transformed rather than scrolled — an inner scroller would be a
          second, competing transport for the same value. */}
      <div className="mt-4 shrink-0 rounded-card border border-hairline bg-paper">
        <div className="flex items-baseline justify-between px-4 pt-3">
          <Label>Timeline</Label>
          <Label>scroll to move</Label>
        </div>

        <div className="relative overflow-hidden px-4 pb-3 pt-3">
          {/* The playhead is fixed and the track moves under it, rather than
              the other way round. The current moment is therefore always in
              the same place on screen, which is what makes it readable. */}
          <div className="pointer-events-none absolute left-4 top-3 z-10 h-14 w-px bg-offset-ink" />

          <div ref={track} className="relative w-[190%] will-change-transform">
            <div className="h-px w-full bg-hairline" />

            {cues.map((c) => {
              const active = c.time === cue.time;
              return (
                <div
                  key={c.time}
                  className="absolute top-0 w-44"
                  style={{ left: `${c.at * 100}%` }}
                >
                  <span
                    aria-hidden
                    className={`block h-2 w-px ${active ? "bg-offset-ink" : "bg-hairline"}`}
                  />
                  <Label
                    tone={active ? "offset" : "quiet"}
                    className="mt-1 block"
                  >
                    {c.time}
                  </Label>
                  <p
                    className={`truncate text-caption ${
                      active ? "text-ink" : "text-graphite"
                    }`}
                  >
                    {c.label}
                  </p>
                </div>
              );
            })}

            {/* Reserves the height the absolutely-placed cues occupy. */}
            <div className="h-14" />
          </div>
        </div>
      </div>
    </section>
  );
}
