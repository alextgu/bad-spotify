"use client";

import { useEffect, useRef } from "react";

/**
 * The product, rotating — and draggable.
 *
 * Built out of divs and CSS 3D transforms rather than a WebGL model. That is a
 * decision, not a shortcut: a downloaded Meta Ray-Ban model is someone else's
 * trademarked product design with an unverifiable licence, it is a megabyte of
 * external asset that can fail on a projector, and the first rule in this repo
 * is that nothing may fail live. This is a few hundred bytes, it is ours, it
 * stays sharp at any resolution, and it cannot 404.
 *
 * ---------------------------------------------------------------------------
 * Why the spin moved out of CSS
 * ---------------------------------------------------------------------------
 * It used to be a `rig-spin` keyframe. A keyframe cannot be nudged: it owns
 * `transform` outright and overwrites anything a pointer sets, every frame. So
 * rotation is one number in JS now, and both inputs add to it — the idle drift
 * and the drag. Grab it and it follows your hand; let go and it carries the
 * speed you left it with, then settles back to drifting.
 *
 * The camera dot keeps its CSS pulse, because nothing competes for that.
 */

/** Degrees per second when nobody is touching it. */
const DRIFT = 20;

/** Degrees of rotation per pixel dragged. */
const SENSITIVITY = 0.45;

/** How quickly a throw decays back to the idle drift. Per second. */
const FRICTION = 2.6;

export default function GlassesRig({ className = "" }: { className?: string }) {
  const rig = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = rig.current;
    if (!el) return;

    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    let angle = -24;
    let velocity = 0;
    let dragging = false;
    let lastX = 0;
    let last = performance.now();
    let frame = 0;

    const draw = () => {
      el.style.transform = `rotateX(-8deg) rotateY(${angle}deg)`;
    };

    const tick = (now: number) => {
      const dt = Math.min((now - last) / 1000, 0.05);
      last = now;

      if (!dragging) {
        if (Math.abs(velocity) > 0.5) {
          // Carry the throw, bleeding off toward the idle speed rather than
          // toward zero — otherwise it stalls and then jerks back into drift.
          angle += velocity * dt;
          velocity += (reduced ? 0 : DRIFT - velocity) * Math.min(FRICTION * dt, 1);
        } else if (!reduced) {
          angle += DRIFT * dt;
        }
      }

      draw();
      frame = requestAnimationFrame(tick);
    };

    const onDown = (event: PointerEvent) => {
      dragging = true;
      lastX = event.clientX;
      velocity = 0;
      el.setPointerCapture(event.pointerId);
    };

    const onMove = (event: PointerEvent) => {
      if (!dragging) return;
      const dx = event.clientX - lastX;
      lastX = event.clientX;
      angle += dx * SENSITIVITY;
      // Remember the speed of the gesture so releasing it throws.
      velocity = dx * SENSITIVITY * 60;
      draw();
    };

    const onUp = (event: PointerEvent) => {
      if (!dragging) return;
      dragging = false;
      el.releasePointerCapture?.(event.pointerId);
    };

    draw();
    frame = requestAnimationFrame(tick);

    el.addEventListener("pointerdown", onDown);
    el.addEventListener("pointermove", onMove);
    el.addEventListener("pointerup", onUp);
    el.addEventListener("pointercancel", onUp);

    return () => {
      cancelAnimationFrame(frame);
      el.removeEventListener("pointerdown", onDown);
      el.removeEventListener("pointermove", onMove);
      el.removeEventListener("pointerup", onUp);
      el.removeEventListener("pointercancel", onUp);
    };
  }, []);

  return (
    <div
      className={`rig-scene ${className}`}
      role="img"
      aria-label="A pair of camera glasses, slowly rotating. Drag to turn them."
    >
      {/* `touch-none` so dragging it on a trackpad or touchscreen turns the
          glasses instead of scrolling the page out from under the gesture. */}
      <div
        ref={rig}
        className="rig cursor-grab touch-none select-none active:cursor-grabbing"
      >
        <div className="rig-front">
          <div className="rig-lens">
            <span className="rig-camera" />
            <span className="rig-camera-pulse" />
          </div>
          <div className="rig-bridge" />
          <div className="rig-lens" />
        </div>

        <div className="rig-temple rig-temple-left" />
        <div className="rig-temple rig-temple-right" />
      </div>
    </div>
  );
}
