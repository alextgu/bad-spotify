"use client";

import { useLayoutEffect, useRef, useState } from "react";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import Label from "@/components/Label";
import Slot from "@/components/Slot";
import { day, dayPanels } from "@/lib/site";

gsap.registerPlugin(ScrollTrigger);

/**
 * 5 — one day, six cues. Pinned, and dragged sideways by vertical scroll.
 *
 * The pacing here is the whole difference between this and the mockup, and it
 * is set by ONE number: how much vertical scroll the horizontal travel is
 * spread over. The mockup used `dist + 50vh`, so the cards raced past — the
 * section was over before you had read the second one. This uses
 * `dist * 1.7 + 80vh`, which is nearly twice the scrolling for the same
 * distance travelled. Nothing about the animation is slower; there is simply
 * more room, and that is what reading as calm actually costs.
 *
 * `scrub: 1.2` rather than `0.85` adds a little lag between the wheel and the
 * cards, so the track settles after you stop rather than stopping with you.
 *
 * Below 1000px the pin is dropped entirely and this becomes a normal
 * horizontal swipe with scroll-snap — hijacking vertical scroll on a
 * touchscreen is the single most disliked thing a page can do.
 */
export default function SectionDay() {
  const root = useRef<HTMLDivElement>(null);
  const track = useRef<HTMLDivElement>(null);
  const fill = useRef<HTMLDivElement>(null);
  const [active, setActive] = useState(0);
  const [time, setTime] = useState<string>(day[0].time);

  useLayoutEffect(() => {
    const mm = gsap.matchMedia();

    mm.add("(min-width: 1000px) and (prefers-reduced-motion: no-preference)", () => {
      const ctx = gsap.context(() => {
        const el = track.current;
        const viewport = el?.parentElement;
        if (!el || !viewport) return;

        const distance = () =>
          Math.max(0, el.scrollWidth - viewport.offsetWidth + 120);

        gsap.to(el, {
          x: () => -distance(),
          ease: "none",
          scrollTrigger: {
            trigger: root.current,
            start: "top top",
            // The one number that sets the pace of this section.
            end: () => "+=" + (distance() * 1.7 + window.innerHeight * 0.8),
            pin: true,
            scrub: 1.2,
            anticipatePin: 1,
            invalidateOnRefresh: true,
            onUpdate: (self) => {
              const p = self.progress;
              gsap.set(fill.current, { scaleX: p });
              setTime(day[Math.min(day.length - 1, Math.floor(p * day.length))].time);
              setActive(
                Math.min(dayPanels.length - 1, Math.floor(p * dayPanels.length)),
              );
            },
          },
        });
      }, root);

      return () => ctx.revert();
    });

    return () => mm.revert();
  }, []);

  return (
    <section ref={root} data-snap className="bg-bone">
      <div className="lg:grid lg:h-svh lg:grid-cols-[36%_64%] lg:overflow-hidden">
        {/* ------------------------------------------------------- the copy -- */}
        <div className="flex flex-col justify-center border-hairline px-gutter py-section-sm lg:border-r lg:py-0 lg:pl-[max(1.5rem,calc((100vw-1320px)/2))] lg:pr-rest">
          <div className="relative lg:min-h-[200px]">
            {dayPanels.map((panel, i) => (
              <div
                key={panel.index}
                className={`transition-[opacity,transform] duration-reveal ease-calm lg:absolute lg:inset-0 ${
                  i === active
                    ? "opacity-100 lg:translate-y-0"
                    : "lg:pointer-events-none lg:translate-y-3 lg:opacity-0"
                } ${i > 0 ? "mt-rest lg:mt-0" : ""}`}
              >
                <Label tone="offset" className="block">
                  {panel.index} — {panel.label}
                </Label>
                <h2 className="mt-block font-serif text-headline">{panel.title}</h2>
              </div>
            ))}
          </div>

          {/* Progress through the day. Hidden on mobile, where the cards
              swipe and the bar would be measuring nothing. */}
          <div className="mt-rest hidden lg:block">
            <div className="relative h-px bg-hairline">
              <div
                ref={fill}
                className="absolute inset-0 origin-left scale-x-0 bg-offset"
              />
            </div>
            <div className="mt-4 flex justify-between">
              <Label>One day</Label>
              <Label tone="offset">{time}</Label>
            </div>
          </div>
        </div>

        {/* ------------------------------------------------------ the cards -- */}
        <div className="flex snap-x snap-mandatory items-center overflow-x-auto pb-section-sm lg:overflow-hidden lg:pb-0">
          <div ref={track} className="flex gap-gutter px-gutter lg:px-rest">
            {day.map((cue) => (
              <article
                key={cue.time}
                className="w-[76vw] shrink-0 snap-center lg:w-[360px]"
              >
                <Slot shot={cue.shot} className="aspect-[4/5] rounded-card" />
                <div className="flex items-baseline justify-between gap-3 pt-gutter">
                  <h3 className="font-serif text-title">{cue.title}</h3>
                  <Label tone="offset">{cue.time}</Label>
                </div>
                <div className="mt-3 border-t border-hairline pt-3">
                  <h4 className="font-serif text-title">{cue.track}</h4>
                  <Label className="mt-1.5 block">{cue.artist}</Label>
                </div>
              </article>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
