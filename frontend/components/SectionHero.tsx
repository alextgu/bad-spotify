import Label from "@/components/Label";
import LogoMark from "@/components/LogoMark";
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
            the right half of the frame being dimmed to pay for it.

            Deepened for the mysterious read. The left third now goes to
            near-black and the frame darkens at the bottom as well as the top,
            so the picture emerges out of the dark rather than sitting on it.
            A vignette on the right keeps the corners from lifting. */}
        <div
          aria-hidden
          className="pointer-events-none absolute inset-0
                     bg-[linear-gradient(to_right,rgba(6,6,8,.94)_0%,rgba(6,6,8,.86)_14%,rgba(6,6,8,.66)_28%,rgba(6,6,8,.4)_42%,rgba(6,6,8,.16)_58%,transparent_74%),linear-gradient(to_bottom,rgba(6,6,8,.55)_0%,rgba(6,6,8,.2)_16%,transparent_34%,rgba(6,6,8,.35)_86%,rgba(6,6,8,.6)_100%),radial-gradient(120%_90%_at_78%_50%,transparent_45%,rgba(6,6,8,.45))]"
        />

        {/* One flow column rather than three absolutely-placed blocks. The
            first version pinned the type at `top: 24%` and the clip to the
            bottom edge; on a short window they simply overlapped, and the
            subhead was sitting underneath the clip card with no way for
            either to know. Laid out as a column, the space between them is
            whatever is left over, and it can never go negative. */}
        <div className="absolute inset-0 z-10 flex flex-col justify-between p-[38px] text-paper">
          <div className="flex items-center gap-3">
            {/* Cropped out of the icon sheet in Downloads. The "amde by AI"
                watermark is tiled across the artwork itself and is part of the
                joke rather than something to remove — at this size it reads as
                texture, which is the only size it has to survive.

                Mark and name react separately, not as one `group`. LogoMark
                owns a `group` of its own for its stars and blooms, and a
                wrapper group would not reach inside it — Tailwind binds
                `group-hover:` to the nearest marked ancestor. Two independent
                hovers is the honest version; faking a shared one would mean
                the mark reaching out for a class name its parent happens to
                set. */}
            <span className="flex items-center gap-4">
              <LogoMark size={64} />
              {/* Set in the display face, not the mono label. It is the
                  product's name, and rendering it at caption weight made it
                  the least considered thing on a page about it. */}
              {/* Sized off the viewport rather than fixed, so it stays in
                  proportion to the headline underneath it at every width. It
                  is capped below the headline's ceiling on purpose: the name
                  can be the loudest thing in the corner without becoming the
                  loudest thing on the screen, which is still the promise. */}
              <span
                className="cursor-default font-display text-[clamp(2rem,3.1vw,3rem)] font-semibold
                           leading-none tracking-[-0.04em] text-paper
                           transition-[letter-spacing,opacity] duration-interaction ease-calm
                           hover:tracking-[-0.025em] hover:opacity-90"
              >
                {brand.name}
              </span>
            </span>
          </div>

          <div className="max-w-[38rem]">
            {/* Says what it does NOT do, beside a dot that is quietly
                pulsing. Three refusals and no explanation — that withholding
                is the whole reason the top of the screen reads as something
                already running rather than as a product being introduced. */}
            <span className="flex items-center gap-2.5">
              <span
                aria-hidden
                className="h-1.5 w-1.5 rounded-full bg-offset motion-safe:animate-[listening_3.4s_ease-in-out_infinite]"
              />
              <Label tone="offset" className="!text-offset">
                {brand.positioning}
              </Label>
            </span>

            <h1 className="mt-block max-w-[13ch] font-display text-display">
              {hero.headline}{" "}
              {/* Colour, not italic. The serif italic here read as a wine
                  label; the accent alone does the emphasis. */}
              <span className="text-offset">{hero.headlineAccent}</span>.
            </h1>

            {/* The punchline, set as flat as it will go: mono, uppercase,
                widely tracked, and no larger than it has to be. The headline
                above is atmospheric and admits nothing; this states the actual
                product in a voice that sounds like a system label rather than
                a boast. Said in the display face at body size it would read as
                a tagline — which is a claim — instead of as a fact. */}
            <p className="mt-block max-w-[34ch] font-mono text-[0.8125rem] uppercase leading-relaxed tracking-[0.2em] text-paper/75">
              {hero.sub}
            </p>
          </div>

          <div className="flex items-end justify-between gap-4">
            {/* The floating clip sits over the film rather than beside it, so
                the hero stays one image.

                It is a coming-soon card until the cinematic is cut, and it has
                NO play triangle. A play button with nothing behind it is the
                same trap as the upload button on the try-it screen: the click
                is the moment someone finds out, and it costs more trust than
                the affordance was worth. Saying so up front costs nothing.

                The border is dimmed to match — at full strength it read as an
                active control. */}
            <div className="w-[min(300px,30vw)] overflow-hidden rounded-card border border-paper/25 bg-[rgba(8,8,10,.55)] backdrop-blur-[2px]">
              <div className="relative grid aspect-[16/10] place-items-center px-4 text-center">
                <span>
                  <Label className="block !text-paper/80">Cinematic demo</Label>
                  <p className="mt-2 font-mono text-[0.6875rem] uppercase tracking-[0.18em] text-paper/45">
                    Coming soon
                  </p>
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
