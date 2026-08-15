import Label from "@/components/Label";
import Screen from "@/components/Screen";
import Slot from "@/components/Slot";
import { demo } from "@/lib/site";

/**
 * 3 — the film.
 *
 * One screen, one moving image, two labels. The three-up grid of moments that
 * used to sit under it is gone: it was the half of this section that pushed it
 * past one page, and a still photograph arguing alongside a film of the same
 * thing is the weaker of the two.
 *
 * Full bleed and unpadded — the film runs to all four edges and the labels sit
 * inside it rather than under it, so the screen is the film rather than a film
 * placed on a page.
 */
export default function SectionDemo() {
  return (
    <Screen id="demo" padded={false} className="relative bg-ink">
      <Slot shot={demo.film} className="absolute inset-0 scale-105" data-parallax />

      <div className="pointer-events-none absolute inset-x-0 bottom-0 h-1/3 bg-[linear-gradient(to_top,rgba(10,10,12,.6),transparent)]" />

      <div className="absolute inset-x-0 bottom-0 flex flex-wrap justify-between gap-3 px-gutter pb-rest">
        <Label tone="offset" className="!text-offset">
          {demo.caption.left}
        </Label>
        <Label className="!text-paper/55">{demo.caption.right}</Label>
      </div>
    </Screen>
  );
}
