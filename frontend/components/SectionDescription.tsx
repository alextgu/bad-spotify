"use client";

import { useLayoutEffect, useRef, useState } from "react";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import GlassesModel from "@/components/GlassesModel";
import Label from "@/components/Label";
import Slot from "@/components/Slot";
import { description } from "@/lib/site";

gsap.registerPlugin(ScrollTrigger);

/**
 * 2 — what it is, argued by example rather than described.
 *
 * The section pins itself and plays three beats as you scroll:
 *
 *   1. the statement, alone
 *   2. a sunlit park floods in from the left, and gets Drowning Pool
 *   3. a quiet library arrives from the right, and gets Sandstorm
 *
 * The alternating sides are doing real work. Both examples have the same
 * shape — scene, read, track, reason — and shown in the same place twice the
 * second one reads as a repeat of the first. Coming from the opposite edge it
 * reads as a second instance, which is the whole argument: it isn't a
 * one-liner, it's a system that does this every time.
 *
 * **Both examples are real output.** The park is the recorded run in
 * public/sessions/sample.json, down to the 0.911 score. The library is the
 * other case the headless run is checked against. Nothing here is an
 * illustration of what it might do.
 *
 * This used to be a statement and three abstractions — "reads the room",
 * "scores it", "drops the needle". Those describe a category; these describe
 * a decision, and one worked example is worth all three.
 */

/**
 * Beats of scroll spent inside the section.
 *
 * This was 2.4 and the section felt stuck at the end: the second example had
 * finished arriving by 0.8 progress, so the last full gesture of the pin
 * changed nothing on screen. A pinned section that stops responding is
 * indistinguishable from a broken one. Every beat now does something, and the
 * pin releases the moment the last one lands.
 */
const BEATS = 2;

/** Ramp a value across a progress window, clamped at both ends. */
const ramp = (p: number, from: number, to: number) =>
  Math.min(1, Math.max(0, (p - from) / (to - from)));

export default function SectionDescription() {
  const root = useRef<HTMLElement>(null);
  const intro = useRef<HTMLDivElement>(null);
  /** The two halves. They persist; only their side and contents change. */
  const scene = useRef<HTMLDivElement>(null);
  const words = useRef<HTMLDivElement>(null);
  /** Two of each, crossfaded as the halves swap sides. */
  const scenes = useRef<(HTMLDivElement | null)[]>([]);
  const blocks = useRef<(HTMLDivElement | null)[]>([]);
  const [active, setActive] = useState(-1);

  useLayoutEffect(() => {
    const mm = gsap.matchMedia();

    mm.add("(min-width: 1000px) and (prefers-reduced-motion: no-preference)", () => {
      const ctx = gsap.context(() => {
        ScrollTrigger.create({
          trigger: root.current,
          start: "top top",
          end: () => "+=" + window.innerHeight * BEATS,
          pin: true,
          scrub: 0.6,
          invalidateOnRefresh: true,
          onUpdate: (self) => {
            const p = self.progress;

            /* Three things happen, and none of them is a page arriving.

               The statement clears. The two halves fade up in place. Then the
               halves TRADE SIDES — the scene slides from the left half to the
               right, the words slide the other way past it, and their contents
               crossfade during the pass. Nothing enters from off-screen and
               nothing leaves; the section rearranges what it is already
               holding, which is what makes it read as one page thinking rather
               than as three pages in a row. */

            /* Three separate ramps, not one, for the same reason the swap
               doesn't crossfade: two blocks of type at half opacity are
               unreadable. The statement clears first, the panel slides in over
               the space it left, and only then does the example's copy arrive.
               Sharing one ramp put the statement and "Bodies" on top of each
               other at 50% each. */
            /* THE STOPS MUST NOT LAND INSIDE THESE WINDOWS.
               `data-stops` in page.tsx is 0 / 0.45 / 1, so the middle stop has
               to fall after `wordsIn` completes (0.44) and before `swap`
               begins (0.5). It used to be 0.5 — a tenth of the way into the
               swap — which parked the section with the scene panel slid 10%
               into the words half. The panel is opaque and sits on top, so it
               covered the first letters of the track name: "Bodies" came to
               rest reading "dies". Anything that moves must be finished, or
               not yet started, at every stop. */
            const introOut = ramp(p, 0.06, 0.2);
            const opened = ramp(p, 0.12, 0.34);
            const wordsIn = ramp(p, 0.3, 0.44);
            const swap = ramp(p, 0.5, 0.86);

            /* The statement doesn't fade out on its own — it is pushed. The
               scene panel slides in from off the left edge and shoves the
               centred type to the right as it arrives, so one movement ends
               the intro and begins the examples. Fading the two independently
               is what made the join feel like a cut between unrelated screens:
               nothing that left was connected to anything that arrived. */
            gsap.set(intro.current, {
              autoAlpha: 1 - introOut,
              x: 90 * opened,
            });

            /* The halves are built once and then moved. `xPercent: 100` on a
               half-width element is exactly the other half, and -100 is
               exactly off-screen — so the same property does the entrance and
               the swap without a second mechanism. */
            gsap.set(scene.current, {
              autoAlpha: 1,
              xPercent: -100 * (1 - opened) + 100 * swap,
            });
            gsap.set(words.current, {
              autoAlpha: wordsIn,
              xPercent: -100 * swap,
            });

            /* The two halves pass through each other, so at the midpoint they
               are both in the centre. The scene is opaque and sits above the
               words, which turns that collision into a wipe: the dark panel
               crosses the screen and the type is behind it while it does.

               The scenes crossfade — two images dissolving is fine, and the
               panel is never empty. The words do NOT crossfade. Two blocks of
               different text at 50% each is unreadable soup, and it was: the
               old copy and the new copy were legible on top of one another.
               They dip instead — the old one leaves before the new one
               arrives, and the gap between falls exactly where the scene is
               covering that half anyway. */
            const dissolve = ramp(p, 0.58, 0.78);
            gsap.set(scenes.current[0], { autoAlpha: 1 - dissolve });
            gsap.set(scenes.current[1], { autoAlpha: dissolve });

            gsap.set(blocks.current[0], { autoAlpha: 1 - ramp(p, 0.52, 0.62) });
            gsap.set(blocks.current[1], { autoAlpha: ramp(p, 0.76, 0.88) });

            setActive(p < 0.3 ? -1 : swap < 0.5 ? 0 : 1);
          },
        });
      }, root);

      return () => ctx.revert();
    });

    return () => mm.revert();
  }, []);

  return (
    <section
      ref={root}
      id="what"
      className="relative flex h-svh flex-col justify-center overflow-hidden"
    >
      {/* The line grid. Behind everything, masked so it fades out toward the
          edges rather than ending on a hard rectangle, and pointer-inert. */}
      <div aria-hidden className="line-grid pointer-events-none absolute inset-0" />

      {/* ------------------------------------------------------ the claim --
          The object on the left, the chain on the right. It is the first thing
          on the page that says what physically goes in and what comes out, so
          it is laid out as a sequence rather than as prose: glasses, read,
          invert, song. */}
      <div
        ref={intro}
        className="relative mx-auto grid w-full max-w-content items-center gap-rest px-gutter lg:grid-cols-[1fr_1fr]"
      >
        <div className="hidden lg:block">
          <GlassesModel />
          {/* Attribution rendered on the page, not just in a source comment.
              An attribution nobody can see is not an attribution. */}
          <p className="mt-3 text-center font-mono text-label uppercase text-graphite/60">
            Model by mminharali · Sketchfab
          </p>
        </div>

        <div>
          <h2 className="max-w-[18ch] font-display text-headline">
            {description.statement}
          </h2>

          {/* Four lines, each one big. The explanatory sentence under every
              step is gone and so are the rules between them: four titles, four
              paragraphs and four dividers made a specification sheet out of
              what should be a single readable idea. The step label carries the
              sequence, so the horizontal rules were saying it twice. */}
          <ol className="mt-rest space-y-5">
            {description.chain.map((link) => (
              <li key={link.step} className="flex items-baseline gap-5">
                <Label tone="offset" className="w-14 shrink-0">
                  {link.step}
                </Label>
                <p className="font-display text-[clamp(1.5rem,2.3vw,2.1rem)] font-semibold leading-tight tracking-[-0.03em]">
                  {link.title}
                </p>
              </li>
            ))}
          </ol>
        </div>
      </div>

      {/* ----------------------------------------------------- the examples --
          Half the screen each, edge to edge and floor to ceiling. The image
          was a 16:10 card sitting inside the content column, which made the
          scene look like an illustration of the example rather than the thing
          being reacted to. Full-bleed, it IS the room, and the verdict sits
          next to it at the same scale.

          Absolutely placed and stacked, because they occupy the same screen at
          different times. On mobile — no pin, no scrub — they fall back to
          stacked blocks in flow; see the `lg:` prefixes. */}
      {/* ------------------------------------------------------ the scene --
          Half the window, floor to ceiling, no rounding and no inset — it runs
          into the corners, which is the only way half a screen reads as a wall
          rather than as a large picture. It starts on the left and ends on the
          right; both examples live inside it and cross over as it travels. */}
      <div
        ref={scene}
        className="lg:absolute lg:inset-y-0 lg:left-0 lg:z-10 lg:w-1/2 lg:opacity-0"
      >
        {description.examples.map((example, i) => (
          <div
            key={example.id}
            ref={(el) => {
              scenes.current[i] = el;
            }}
            className="lg:absolute lg:inset-0"
          >
            <Slot shot={example.shot} className="h-[38vh] w-full lg:h-full" />
          </div>
        ))}
      </div>

      {/* ------------------------------------------------------ the words --
          The other half, moving the opposite way. It passes the scene rather
          than following it, which is what sells the two halves as one object
          rearranging instead of two slides changing. */}
      <div
        ref={words}
        className="lg:absolute lg:inset-y-0 lg:left-1/2 lg:w-1/2 lg:opacity-0"
      >
        {description.examples.map((example, i) => (
          <div
            key={example.id}
            ref={(el) => {
              blocks.current[i] = el;
            }}
            className="flex items-center px-gutter py-rest lg:absolute lg:inset-0 lg:px-rest lg:py-0"
          >
            <div>
              <Label tone="offset">{example.scene}</Label>
              <p className="mt-2 font-mono text-label lowercase tracking-normal text-graphite">
                {example.read}
              </p>

              {/* The verdict. Sized against HALF the window, not the whole
                  one: `text-display` clamps to 5.75rem because it was written
                  for a full-width hero, and in a half with the section
                  clipping overflow it ran "Bodies" off its own panel. 4.5vw
                  against a 50% column with `rest` padding either side leaves
                  room for the longest track name in the corpus. */}
              <p className="mt-block font-display text-[clamp(2.25rem,4.5vw,4rem)] font-semibold leading-[0.95] tracking-[-0.035em] [overflow-wrap:anywhere]">
                {example.track}
              </p>
              <p className="mt-3 text-subheading text-graphite">
                {example.artist}
              </p>

              <p className="mt-block max-w-measure text-body text-graphite">
                {example.why}
              </p>
            </div>
          </div>
        ))}
      </div>

      {/* Which of the two you are on. Two marks, so the section says how long
          it is rather than leaving you to find out by scrolling. */}
      {/* z-20: the scene panel rides at z-10 and was swallowing the left-hand
          dot as it crossed the centre. */}
      <div className="pointer-events-none absolute inset-x-0 bottom-8 z-20 hidden justify-center gap-2 lg:flex">
        {description.examples.map((example, i) => (
          <span
            key={example.id}
            className={`h-1 w-8 rounded-full transition-colors duration-interaction ease-calm ${
              active === i ? "bg-offset-ink" : "bg-hairline"
            }`}
          />
        ))}
      </div>
    </section>
  );
}
