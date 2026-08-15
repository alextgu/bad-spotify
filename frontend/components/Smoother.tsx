"use client";

import { useLayoutEffect, useRef } from "react";
import gsap from "gsap";
import { ScrollSmoother } from "gsap/ScrollSmoother";
import { ScrollTrigger } from "gsap/ScrollTrigger";

gsap.registerPlugin(ScrollTrigger, ScrollSmoother);

/**
 * Owns scrolling for the whole page, on desktop only.
 *
 * Two jobs:
 *
 *   1. **Inertia.** `smooth: 1.4` — slower than the mockup's 1.2. Smoothing is
 *      the difference between a page that responds to the wheel and one that
 *      settles after it, and settling is the entire brief. Past about 1.8 it
 *      stops reading as weight and starts reading as lag.
 *
 *   2. **Parallax on full-bleed media.** Anything marked `data-parallax` drifts
 *      ±4.5% against the scroll. The mockup used ±8%, which is enough to see
 *      the image sliding inside its frame; at this amplitude you only notice
 *      that the page has depth, which is the point at which it stops being an
 *      effect.
 *
 *   3. **Snapping to sections.** Scroll stops, and the page settles onto the
 *      nearest section edge.
 *
 * On snapping specifically — it is *proximity*, not mandatory, and that is a
 * deliberate choice rather than a compromise. Mandatory snap means a section
 * taller than the viewport becomes a trap: you scroll into the middle of it to
 * read, stop, and get yanked back to its top. Several sections here are taller
 * than a screen by design. So a snap only happens when the nearest edge is
 * already within `SNAP_RANGE` of where you stopped; anywhere else the page
 * leaves you exactly where you are.
 *
 * The snap itself is long (up to 0.9s on `power2.inOut`) and starts after a
 * beat. A fast snap feels like the page correcting you; a slow one feels like
 * it coming to rest.
 *
 * Off entirely below 1000px and under `prefers-reduced-motion`: smoothing on a
 * touch device fights the platform's own scrolling, and it is the first thing
 * to feel broken on a phone.
 */

/** How close to a section edge you have to stop before the page settles onto
 *  it, as a fraction of the viewport height. */
const SNAP_RANGE = 0.34;
export default function Smoother({ children }: { children: React.ReactNode }) {
  const wrapper = useRef<HTMLDivElement>(null);

  useLayoutEffect(() => {
    const mm = gsap.matchMedia();

    mm.add(
      "(min-width: 1000px) and (prefers-reduced-motion: no-preference)",
      () => {
        const smoother = ScrollSmoother.create({
          wrapper: "#smooth-wrapper",
          content: "#smooth-content",
          smooth: 1.4,
          effects: false,
          normalizeScroll: true,
        });

        gsap.utils.toArray<HTMLElement>("[data-parallax]").forEach((el) => {
          gsap.fromTo(
            el,
            { yPercent: -4.5 },
            {
              yPercent: 4.5,
              ease: "none",
              scrollTrigger: {
                trigger: el.parentElement ?? el,
                start: "top bottom",
                end: "bottom top",
                scrub: true,
              },
            },
          );
        });

        /* ------------------------------------------------------- snapping --
           Section edges, expressed as scroll progress. Recomputed on refresh
           because pinning changes the document height underneath us.

           Measured from layout rather than from `smoother.offset()`: that
           returns a position in the smoother's own coordinate space, which is
           not the same number as ScrollTrigger's progress once a pinned
           section has inserted a spacer. Mixing the two produced points that
           were confidently wrong — the page would settle onto a section other
           than the nearest one, which reads as the page overruling you. */
        /* Native scroll position. Everything below stays in this one
           coordinate space — during momentum the smoother's *visual* position
           (the transform on #smooth-content) and the native scroll differ by
           however much is still being eased out, so measuring one against the
           other is off by exactly the amount of smoothing in flight.

           `edges()` only runs at setup and on refresh, when the two agree, so
           the offsets it records are true document positions. */
        const scrollPos = () => smoother.scrollTop();

        const edges = () => {
          const max = ScrollTrigger.maxScroll(window);
          if (!max) return [0];
          const here = scrollPos();
          return gsap.utils
            .toArray<HTMLElement>("[data-snap]")
            .map((el) => (el.getBoundingClientRect().top + here) / max)
            .concat(0)
            .filter((p) => p >= 0 && p <= 1)
            .sort((a, b) => a - b);
        };

        /* ScrollTrigger's own `snap` is not used here. Under a smoother with a
           pinned section in the page it fired inconsistently — sometimes
           settling on an edge other than the nearest, sometimes not firing at
           all — and a snap that is unpredictable is worse than none, because
           the reader cannot tell whether the page moved or they did.

           This is the same behaviour written out plainly: wait until scrolling
           has actually stopped, find the nearest section edge, and go there if
           it is close. `smoother.scrollTo(y, true)` reuses the smoother's own
           easing, so the settle is the same motion as the scrolling it follows
           rather than a second, different animation bolted on. */
        let points = edges();
        let settleTimer: number;
        let settling = false;

        const refresh = () => {
          points = edges();
        };
        ScrollTrigger.addEventListener("refresh", refresh);

        const onScroll = () => {
          if (settling) return;
          window.clearTimeout(settleTimer);
          settleTimer = window.setTimeout(() => {
            const max = ScrollTrigger.maxScroll(window);
            if (!max || !points.length) return;

            const here = scrollPos();
            const nearest =
              points.reduce((best, p) =>
                Math.abs(p * max - here) < Math.abs(best * max - here) ? p : best,
              ) * max;

            const away = Math.abs(nearest - here);
            // Already there, or nowhere near an edge: leave it alone. The
            // second case is what stops a section taller than the viewport
            // from dragging you back out of itself while you read it.
            if (away < 2 || away > window.innerHeight * SNAP_RANGE) return;

            settling = true;
            smoother.scrollTo(nearest, true);
            window.setTimeout(() => {
              settling = false;
            }, 900);
          }, 150);
        };

        ScrollTrigger.addEventListener("scrollEnd", onScroll);
        window.addEventListener("scroll", onScroll, { passive: true });

        return () => {
          window.clearTimeout(settleTimer);
          ScrollTrigger.removeEventListener("refresh", refresh);
          ScrollTrigger.removeEventListener("scrollEnd", onScroll);
          window.removeEventListener("scroll", onScroll);
          smoother.kill();
        };
      },
    );

    return () => mm.revert();
  }, []);

  return (
    <div id="smooth-wrapper" ref={wrapper}>
      <div id="smooth-content">{children}</div>
    </div>
  );
}
