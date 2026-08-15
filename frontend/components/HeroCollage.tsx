import Image from "next/image";
import NowPlayingCard from "@/components/NowPlayingCard";

/**
 * The three-piece title-page collage.
 *
 * It lives entirely inside the first viewport: the forest anchors the stack,
 * the rock photo overlaps from below, and the transparent notes stitch the two
 * scenes together. Each piece owns its own slow, restrained hover transform.
 */
export default function HeroCollage() {
  return (
    <div
      aria-label="A forest walk colliding with a rock performance"
      className="pointer-events-none absolute right-[1.5%] top-[8%] z-[5] hidden h-[82%] w-[56%] lg:block"
    >
      <figure
        className="pointer-events-auto absolute left-0 top-[4%] z-10 h-[78%] w-[82%]
                   overflow-hidden rounded-[2rem] shadow-[0_28px_80px_rgba(0,0,0,0.42)]
                   ring-1 ring-white/10 transition-transform duration-700 ease-[cubic-bezier(0.22,1,0.36,1)]
                   origin-center will-change-transform hover:-rotate-[1.5deg] hover:scale-[1.035]"
      >
        <Image
          src="/images/forest_walk.png"
          alt="A quiet wooden path through a green forest"
          fill
          priority
          sizes="(min-width: 1024px) 46vw, 0px"
          className="object-cover"
        />
      </figure>

      {/* The rock photo used to sit here, rotated 5.5deg over the corner. Its
          file was never added — `/images/rock.png` returns 404 — so it drew as
          a shadowed empty rectangle with an alt string nobody could see. A
          frame around nothing is worse than one less frame. If the photo turns
          up, this is where it goes. */}

      {/* The track, sitting ON the walk, lower right.
          The forest figure occupies left 0 to 82% across and 4% to 82% down,
          so these offsets put the bar inside that box with a margin rather
          than hanging off it — measured against the photo, not eyeballed
          against the section, which is why they are odd numbers.

          It now crosses the bottom edge rather than clearing it. There were
          only 11px of photograph left below it at 20%, so "down more" had
          nowhere to go inside the frame — it straddles instead, which reads
          as a sticker laid on the picture rather than a bar squeezed into a
          corner. The right margin stays clear of the 2rem corner radius.

          `pointer-events-auto` because the wrapper turns them off — the
          collage is decoration, this one is not. `z-40` to clear the notes. */}
      <div className="pointer-events-auto absolute bottom-[14%] right-[20%] z-40">
        <NowPlayingCard />
      </div>

      <figure
        className="group pointer-events-auto absolute -right-[2%] -top-[5%] z-30 h-[82%] w-[48%]
                   drop-shadow-[0_16px_28px_rgba(222,32,190,0.28)]
                   motion-safe:animate-[notes-float_6s_ease-in-out_infinite]"
      >
        <div
          className="relative h-full w-full transition-transform duration-700
                     origin-center ease-[cubic-bezier(0.22,1,0.36,1)] will-change-transform
                     group-hover:rotate-[2.5deg] group-hover:scale-[1.04]"
        >
          <Image
            src="/images/notes.png"
            alt=""
            fill
            priority
            sizes="(min-width: 1024px) 27vw, 0px"
            className="object-contain"
          />
        </div>
      </figure>
    </div>
  );
}
