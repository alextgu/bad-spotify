"use client";

import { useLayoutEffect } from "react";
import gsap from "gsap";
import { ScrollToPlugin } from "gsap/ScrollToPlugin";
import { ScrollTrigger } from "gsap/ScrollTrigger";

gsap.registerPlugin(ScrollTrigger, ScrollToPlugin);

/**
 * Scrolling is discrete: one gesture moves to the next stop.
 *
 * This replaced a smoother plus a proximity snap, which behaved differently in
 * a way that mattered — there, a gesture scrolled you somewhere arbitrary and
 * then the page *corrected* you onto an edge afterwards. Two movements for one
 * input, the second one unrequested. Here the gesture is the whole movement:
 * you ask for the next stop, you go to the next stop, nothing happens after.
 *
 * ScrollSmoother is gone with it. Its entire job was making free scrolling feel
 * weighted, and there is no free scrolling left to weight — every position the
 * page can be in is now one we chose. That also removes a real class of bug:
 * the smoother's transform position and the native scroll position disagree
 * during momentum, and anything measuring one against the other is wrong by
 * however much easing is still in flight.
 *
 * ---------------------------------------------------------------------------
 * STOPS ARE NOT SECTIONS
 * ---------------------------------------------------------------------------
 * A stop is a screenful, not a section. Several sections are taller than the
 * viewport, and the pinned day section is *much* taller — it converts about
 * three screens of scrolling into horizontal travel across six cards. If one
 * gesture jumped a whole section, those would be skipped entirely: you would
 * arrive past the day having seen none of it.
 *
 * So each block contributes a stop at its top, then another every viewport
 * height until it runs out. Short sections get exactly one stop and behave the
 * way you would expect; tall ones step through. Inside the pinned section the
 * steps drive the horizontal track, so it reads as advancing through the day a
 * screen at a time rather than as scrolling past a pinned thing.
 *
 * Disabled below 1000px and under `prefers-reduced-motion`. Taking over the
 * wheel is a strong thing to do to a reader; doing it to a touchscreen, where
 * it fights the platform's own physics, is worse than anything it buys.
 */

/** How long a jump takes. Long enough to read as travel, not a cut. */
const TRAVEL = 0.9;

/**
 * Ignore a block's trailing remainder if it is smaller than this fraction of a
 * screen — otherwise the last stop in a tall section sits a sliver from the
 * next section's top and costs a whole gesture to cross.
 */
const REMAINDER = 0.35;

export default function ScrollController() {
  useLayoutEffect(() => {
    const mm = gsap.matchMedia();

    mm.add("(min-width: 1000px) and (prefers-reduced-motion: no-preference)", () => {
      const ctx = gsap.context(() => {
        /* ------------------------------------------------------ parallax --
           Kept from before: full-bleed media drifts ±4.5% against the scroll.
           Enough to give the page depth, not enough to read as an effect. */
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
      });

      /* --------------------------------------------------------- the stops --
         Measured from the direct children of <main>, in document order. That
         is deliberately not `[data-snap]`: once ScrollTrigger pins the day
         section it wraps it in a pin-spacer, and the spacer is what actually
         occupies the scroll length. Walking main's children gets the real
         geometry whatever pinning did to the DOM. */
      let stops: number[] = [];

      const measure = () => {
        const main = document.querySelector("main");
        const max = ScrollTrigger.maxScroll(window);
        if (!main || !max) return;

        const vh = window.innerHeight;
        const found: number[] = [];

        Array.from(main.children).forEach((child) => {
          const el = child as HTMLElement;
          const rect = el.getBoundingClientRect();
          const top = rect.top + window.scrollY;
          found.push(top);

          /* A block can name its own stops with `data-stops`: a comma-separated
             list of fractions of its scrollable length. The try-it section uses
             it so that a gesture moves between the moments the agent actually
             did something, rather than between evenly spaced screenfuls — you
             can't land halfway and get a reasoning panel describing neither
             state. */
          const declared = el.dataset.stops;
          if (declared) {
            const length = rect.height - vh;
            declared
              .split(",")
              .map((n) => parseFloat(n.trim()))
              .filter((n) => Number.isFinite(n))
              .forEach((fraction) => found.push(top + length * fraction));
            return;
          }

          // Otherwise a stop per screen, while more than a remainder is left.
          for (let y = top + vh; y < top + rect.height - vh * REMAINDER; y += vh) {
            found.push(y);
          }
        });

        found.push(max);

        stops = Array.from(new Set(found.map((y) => Math.round(Math.min(Math.max(y, 0), max)))))
          .sort((a, b) => a - b)
          // Collapse stops that landed within a few pixels of each other —
          // a block boundary and the previous block's last step often do.
          .filter((y, i, all) => i === 0 || y - all[i - 1] > 8);
      };

      measure();
      ScrollTrigger.addEventListener("refresh", measure);
      window.addEventListener("resize", measure);

      /* ------------------------------------------------------- the travel -- */
      let moving = false;

      const go = (direction: 1 | -1) => {
        if (moving || !stops.length) return;
        const here = window.scrollY;

        const target =
          direction === 1
            ? stops.find((y) => y > here + 4)
            : [...stops].reverse().find((y) => y < here - 4);

        if (target === undefined) return;

        moving = true;

        /* A shallow dip in opacity across the travel, so one screen dissolves
           into the next instead of sliding past. It bottoms out at 0.86 — deep
           enough to soften the hand-off, nowhere near a fade to black, which
           would read as a page transition and make every gesture feel like a
           commitment. Skipped inside a pinned section, where the content is
           supposed to be continuous with itself. */
        const main = document.querySelector("main");
        if (main && !document.querySelector(".pin-spacer .pin-spacer")) {
          gsap.fromTo(
            main,
            { opacity: 1 },
            {
              opacity: 0.86,
              duration: TRAVEL / 2,
              ease: "power1.inOut",
              yoyo: true,
              repeat: 1,
              overwrite: true,
            },
          );
        }

        gsap.to(window, {
          duration: TRAVEL,
          ease: "power2.inOut",
          scrollTo: { y: target, autoKill: false },
          onComplete: () => {
            // A short tail after arriving. Without it, one long trackpad
            // flick keeps firing and walks several stops at once, which is
            // exactly the runaway feeling this is meant to remove.
            gsap.delayedCall(0.12, () => {
              moving = false;
            });
          },
        });
      };

      const onWheel = (event: WheelEvent) => {
        // Let the browser handle zoom and horizontal gestures.
        if (event.ctrlKey || Math.abs(event.deltaX) > Math.abs(event.deltaY)) return;
        event.preventDefault();
        if (Math.abs(event.deltaY) < 2) return;
        go(event.deltaY > 0 ? 1 : -1);
      };

      const onKey = (event: KeyboardEvent) => {
        const target = event.target as HTMLElement | null;
        // Never swallow keys aimed at something interactive.
        if (target?.closest("input, textarea, select, summary, a, button")) return;

        const down = ["ArrowDown", "PageDown", " ", "Spacebar"];
        const up = ["ArrowUp", "PageUp"];

        if (down.includes(event.key)) {
          event.preventDefault();
          go(1);
        } else if (up.includes(event.key)) {
          event.preventDefault();
          go(-1);
        } else if (event.key === "Home") {
          event.preventDefault();
          gsap.to(window, { duration: TRAVEL, ease: "power2.inOut", scrollTo: 0 });
        } else if (event.key === "End") {
          event.preventDefault();
          gsap.to(window, {
            duration: TRAVEL,
            ease: "power2.inOut",
            scrollTo: ScrollTrigger.maxScroll(window),
          });
        }
      };

      window.addEventListener("wheel", onWheel, { passive: false });
      window.addEventListener("keydown", onKey);

      return () => {
        ScrollTrigger.removeEventListener("refresh", measure);
        window.removeEventListener("resize", measure);
        window.removeEventListener("wheel", onWheel);
        window.removeEventListener("keydown", onKey);
        ctx.revert();
      };
    });

    return () => mm.revert();
  }, []);

  return null;
}
