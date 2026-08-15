"use client";

import { useEffect, useRef } from "react";

/**
 * Four quiet strings moving behind the foot of the page.
 *
 * They are intentionally atmospheric rather than playable. Each line is a
 * layered set of long travelling waves whose speed and phase wander slowly,
 * so the composition keeps changing without settling into a visible loop.
 * The pointer adds a very broad, shallow pressure field: nearby lines shift by
 * only a few pixels and ease back into their own motion. There is no click,
 * pluck, or state for the visitor to operate.
 *
 * The wide translucent under-stroke gives every string depth without turning
 * it into a glow effect. A sharper core keeps the shape legible on the paper
 * background. The green line is the brand accent; the other three stay close
 * to ink, warm graphite, and a deep blue so the group reads as one object.
 *
 * Any direct child of `main` marked `data-strings="off"` fades the canvas out
 * while it holds the middle of the viewport. Reduced-motion visitors receive
 * the same composition as a still image, with no pointer response.
 */

const COUNT = 4;

/** A low band: present at the foot of a screen, absent from the reading area. */
const BAND = 0.42;

const SAMPLE_STEP = 5;
const POINTER_RADIUS_X = 760;
const POINTER_RADIUS_Y = 150;
const POINTER_PUSH = 4;

const COLOURS = [
  { r: 22, g: 21, b: 19, a: 0.14 },
  { r: 116, g: 101, b: 82, a: 0.17 },
  { r: 24, g: 148, b: 80, a: 0.23 },
  { r: 34, g: 58, b: 92, a: 0.16 },
] as const;

interface Wave {
  /** Wavelength as a fraction of the viewport width. */
  length: number;
  amp: number;
  speed: number;
  phase: number;
  /** A second, slower oscillation that prevents a mechanically even march. */
  meander: number;
  meanderSpeed: number;
  meanderPhase: number;
}

interface StringLine {
  base: number;
  waves: Wave[];
  breathSpeed: number;
  breathPhase: number;
  roam: number;
  roamSpeed: number;
  roamPhase: number;
  width: number;
  colour: (typeof COLOURS)[number];
}

interface PointerField {
  x: number;
  y: number;
  targetX: number;
  targetY: number;
  strength: number;
  targetStrength: number;
}

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
      // Deliberately irregular spacing keeps the group from looking ruled.
      base: [0.2, 0.43, 0.67, 0.88][i] + between(-0.018, 0.018),
      waves: [
        {
          length: between(1.35, 2.05),
          amp: between(14, 23),
          speed: between(0.11, 0.19),
          phase: between(0, Math.PI * 2),
          meander: between(0.35, 0.7),
          meanderSpeed: between(0.035, 0.065),
          meanderPhase: between(0, Math.PI * 2),
        },
        {
          length: between(0.74, 1.18),
          amp: between(7, 13),
          speed: between(-0.28, -0.16),
          phase: between(0, Math.PI * 2),
          meander: between(0.22, 0.52),
          meanderSpeed: between(0.055, 0.095),
          meanderPhase: between(0, Math.PI * 2),
        },
        {
          length: between(0.42, 0.68),
          amp: between(2, 5),
          speed: between(0.24, 0.39),
          phase: between(0, Math.PI * 2),
          meander: between(0.12, 0.3),
          meanderSpeed: between(0.08, 0.14),
          meanderPhase: between(0, Math.PI * 2),
        },
      ],
      breathSpeed: between(0.045, 0.085),
      breathPhase: between(0, Math.PI * 2),
      roam: between(5, 11),
      roamSpeed: between(0.035, 0.075),
      roamPhase: between(0, Math.PI * 2),
      width: [1.15, 1.05, 1.5, 1.1][i],
      colour: COLOURS[i],
    }));

    const pointer: PointerField = {
      x: window.innerWidth / 2,
      y: 0,
      targetX: window.innerWidth / 2,
      targetY: 0,
      strength: 0,
      targetStrength: 0,
    };

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
      ctx.lineCap = "round";
      ctx.lineJoin = "round";
    };

    const draw = (t: number) => {
      ctx.clearRect(0, 0, width, height);

      for (const line of lines) {
        const breath = 0.82 + 0.24 * Math.sin(t * line.breathSpeed + line.breathPhase);
        const y0 =
          line.base * height +
          line.roam * Math.sin(t * line.roamSpeed + line.roamPhase) +
          line.roam * 0.28 * Math.sin(t * line.roamSpeed * 1.73 + line.roamPhase * 0.7);

        ctx.beginPath();

        for (let x = -SAMPLE_STEP; x <= width + SAMPLE_STEP; x += SAMPLE_STEP) {
          let y = y0;

          for (const wave of line.waves) {
            const wanderingPhase =
              Math.sin(t * wave.meanderSpeed + wave.meanderPhase) * wave.meander;
            y +=
              wave.amp *
              breath *
              Math.sin(
                (Math.PI * 2 * x) / (wave.length * width) +
                  wave.phase +
                  t * wave.speed +
                  wanderingPhase,
              );
          }

          // The field is intentionally much broader than the visible response.
          // It nudges a long section of string together instead of making the
          // sharp local bend that a pluck or direct cursor tracker produces.
          if (pointer.strength > 0.001) {
            const dx = (x - pointer.x) / POINTER_RADIUS_X;
            const dy = y - pointer.y;
            const vertical = Math.max(0, 1 - Math.abs(dy) / POINTER_RADIUS_Y);
            const horizontal = Math.exp(-dx * dx * 0.65);
            const direction = Math.sign(dy) || (line.base < 0.5 ? -1 : 1);
            y +=
              direction *
              POINTER_PUSH *
              horizontal *
              vertical *
              vertical *
              pointer.strength;
          }

          if (x === -SAMPLE_STEP) ctx.moveTo(x, y);
          else ctx.lineTo(x, y);
        }

        const colour = line.colour;

        // A restrained translucent bed gives the line physical depth.
        ctx.strokeStyle = `rgba(${colour.r}, ${colour.g}, ${colour.b}, ${colour.a * 0.12})`;
        ctx.lineWidth = line.width + 4;
        ctx.stroke();

        // The precise core prevents the large motion from feeling blurry.
        ctx.strokeStyle = `rgba(${colour.r}, ${colour.g}, ${colour.b}, ${colour.a})`;
        ctx.lineWidth = line.width;
        ctx.stroke();
      }
    };

    let frame = 0;
    let start = 0;
    let previous = 0;

    const tick = (now: number) => {
      if (!start) start = now;
      if (!previous) previous = now;
      const t = (now - start) / 1000;
      const dt = Math.min((now - previous) / 1000, 0.05);
      previous = now;

      // Easing the field is what makes entering and leaving it feel like
      // pressure in material instead of direct cursor tracking.
      const positionEase = 1 - Math.exp(-dt * 5.5);
      const strengthEase = 1 - Math.exp(-dt * 3.4);
      pointer.x += (pointer.targetX - pointer.x) * positionEase;
      pointer.y += (pointer.targetY - pointer.y) * positionEase;
      pointer.strength += (pointer.targetStrength - pointer.strength) * strengthEase;

      draw(t);
      frame = requestAnimationFrame(tick);
    };

    const onPointerMove = (event: PointerEvent) => {
      const bandTop = window.innerHeight - height;
      const y = event.clientY - bandTop;
      pointer.targetX = event.clientX;
      pointer.targetY = y;
      pointer.targetStrength = y >= -POINTER_RADIUS_Y && y <= height + POINTER_RADIUS_Y ? 1 : 0;
    };

    const releasePointer = () => {
      pointer.targetStrength = 0;
    };

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

    document.querySelectorAll("main > *").forEach((block) => observer.observe(block));

    resize();
    window.addEventListener("resize", resize);

    if (reduced) {
      draw(0);
    } else {
      window.addEventListener("pointermove", onPointerMove, { passive: true });
      window.addEventListener("blur", releasePointer);
      document.documentElement.addEventListener("mouseleave", releasePointer);
      frame = requestAnimationFrame(tick);
    }

    return () => {
      cancelAnimationFrame(frame);
      observer.disconnect();
      window.removeEventListener("resize", resize);
      window.removeEventListener("pointermove", onPointerMove);
      window.removeEventListener("blur", releasePointer);
      document.documentElement.removeEventListener("mouseleave", releasePointer);
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
