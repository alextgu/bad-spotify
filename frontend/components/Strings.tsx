"use client";

import { useEffect, useRef } from "react";

/**
 * Four strings along the bottom of the window, drifting, pluckable.
 *
 * The first version put seven of them across the whole viewport and held them
 * perfectly straight until touched. Two things were wrong with that: lines
 * through the middle of the screen are lines through the middle of the
 * reading, and a background that is motionless until poked doesn't read as
 * alive, it reads as broken. This one lives in a band at the foot of the
 * window and is always moving slightly, the way a string that has just been
 * put down is.
 *
 * ---------------------------------------------------------------------------
 * The drift
 * ---------------------------------------------------------------------------
 * Each string is the sum of three travelling waves with different wavelengths
 * and speeds, times a slow breath that swells and settles the whole line.
 * Nothing in that stack shares a period with anything else, so the pattern
 * never visibly repeats — which is the only thing that makes ambient motion
 * bearable for longer than about ten seconds. Every constant is jittered per
 * string at mount, so no two runs of the page are quite the same and the four
 * lines never drift into agreement with each other.
 *
 * Amplitudes are small on purpose: 3-5px of travel. Enough that you can see it
 * is not a ruled line, not so much that it becomes something happening.
 *
 * ---------------------------------------------------------------------------
 * The pluck
 * ---------------------------------------------------------------------------
 * Crossing a string with the cursor adds the fundamental mode of a real
 * plucked string on top of the drift — fixed at both ends, maximum
 * displacement in the middle, decaying over about a second and a half:
 *
 *     sin(pi·x/w) · cos(omega·t) · e^(-t/tau)
 *
 * Amplitude from the speed of the crossing, sign from its direction, so an
 * upward flick throws the string upward.
 *
 * ---------------------------------------------------------------------------
 * Where it disappears
 * ---------------------------------------------------------------------------
 * Any section marked `data-strings="off"` fades the whole band out while it
 * holds the viewport. Used on the two screens that are purely reading — the
 * statement, which is one sentence alone on purpose, and the FAQ. A moving
 * line under a paragraph is a moving line under a paragraph.
 *
 * Sections with their own background — the dark ones and the day — cover the
 * band without needing the attribute.
 */

/** Four strings, low to high. */
const COUNT = 4;

/** The band's height as a fraction of the window. Only this is ever drawn. */
const BAND = 0.34;

/** Peak displacement from one crossing, px. */
const MAX_PLUCK = 20;

/** Seconds for a pluck to fall to silence. */
const DECAY = 1.5;

/**
 * One per string, faintly different. Not a gradient and not a rainbow — four
 * colours that could all plausibly be "a light line", pulled a few degrees
 * apart so the band has depth instead of looking like one object drawn four
 * times. Green sits third, where it is noticed without leading.
 */
const COLOURS = [
  { r: 26, g: 25, b: 23, a: 0.1 }, // ink
  { r: 121, g: 115, b: 106, a: 0.14 }, // graphite, warm
  { r: 28, g: 168, b: 92, a: 0.17 }, // the accent
  { r: 46, g: 74, b: 110, a: 0.12 }, // phase blue
];

interface Wave {
  /** Wavelength, as a multiple of the band width. */
  length: number;
  /** Peak contribution, px. */
  amp: number;
  /** Travel speed, rad/s. Slow — everything here is under half a radian. */
  speed: number;
  /** Starting offset, so the strings never begin aligned. */
  phase: number;
}

interface StringLine {
  /** Resting y within the band, 0 at the top of it. */
  base: number;
  waves: Wave[];
  /** Period and offset of the slow swell over the whole line. */
  breathSpeed: number;
  breathPhase: number;
  /** Fundamental frequency when plucked. */
  omega: number;
  /** Current pluck displacement, signed px. */
  pluck: number;
  /** Seconds since plucked. */
  age: number;
  colour: (typeof COLOURS)[number];
}

/** Random in [min, max). Called once per string at mount, never per frame. */
const between = (min: number, max: number) => min + Math.random() * (max - min);

export default function Strings() {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    const lines: StringLine[] = Array.from({ length: COUNT }, (_, i) => ({
      // Spread through the band, each nudged so they are not evenly ruled.
      base: (i + 0.7) / (COUNT + 0.4) + between(-0.035, 0.035),
      // Wavelengths under one screen-width, so each line actually bends
      // several times across the window rather than bowing once. The first
      // pass used 1.5-2.1 widths at 2-4px, which is a straight line with a
      // slight lean on it — technically curved, not visibly so.
      waves: [
        { length: between(1.0, 1.5), amp: between(7, 11), speed: between(0.15, 0.24), phase: between(0, Math.PI * 2) },
        { length: between(0.5, 0.8), amp: between(3.5, 6), speed: between(0.28, 0.44), phase: between(0, Math.PI * 2) },
        { length: between(0.26, 0.42), amp: between(1.5, 3), speed: between(0.46, 0.72), phase: between(0, Math.PI * 2) },
      ],
      breathSpeed: between(0.07, 0.14),
      breathPhase: between(0, Math.PI * 2),
      omega: 9 + i * 2.3 + between(-0.6, 0.6),
      pluck: 0,
      age: 0,
      colour: COLOURS[i % COLOURS.length],
    }));

    let width = 0;
    let height = 0;

    const resize = () => {
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      width = window.innerWidth;
      height = Math.round(window.innerHeight * BAND);
      canvas.width = Math.floor(width * dpr);
      canvas.height = Math.floor(height * dpr);
      canvas.style.width = `${width}px`;
      canvas.style.height = `${height}px`;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    };

    const draw = (t: number) => {
      ctx.clearRect(0, 0, width, height);

      for (const line of lines) {
        const y0 = line.base * height;

        // The swell: the whole line grows and settles on its own slow period.
        const breath = 0.72 + 0.42 * Math.sin(t * line.breathSpeed + line.breathPhase);

        const pluckNow = line.pluck
          ? line.pluck * Math.cos(line.omega * line.age) * Math.exp(-line.age / DECAY)
          : 0;

        const loud = Math.min(Math.abs(pluckNow) / MAX_PLUCK, 1);
        const c = line.colour;

        // Ringing, a string pulls toward the accent green and brightens.
        ctx.strokeStyle = `rgba(${Math.round(c.r + (28 - c.r) * loud)}, ${Math.round(
          c.g + (168 - c.g) * loud,
        )}, ${Math.round(c.b + (92 - c.b) * loud)}, ${c.a + loud * 0.45})`;
        ctx.lineWidth = 1 + loud * 0.7;

        ctx.beginPath();
        // Finer sampling than before: at 10px the shortest wave was being
        // drawn with about four points per period and came out as a
        // zigzag rather than a curve.
        const step = 6;
        for (let x = 0; x <= width; x += step) {
          let y = y0;

          for (const w of line.waves) {
            y += w.amp * breath * Math.sin((Math.PI * 2 * x) / (w.length * width) + w.phase + t * w.speed);
          }

          // The pluck is pinned at both ends, so it fades out toward the edges
          // while the drift keeps running underneath it.
          y += pluckNow * Math.sin((Math.PI * x) / width);

          if (x === 0) ctx.moveTo(x, y);
          else ctx.lineTo(x, y);
        }
        ctx.stroke();
      }
    };

    /* ---------------------------------------------------------------- loop --
       Runs continuously now, because the drift never stops. It is four
       polylines over a third of the window; the earlier stop-when-idle
       machinery bought nothing once there was no idle state to detect. */
    let frame = 0;
    let start = 0;

    const tick = (now: number) => {
      if (!start) start = now;
      const t = (now - start) / 1000;

      for (const line of lines) {
        if (!line.pluck) continue;
        line.age += 1 / 60;
        if (Math.abs(line.pluck) * Math.exp(-line.age / DECAY) < 0.05) {
          line.pluck = 0;
          line.age = 0;
        }
      }

      draw(t);
      frame = requestAnimationFrame(tick);
    };

    /* --------------------------------------------------------------- pluck --
       A crossing is the cursor being on one side of a string and then the
       other. Only the band's own vertical range is considered. */
    let prevY: number | null = null;
    let prevTime = 0;

    const onMove = (event: MouseEvent) => {
      const now = performance.now();
      const bandTop = window.innerHeight - height;
      const y = event.clientY - bandTop;

      if (prevY === null) {
        prevY = y;
        prevTime = now;
        return;
      }

      const dt = Math.max((now - prevTime) / 1000, 0.001);
      const speed = Math.abs(y - prevY) / dt;
      const direction = Math.sign(y - prevY) || 1;

      for (const line of lines) {
        const lineY = line.base * height;
        if ((prevY - lineY) * (y - lineY) > 0 || prevY === y) continue;
        line.pluck = direction * Math.min(2 + speed * 0.012, MAX_PLUCK);
        line.age = 0;
      }

      prevY = y;
      prevTime = now;
    };

    /* ------------------------------------------------------------- fade out --
       Whichever block holds the middle of the viewport decides whether the
       band is shown. */
    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (!entry.isIntersecting) continue;
          const off = (entry.target as HTMLElement).dataset.strings === "off";
          canvas.style.opacity = off ? "0" : "1";
        }
      },
      { rootMargin: "-45% 0px -45% 0px", threshold: 0 },
    );

    document
      .querySelectorAll("main > *")
      .forEach((block) => observer.observe(block));

    resize();
    window.addEventListener("resize", resize);

    if (!reduced) {
      window.addEventListener("mousemove", onMove, { passive: true });
      frame = requestAnimationFrame(tick);
    } else {
      draw(0);
    }

    return () => {
      cancelAnimationFrame(frame);
      observer.disconnect();
      window.removeEventListener("resize", resize);
      window.removeEventListener("mousemove", onMove);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      aria-hidden
      className="pointer-events-none fixed bottom-0 left-0 right-0 -z-10 transition-opacity duration-slow ease-calm"
    />
  );
}
