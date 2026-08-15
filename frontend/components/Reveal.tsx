"use client";

import { useEffect, useRef } from "react";

/**
 * The entire entrance vocabulary of this page: fade, and rise a little.
 *
 * What it is NOT, and why:
 *
 *   - **No masked line reveal.** Splitting a headline into lines and sliding
 *     them out from behind a mask is the most recognisable motion of the last
 *     two years of launch pages, and it delays the sentence — you cannot read
 *     the thing until the animation has finished with it.
 *   - **No `expo` easing.** Expo leaves at enormous speed and stops dead. The
 *     curve here leaves gently and spends most of its duration arriving.
 *   - **Small distance, long duration.** 14px over 1.6s. Closer to something
 *     coming into presence than to something travelling.
 *
 * **It re-animates on every arrival**, which is a reversal of how this started.
 * When the page scrolled freely, re-animating on each scroll-past was the
 * fastest way to make it feel busy — you would trip the same animation three
 * times fighting your own trackpad. The page is discrete now: you don't pass a
 * screen, you arrive at it, deliberately, one gesture at a time. Composing
 * itself as you land is then the right behaviour, and going back to a screen
 * you have seen shows it composing again rather than sitting there already
 * finished.
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

    const show = () => {
      el.style.transitionDelay = `${delay}s`;
      el.style.opacity = "1";
      el.style.transform = "translateY(0)";
    };

    const hide = () => {
      // No delay on the way out: staggering a disappearance is fussy, and
      // nobody is watching a screen they have already left.
      el.style.transitionDelay = "0s";
      el.style.opacity = "0";
      el.style.transform = "translateY(14px)";
    };

    const io = new IntersectionObserver(
      ([entry]) => (entry.isIntersecting ? show() : hide()),
      // Fires a little before the element is fully on screen, so the reveal
      // has finished by the time it is in comfortable reading position.
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
