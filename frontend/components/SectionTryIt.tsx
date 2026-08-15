"use client";

import { useLayoutEffect, useMemo, useRef, useState } from "react";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import ClipPicker from "@/components/ClipPicker";
import Label from "@/components/Label";
import { AnalyzeError, analyze, durationOf } from "@/lib/analyze";
import { cueAt, cuesFor, cuesFromSession, type Cue } from "@/lib/cues";
import { samples, type Sample } from "@/lib/samples";
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
 * Bundled samples and your own footage
 * ---------------------------------------------------------------------------
 * Each sample carries its own real recorded session. `lib/cues.ts` converts
 * the selected session into cues, so the footage, decisions and timeline all
 * change together.
 *
 * "Upload your own" sends a file to the agent running on this machine and
 * replaces BOTH halves -- the video and the cues beside it -- because a panel
 * reasoning about a park next to somebody's kitchen is exactly the failure
 * that kept this button switched off for so long.
 *
 * It never silently falls back to the sample. With no agent running it says
 * so, and says how to start one. That rule is why the button can be trusted
 * now that it does something.
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

  const [picking, setPicking] = useState(false);
  const [clip, setClip] = useState<Sample>(samples[0]);

  /* ---------------------------------------------------------- your footage --
     An uploaded clip replaces both halves at once: the video, and the cues
     beside it. They have to move together -- a panel reasoning about the park
     next to somebody's kitchen is the exact failure the disabled button was
     protecting against, and it costs the whole screen its credibility. */
  const [ownCues, setOwnCues] = useState<Cue[] | null>(null);
  const [busy, setBusy] = useState(false);
  const [problem, setProblem] = useState<{ what: string; hint?: string } | null>(null);
  const file = useRef<HTMLInputElement>(null);

  async function useOwnClip(chosen: File) {
    setProblem(null);
    setBusy(true);
    try {
      const [{ session }, seconds] = await Promise.all([
        analyze(chosen),
        durationOf(chosen),
      ]);
      const built = cuesFromSession(session, seconds);
      if (!built.length) {
        throw new AnalyzeError(
          "The agent watched it and decided nothing.",
          "Too short, too dark, or too still -- it holds when it is not sure.",
        );
      }
      setOwnCues(built);
      setClip({
        id: "yours",
        title: chosen.name.replace(/\.[^.]+$/, ""),
        blurb: "Your footage, read by the agent running on this machine.",
        length: clock(seconds),
        durationS: seconds,
        src: URL.createObjectURL(chosen),
        session,
        placeholder: false,
      });
      setProgress(0);
      setStarted(true);
    } catch (e) {
      const err = e as AnalyzeError;
      setProblem({ what: err.message ?? String(e), hint: err.hint });
    } finally {
      setBusy(false);
    }
  }

  const bundledCues = useMemo(
    () => cuesFor(clip.session, clip.durationS),
    [clip.session, clip.durationS],
  );
  const activeCues = ownCues ?? bundledCues;

  /** The card the clip was chosen from, so it can fly out of it. */
  const origin = useRef<DOMRect | null>(null);
  const stage = useRef<HTMLDivElement>(null);

  const cue = cueAt(progress, activeCues);

  /* ------------------------------------------------------------- the FLIP --
     The chosen card becomes the video panel rather than being replaced by it.

     First and Last are both known — the card's rect was captured on click, and
     the panel's rect can be read once it has rendered — so Invert is a
     transform from one to the other and Play is a single tween back to
     identity. No clone, no portal, no measuring twice.

     It matters more than it looks: cutting from a grid of three cards to a
     completely different layout makes the reader re-find what they picked. If
     it travels, they never lose it. */
  useLayoutEffect(() => {
    const from = origin.current;
    const panel = stage.current;
    if (!started || !from || !panel) return;

    origin.current = null;

    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;

    const to = panel.getBoundingClientRect();

    gsap.fromTo(
      panel,
      {
        // Scale about the top-left so the two rects can be matched with a
        // translate and a scale alone.
        transformOrigin: "top left",
        x: from.left - to.left,
        y: from.top - to.top,
        scaleX: from.width / to.width,
        scaleY: from.height / to.height,
      },
      {
        x: 0,
        y: 0,
        scaleX: 1,
        scaleY: 1,
        duration: 0.85,
        ease: "power3.inOut",
        clearProps: "transform",
      },
    );

    // The rest of the workbench arrives just behind the video, so the picture
    // leads and the panels settle around it.
    gsap.fromTo(
      panel.parentElement?.children ?? [],
      { autoAlpha: 0 },
      { autoAlpha: 1, duration: 0.6, delay: 0.22, ease: "power2.out", stagger: 0.06 },
    );
  }, [started]);

  const choose = (sample: Sample, from: DOMRect) => {
    origin.current = from;
    setOwnCues(null);
    setClip(sample);
    setProgress(0);
    setStamp("00:00");
    setPicking(false);
    setStarted(true);
  };

  /* The selected session owns the wheel stops too. The server-rendered page
     starts with ordinary section boundaries; once a clip is chosen, publish
     its actual decision times and ask the shared scroll controller to measure
     again. */
  useLayoutEffect(() => {
    if (!started || !root.current?.parentElement) return;

    const wrapper = root.current.parentElement;
    const stops = Array.from(
      new Set([0, ...activeCues.map((item) => Number(item.at.toFixed(4))), 1]),
    ).sort((a, b) => a - b);
    wrapper.dataset.stops = stops.join(",");
    ScrollTrigger.refresh();
  }, [started, activeCues]);

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
     Two ways in: take a bundled sample, or analyze your own clip locally. */
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

          <div className="mx-auto mt-rest max-w-[48rem] space-y-3 text-left">
            {samples.map((sample) => (
              <button
                key={sample.id}
                data-sample-card
                type="button"
                onClick={(event) =>
                  choose(sample, event.currentTarget.getBoundingClientRect())
                }
                className="group grid w-full overflow-hidden rounded-card border border-hairline bg-paper text-left
                           transition-[transform,border-color] duration-interaction ease-calm
                           hover:-translate-y-1 hover:border-ink focus-visible:-translate-y-1
                           sm:grid-cols-[minmax(220px,0.9fr)_1.1fr]"
              >
                <div className="relative aspect-[16/10] overflow-hidden bg-ink sm:aspect-auto">
                  <video
                    className="h-full w-full object-cover"
                    src={sample.src}
                    muted
                    playsInline
                    preload="metadata"
                  />
                  <span className="absolute bottom-3 right-3">
                    <Label className="!text-paper/70">{sample.length}</Label>
                  </span>
                </div>

                <div className="flex flex-col justify-center p-5 sm:p-6">
                  <div className="flex items-baseline justify-between gap-3">
                    <h3 className="font-display text-title">{sample.title}</h3>
                    {sample.placeholder && (
                      <Label className="shrink-0 !text-graphite/70">
                        placeholder
                      </Label>
                    )}
                  </div>
                  <p className="mt-2 text-caption text-graphite">{sample.blurb}</p>
                </div>
              </button>
            ))}
          </div>

          {/* Wired now, and wired honestly. The rule that kept this disabled
              still holds -- a control that silently does the OTHER thing is
              worse than one plainly switched off -- so it never falls back to
              the sample. It either shows your footage with your reasoning
              beside it, or it says exactly why it cannot.

              The row wrapper is what the merge lost: the upload control used
              to sit in a flex row beside a "use a sample" button, and when the
              chooser became a list of cards the button survived while its
              container did not. */}
          <div className="mt-rest flex flex-wrap items-center justify-center gap-3">
            <button
              type="button"
              onClick={() => file.current?.click()}
              disabled={busy}
              className="rounded-full border border-ink/25 px-8 py-4 font-mono
                         text-label uppercase transition hover:border-ink/60
                         disabled:cursor-wait disabled:text-graphite/60"
            >
              {busy ? "Watching it…" : "Upload your own"}
            </button>
            <input
              ref={file}
              type="file"
              accept="video/*"
              hidden
              onChange={(e) => {
                const chosen = e.target.files?.[0];
                e.target.value = "";
                if (chosen) void useOwnClip(chosen);
              }}
            />
          </div>

          {problem ? (
            <p className="mt-block max-w-prose font-mono text-label uppercase text-graphite">
              {problem.what}
              {problem.hint && (
                <span className="mt-2 block normal-case tracking-normal text-graphite/70">
                  {problem.hint}
                </span>
              )}
            </p>
          ) : (
            <p className="mt-block font-mono text-label uppercase text-graphite/70">
              {busy
                ? "Reading your clip — one model call per moment it notices"
                : "Uploading needs the agent running on this machine"}
            </p>
          )}
        </div>

        <ClipPicker
          open={picking}
          onClose={() => setPicking(false)}
          onPick={choose}
        />
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
          {/* Reopens the picker over the workbench rather than unwinding back
              to the chooser: changing clip is a change of subject, not a
              change of mind about being here at all. */}
          <button
            type="button"
            onClick={() => setPicking(true)}
            className="rounded-full border border-hairline px-4 py-2 font-mono text-label uppercase text-graphite transition-colors duration-interaction ease-calm hover:border-ink hover:text-ink"
          >
            Change sample clip
          </button>

          {/* The same control inside the workbench, so you can keep trying
              clips without scrolling back out to the chooser. */}
          <button
            type="button"
            onClick={() => file.current?.click()}
            disabled={busy}
            className="rounded-full border border-hairline px-4 py-2 font-mono text-label uppercase text-graphite transition-colors duration-interaction ease-calm hover:border-ink hover:text-ink disabled:cursor-wait disabled:opacity-60"
          >
            {busy ? "Watching it…" : "Upload your own"}
          </button>
        </div>
      </header>

      {/* ------------------------------------------- video · reasoning --
          2.05fr against 1fr, full window width rather than the 1320px column.
          The video is the subject of this screen; the previous split gave it
          barely half and then centred the result, which made it look like an
          illustration of a video rather than one. */}
      <div className="grid min-h-0 flex-1 gap-4 lg:grid-cols-[2.05fr_1fr]">
        <div
          ref={stage}
          className="relative min-h-0 overflow-hidden rounded-card bg-ink"
        >
          <video
            ref={video}
            key={clip.id}
            className="h-full w-full object-cover"
            src={clip.src}
            muted
            playsInline
            preload="auto"
          />
          <div className="pointer-events-none absolute inset-x-0 bottom-0 flex items-center justify-between p-4">
            <Label className="!text-paper/70">
              {clip.title}
              {clip.placeholder && " · placeholder footage"}
            </Label>
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

            {/* Everything on this line comes off the scene read. It used to
                end "10ms via gemini", which was `played.latency_ms` -- how
                long the PLAYER took, not the model. A precise number in the
                wrong place is worse than no number. */}
            <p className="mt-3 font-mono text-label lowercase tracking-normal text-graphite">
              {cue.register} · confidence {cue.confidence.toFixed(2)} · tempo{" "}
              {cue.tempo} · {cue.meter}
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

          {/* What it was hunting for, straight out of the inversion. */}
          {cue.lookingFor.length > 0 && (
            <div className="shrink-0 border-t border-hairline px-4 py-3">
              <Label>Looking for</Label>
              <p className="mt-1.5 font-mono text-[0.6875rem] leading-relaxed tracking-normal text-graphite">
                {cue.lookingFor.join(" · ")}
              </p>
            </div>
          )}

          {/* The decision log, newest first, exactly as the HUD prints it. */}
          {/* `overflow-x-hidden` as well as y: setting only `overflow-y`
              makes the x axis `auto` too, and the log lines were `pre`, so a
              long one produced a second scrollbar across the bottom of the
              panel. Two scrollbars on a 300px card reads as broken. The lines
              wrap now instead, which is what a log should do at this width. */}
          <div className="min-h-0 flex-1 overflow-y-auto overflow-x-hidden border-t border-hairline px-4 py-3">
            <ul className="space-y-1.5">
              {cue.log.map((line) => (
                <li
                  key={line}
                  className="whitespace-pre-wrap break-words font-mono text-[0.6875rem] leading-relaxed tracking-normal text-graphite"
                >
                  {line}
                </li>
              ))}
            </ul>

            {/* The candidates that LOST, with their scores.
                This is the most convincing thing in the panel and it costs
                nothing — the session file already records everything each
                strategy proposed. One answer appearing looks like a lookup;
                nine answers ranked, with the winner two points clear, looks
                like a decision. */}
            {cue.considered.length > 0 && (
              <table className="mt-4 w-full border-t border-hairline pt-3 text-left">
                <caption className="pb-2 text-left">
                  <Label>Also considered</Label>
                </caption>
                <tbody>
                  {cue.considered.slice(0, 6).map((c, i) => (
                    <tr key={c.title + c.strategy} className="align-baseline">
                      <td className="py-0.5 pr-2 font-mono text-[0.6875rem] tracking-normal text-graphite">
                        {c.score.toFixed(3)}
                      </td>
                      <td
                        className={`py-0.5 pr-2 text-caption ${
                          i === 0 ? "text-ink" : "text-graphite"
                        }`}
                      >
                        {c.title}
                      </td>
                      <td className="py-0.5 font-mono text-[0.625rem] tracking-normal text-graphite/70">
                        {c.strategy}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
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

            {activeCues.map((c) => {
              const active = c.time === cue.time;
              return (
                <div
                  key={`${c.time}-${c.track}`}
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

      <ClipPicker
        open={picking}
        onClose={() => setPicking(false)}
        onPick={choose}
      />
    </section>
  );
}
