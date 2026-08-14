"use client";

import { motion, useInView } from "motion/react";
import { useRef } from "react";

/**
 * Fade up, unblur, and settle as it enters view.
 *
 * Replaces the old Reveal, which only faded and rose. The blur is what makes
 * it read as considered rather than as "an animation happened" — the eye
 * registers something coming into focus, not something sliding.
 *
 * `once: true` on purpose. Re-animating on every scroll-past is the single
 * most common way a page starts feeling cheap.
 *
 * Respects prefers-reduced-motion: those visitors get the content immediately,
 * with no movement at all.
 */
export default function BlurFade({
  children,
  delay = 0,
  className = "",
  offset = 18,
  blur = "8px",
}: {
  children: React.ReactNode;
  /** Seconds. Stagger siblings by ~0.08 rather than animating them together. */
  delay?: number;
  className?: string;
  offset?: number;
  blur?: string;
}) {
  const ref = useRef<HTMLDivElement>(null);
  const inView = useInView(ref, { once: true, margin: "-60px" });

  return (
    <motion.div
      ref={ref}
      className={className}
      initial={{ opacity: 0, y: offset, filter: `blur(${blur})` }}
      animate={
        inView
          ? { opacity: 1, y: 0, filter: "blur(0px)" }
          : { opacity: 0, y: offset, filter: `blur(${blur})` }
      }
      transition={{
        // One curve for the whole site. Slightly long, so it reads as
        // deliberate rather than snappy.
        duration: 0.7,
        delay,
        ease: [0.21, 0.47, 0.32, 0.98],
      }}
    >
      {children}
    </motion.div>
  );
}
