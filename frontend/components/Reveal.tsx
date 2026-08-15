"use client";

import { useEffect, useRef } from "react";

/**
 * The entire entrance vocabulary of this page: fade, and rise a little.
 *
 * What it is NOT, and why:
 *
 *   - **No masked line reveal.** Splitting a headline into lines and sliding
 *     them out from behind a mask is the most recognisable motion of the last
 *     two years of launch pages. It also delays the sentence — you cannot read
 *     the thing until the animation has finished with it.
 *   - **No `expo` easing.** Expo leaves at enormous speed and stops dead. It
 *     reads as urgent, which is the opposite of the brief. The curve here
 *     leaves gently and spends most of its duration arriving.
 *   - **Small distance, long duration.** 14px over 1.6s. The previous pass
 *     moved 30–80px in under a second, which the eye reads as *travel*. This
 *     is closer to something coming into presence.
 *
 * `once` is not optional: re-animating on every scroll-past is the fastest way
 * to make a calm page feel busy.
 */
export default function Reveal({
  children,
  delay = 0,
  as: Tag = "div",
  className = "",
}: {
  children: React.ReactNode;
  /** Seconds. Stagger siblings by ~0.12 — wide enough to read as a sequence. */
  delay?: number;
  as?: "div" | "section" | "li" | "article";
  className?: string;
}) {
  const ref = useRef<HTMLElement>(null);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;

    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      el.style.opacity = "1";
      el.style.transform = "none";
      return;
    }

    const io = new IntersectionObserver(
      ([entry]) => {
        if (!entry.isIntersecting) return;
        el.style.transitionDelay = `${delay}s`;
        el.style.opacity = "1";
        el.style.transform = "translateY(0)";
        io.disconnect();
      },
      // Fires a little before the element is fully on screen, so the reveal
      // has finished by the time it is in comfortable reading position and
      // nobody is ever waiting on it.
      { rootMargin: "0px 0px -12% 0px", threshold: 0.01 },
    );

    io.observe(el);
    return () => io.disconnect();
  }, [delay]);

  return (
    <Tag
      ref={ref as React.Ref<never>}
      className={`translate-y-[14px] opacity-0 transition-[opacity,transform] duration-reveal ease-calm motion-reduce:translate-y-0 motion-reduce:opacity-100 ${className}`}
    >
      {children}
    </Tag>
  );
}
