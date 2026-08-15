import Label from "@/components/Label";
import Slot from "@/components/Slot";
import { brand } from "@/lib/brand";
import { hero } from "@/lib/site";

/**
 * 1 — the hero.
 *
 * A single film, inset inside the paper rather than bleeding to the window
 * edge. The 15px margin of paper around a 26px-radius card is doing a
 * surprising amount of work: a full-bleed video says *website*, a framed one
 * says *object*, and the whole page is arguing that this is a product rather
 * than a launch.
 *
 * The type sits in the left third, which is why the shot note asks for that
 * third to be dark. `hero-feather` is a gradient rather than a flat scrim
 * because a uniform overlay dulls the whole frame to protect a corner of it.
 *
 * Already exactly one viewport, so it doesn't use `Screen` — it needs the
 * 15px of paper around the card, which `Screen`'s padding scale doesn't do.
 */
export default function SectionHero() {
  return (
    <section id="hero" className="h-svh p-[15px]">
      <div className="relative h-full w-full overflow-hidden rounded-frame bg-[#16151a]">
        <Slot shot={hero.shot} className="absolute inset-0" />

        {/* Feathered, not flat: the type stays legible on the left without
            the right half of the frame being dimmed to pay for it. */}
        <div
          aria-hidden
          className="pointer-events-none absolute inset-0
                     bg-[linear-gradient(to_right,rgba(10,10,12,.72)_0%,rgba(10,10,12,.58)_12%,rgba(10,10,12,.4)_26%,rgba(10,10,12,.22)_40%,rgba(10,10,12,.08)_54%,transparent_68%),linear-gradient(to_bottom,rgba(10,10,12,.4)_0%,rgba(10,10,12,.16)_14%,transparent_28%)]"
        />

        {/* One flow column rather than three absolutely-placed blocks. The
            first version pinned the type at `top: 24%` and the clip to the
            bottom edge; on a short window they simply overlapped, and the
            subhead was sitting underneath the clip card with no way for
            either to know. Laid out as a column, the space between them is
            whatever is left over, and it can never go negative. */}
        <div className="absolute inset-0 z-10 flex flex-col justify-between p-[38px] text-paper">
          <div className="flex items-center gap-3">
            <span className="rounded border border-dashed border-paper/40 px-3 py-2 font-mono text-label uppercase text-paper/70">
              logo
            </span>
            {/* Set in the display face, not the mono label. It is the
                product's name, and rendering it at caption weight made it the
                least considered thing on a page about it. */}
            <span className="font-display text-[1.0625rem] font-semibold tracking-[-0.03em] text-paper">
              {brand.name}
            </span>
          </div>

          <div className="max-w-[38rem]">
            {/* What it is, said by pointing at the thing everyone already
                has. It goes ABOVE the headline because the headline is a
                promise and this is the category — a reader who doesn't know
                what kind of object this is cannot evaluate the promise. */}
            <Label tone="offset" className="block !text-offset">
              {brand.positioning}
            </Label>

            <h1 className="mt-block max-w-[13ch] font-display text-display">
              {hero.headline}{" "}
              {/* Colour, not italic. The serif italic here read as a wine
                  label; the accent alone does the emphasis. */}
              <span className="text-offset">{hero.headlineAccent}</span>.
            </h1>

            <p className="mt-block max-w-[30ch] text-body text-paper/85">
              {hero.sub}
            </p>
          </div>

          <div className="flex items-end justify-between gap-4">
            {/* The floating clip sits over the film rather than beside it, so
                the hero stays one image. */}
            <div className="w-[min(300px,30vw)] overflow-hidden rounded-card border-2 border-paper/90">
              <div className="relative aspect-[16/10]">
                <Slot shot={hero.clip} className="absolute inset-0" />
                <span
                  aria-hidden
                  className="absolute inset-0 grid place-items-center"
                >
                  <span className="ml-1 border-y-[13px] border-l-[20px] border-y-transparent border-l-paper drop-shadow-[0_2px_12px_rgba(0,0,0,.5)]" />
                </span>
              </div>
            </div>

            <Label className="!text-paper/55">Scroll</Label>
          </div>
        </div>
      </div>
    </section>
  );
}
