"use client";

import { useState } from "react";
import Label from "@/components/Label";
import Screen from "@/components/Screen";
import Slot from "@/components/Slot";
import { demo } from "@/lib/site";

/**
 * 3 — the film.
 *
 * One screen, one moving image, and one compact explanation. The three-up grid
 * used to sit under it is gone: it was the half of this section that pushed it
 * past one page, and a still photograph arguing alongside a film of the same
 * thing is the weaker of the two.
 *
 * Full bleed and unpadded — the film runs to all four edges and the labels sit
 * inside it rather than under it, so the screen is the film rather than a film
 * placed on a page.
 */
export default function SectionDemo() {
  const [isPlaying, setIsPlaying] = useState(false);
  return (
    <Screen id="demo" padded={false} className="relative bg-ink">
      <Slot
        shot={demo.film}
        className="absolute inset-0 h-full w-full object-cover"
        background={false}
        onPlaybackChange={setIsPlaying}
      />

      <div
        className={[
          "pointer-events-none absolute inset-x-0 bottom-0 h-1/3",
          "bg-[linear-gradient(to_top,rgba(10,10,12,.6),transparent)]",
          "transition-opacity duration-interaction ease-calm",
          isPlaying ? "opacity-0" : "opacity-100",
        ].join(" ")}
      />

      <div
        className={[
          "pointer-events-none absolute inset-x-0 bottom-0 flex flex-col gap-5",
          "px-gutter pb-24 text-paper transition-opacity duration-interaction ease-calm",
          "lg:flex-row lg:items-end lg:justify-between",
          isPlaying ? "opacity-0" : "opacity-100",
        ].join(" ")}
      >
        <div className="max-w-measure">
          <Label tone="offset" className="!text-offset">
            {demo.caption.left}
          </Label>
          <h2 className="mt-3 font-display text-headline">{demo.title}</h2>
          <p className="mt-3 max-w-measure-sub text-body text-paper/75">
            {demo.body}
          </p>
        </div>
        <Label className="shrink-0 !text-paper/55">{demo.caption.right}</Label>
      </div>
    </Screen>
  );
}
