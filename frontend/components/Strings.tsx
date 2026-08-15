"use client";

import { useEffect, useRef } from "react";

/**
 * The background: seven strings across the viewport, which you can pluck.
 *
 * The page was plain paper, which is fine and says nothing. This says "music"
 * without another photograph, and it is the only thing here that answers to
 * the reader directly — everything else on the page happens whether they are
 * there or not.
 *
 * **At rest it is completely still**, and that is the whole discipline of it.
 * An ambient background that drifts on its own is a screensaver: it competes
 * with the type, it never stops, and after ten seconds it is noise. These
 * lines do nothing at all until the cursor crosses one, and go back to nothing
 * about a second and a half later. The motion is *caused*, so it reads as
 * response rather than decoration.
 *
 * ---------------------------------------------------------------------------
 * The physics, such as it is
 * ---------------------------------------------------------------------------
 * A plucked string vibrates in its fundamental mode: fixed at both ends,
 * maximum displacement in the middle. So the shape is a half sine over the
 * width, `sin(pi * x / w)`, scaled by an amplitude that oscillates and decays:
 *
 *     y(x, t) = y0 + A · sin(pi·x/w) · cos(omega·t) · e^(-t/tau)
 *
 * Amplitude comes from how fast the cursor crossed, and its sign from which
 * way — so flicking upward through a string throws it upward. Each string has
 * its own `omega`, low strings slower, which is what stops seven simultaneous
 * plucks from looking like one thick vibrating band.
 *
 * It is not a physical simulation and does not need to be. The only thing that
 * has to be true is that a fast crossing moves it more than a slow one.
 *
 * ---------------------------------------------------------------------------
 * Cost
 * ---------------------------------------------------------------------------
 * The rAF loop **stops** when every string is below the visible threshold, and
 * restarts on the next pluck. An untouched page runs no animation frames at
 * all, which matters on a laptop driving a projector.
 *
 * `pointer-events: none` throughout — this must never eat a click meant for a
 * link. It listens on the window instead.
 */

/** Seven, not six: six reads as an explicit guitar, which is more literal than
 *  this wants to be. Seven reads as strings. */
const COUNT = 7;

/** Peak displacement from one crossing, px. Past ~24 the lines start colliding
 *  with each other and it reads as a mess rather than as an instrument. */
const MAX_AMPLITUDE = 22;

/** Seconds for a pluck to fall to silence. */
const DECAY = 1.4;

/** Below this many px of displacement, a string counts as at rest. */
const SILENT = 0.06;

interface StringLine {
  /** Resting y, as a fraction of viewport height. */
  base: number;
  /** Angular frequency. Lower index = lower and slower. */
  omega: number;
  /** Current peak displacement in px, signed. */
  amplitude: number;
  /** Seconds since this string was last plucked. */
  age: number;
}

export default function Strings() {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    const lines: StringLine[] = Array.from({ length: COUNT }, (_, i) => ({
      base: (i + 1) / (COUNT + 1),
      // 8.5 to 17 rad/s, low to high. Deliberately not harmonic ratios: real
      // ratios make simultaneous plucks re-align into a visible pulse.
      omega: 8.5 + (i / (COUNT - 1)) * 8.5 + (i % 2) * 0.7,
      amplitude: 0,
      age: 0,
    }));

    let width = 0;
    let height = 0;

    const resize = () => {
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      width = window.innerWidth;
      height = window.innerHeight;
      canvas.width = Math.floor(width * dpr);
      canvas.height = Math.floor(height * dpr);
      canvas.style.width = `${width}px`;
      canvas.style.height = `${height}px`;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      draw();
    };

    const draw = () => {
      ctx.clearRect(0, 0, width, height);

      for (const line of lines) {
        const y0 = line.base * height;
        const displacement =
          line.amplitude *
          Math.cos(line.omega * line.age) *
          Math.exp(-line.age / DECAY);

        const loud = Math.min(Math.abs(displacement) / MAX_AMPLITUDE, 1);

        // At rest the strings are barely there — one step above the hairline
        // the page already uses. Ringing, they take on the accent, so a
        // plucked string is briefly the greenest thing on screen.
        ctx.strokeStyle = loud
          ? `rgba(${Math.round(26 + (28 - 26) * loud)}, ${Math.round(
              25 + (168 - 25) * loud,
            )}, ${Math.round(23 + (92 - 23) * loud)}, ${0.1 + loud * 0.5})`
          : "rgba(26, 25, 23, 0.1)";
        ctx.lineWidth = 1 + loud * 0.6;

        ctx.beginPath();
        if (Math.abs(displacement) < SILENT) {
          // Flat: two points, no sampling.
          ctx.moveTo(0, y0);
          ctx.lineTo(width, y0);
        } else {
          const step = 12;
          for (let x = 0; x <= width; x += step) {
            const y = y0 + displacement * Math.sin((Math.PI * x) / width);
            if (x === 0) ctx.moveTo(x, y);
            else ctx.lineTo(x, y);
          }
          ctx.lineTo(width, y0);
        }
        ctx.stroke();
      }
    };

    /* ------------------------------------------------------------- the loop --
       Runs only while something is moving. `running` is the gate; the last
       frame before stopping draws every string flat. */
    let running = false;
    let frame = 0;
    let last = 0;

    const tick = (now: number) => {
      const dt = Math.min((now - last) / 1000, 0.05);
      last = now;

      let alive = false;
      for (const line of lines) {
        if (Math.abs(line.amplitude) < SILENT) {
          line.amplitude = 0;
          continue;
        }
        line.age += dt;
        if (Math.abs(line.amplitude) * Math.exp(-line.age / DECAY) < SILENT) {
          line.amplitude = 0;
          line.age = 0;
        } else {
          alive = true;
        }
      }

      draw();

      if (alive) {
        frame = requestAnimationFrame(tick);
      } else {
        running = false;
        draw(); // settle flat
      }
    };

    const start = () => {
      if (running) return;
      running = true;
      last = performance.now();
      frame = requestAnimationFrame(tick);
    };

    /* ----------------------------------------------------------- the pluck --
       A string is plucked when the cursor crosses it: previous position on one
       side, current position on the other. Speed sets how hard, direction sets
       which way. */
    let prevY: number | null = null;
    let prevTime = 0;

    const onMove = (event: MouseEvent) => {
      const now = performance.now();
      const y = event.clientY;

      if (prevY === null) {
        prevY = y;
        prevTime = now;
        return;
      }

      const dt = Math.max((now - prevTime) / 1000, 0.001);
      const speed = Math.abs(y - prevY) / dt; // px per second
      const direction = Math.sign(y - prevY) || 1;

      for (const line of lines) {
        const lineY = line.base * height;
        const crossed = (prevY - lineY) * (y - lineY) <= 0 && prevY !== y;
        if (!crossed) continue;

        // Slow drags barely disturb it; a flick throws it. Capped so that
        // dragging wildly can't stack the strings into each other.
        const strength = Math.min(2 + speed * 0.012, MAX_AMPLITUDE);
        line.amplitude = direction * strength;
        line.age = 0;
      }

      prevY = y;
      prevTime = now;
      start();
    };

    resize();
    window.addEventListener("resize", resize);

    if (!reduced) {
      window.addEventListener("mousemove", onMove, { passive: true });
    }

    return () => {
      cancelAnimationFrame(frame);
      window.removeEventListener("resize", resize);
      window.removeEventListener("mousemove", onMove);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      aria-hidden
      className="pointer-events-none fixed inset-0 -z-10"
    />
  );
}
