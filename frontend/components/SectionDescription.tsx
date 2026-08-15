"use client";

import { useLayoutEffect, useRef, useState } from "react";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
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

/** Beats of scroll spent inside the section, one per example plus the intro. */
const BEATS = 2.4;

/** Ramp a value across a progress window, clamped at both ends. */
const ramp = (p: number, from: number, to: number) =>
  Math.min(1, Math.max(0, (p - from) / (to - from)));

export default function SectionDescription() {
  const root = useRef<HTMLElement>(null);
  const intro = useRef<HTMLDivElement>(null);
  const panels = useRef<(HTMLDivElement | null)[]>([]);
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

            // The statement holds, then clears out of the way entirely.
            gsap.set(intro.current, {
              autoAlpha: 1 - ramp(p, 0.16, 0.32),
              y: -28 * ramp(p, 0.16, 0.32),
            });

            // Each example floods in from its own side and leaves the way it
            // came. The park enters from the left, the library from the right.
            const windows = [
              { in: [0.24, 0.42], out: [0.56, 0.68], from: -1 },
              { in: [0.62, 0.8], out: [1.01, 1.02], from: 1 },
            ];

            windows.forEach((w, i) => {
              const entering = ramp(p, w.in[0], w.in[1]);
              const leaving = ramp(p, w.out[0], w.out[1]);
              const shown = entering - leaving;

              gsap.set(panels.current[i], {
                autoAlpha: shown,
                // Travels in from its edge, and keeps going the same way out,
                // so it never appears to reverse over its own path.
                xPercent: w.from * (12 * (1 - entering) + 12 * leaving),
              });
            });

            setActive(p < 0.3 ? -1 : p < 0.62 ? 0 : 1);
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
      className="relative flex h-svh flex-col justify-center overflow-hidden px-gutter"
    >
      {/* ------------------------------------------------------ the claim -- */}
      <div ref={intro} className="mx-auto w-full max-w-content">
        <h2 className="mx-auto max-w-statement text-center font-display text-headline">
          {description.statement}
        </h2>
        <p className="mx-auto mt-block max-w-measure-sub text-center text-body text-graphite">
          Never at random — random isn&rsquo;t funny. Here are two it actually
          made.
        </p>
      </div>

      {/* ----------------------------------------------------- the examples --
          Absolutely placed and stacked, because they occupy the same screen at
          different times. On mobile (no pin, no scrub) they fall back to being
          stacked in flow — see the `lg:` prefixes. */}
      {description.examples.map((example, i) => (
        <div
          key={example.id}
          ref={(el) => {
            panels.current[i] = el;
          }}
          className="mx-auto w-full max-w-content lg:absolute lg:inset-x-0 lg:px-gutter lg:opacity-0"
        >
          <div
            className={`grid items-center gap-rest lg:grid-cols-2 ${
              // The library sits image-right, so the two examples are mirror
              // images of each other rather than the same slide twice.
              i === 1 ? "lg:[&>*:first-child]:order-2" : ""
            }`}
          >
            <Slot shot={example.shot} className="aspect-[16/10] rounded-card" />

            <div>
              <Label tone="offset">{example.scene}</Label>
              <p className="mt-2 font-mono text-label lowercase tracking-normal text-graphite">
                {example.read}
              </p>

              {/* The verdict, at headline size. This is the punchline of the
                  beat and everything else on the panel is support for it. */}
              <p className="mt-block font-display text-headline leading-none">
                {example.track}
              </p>
              <p className="mt-2 text-body text-graphite">{example.artist}</p>

              <p className="mt-block max-w-measure text-caption text-graphite">
                {example.why}
              </p>
            </div>
          </div>
        </div>
      ))}

      {/* Which of the two you are on. Two marks, so the section says how long
          it is rather than leaving you to find out by scrolling. */}
      <div className="pointer-events-none absolute inset-x-0 bottom-8 hidden justify-center gap-2 lg:flex">
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
