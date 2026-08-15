import Image from "next/image";

/**
 * The Slopify mark, twinkling.
 *
 * The icon is deliberate AI slop — a gradient bubble, four-pointed stars, a
 * misspelt wordmark, and "amde by AI" tiled across the art. The animation
 * commits to that rather than trying to dignify it: the stars twinkle, the
 * mark bobs, and a soft halo breathes behind it, which is exactly what every
 * generated app icon on the internet does.
 *
 * It is the one place on the page allowed to be tacky, and it works *because*
 * everything around it is not. A page that behaved like this throughout would
 * just be a bad page; one restrained screen with a winking logo in the corner
 * is a joke.
 *
 * Pure CSS — no canvas, no library, no runtime. Five absolutely-placed stars
 * with periods that share no common multiple, so they never fire together and
 * never settle into a beat. Synchronised twinkling reads as a loading spinner.
 *
 * `aria-hidden` on every star: they are decoration, and a screen reader
 * announcing five sparkles beside a logo is nobody's idea of a good time.
 */

/**
 * The four-pointed star that is already drawn inside the icon art.
 *
 * Two nested elements rather than one, and that is the whole trick behind the
 * hover: the outer span owns *position and hover scale* as a transition, the
 * inner svg owns the *twinkle* as a keyframe animation. Put both on one
 * element and they fight — the keyframe sets `transform` every frame and
 * stamps the hover straight back out. Split across two, they compose.
 */
function Star({
  style,
  hover,
}: {
  style?: React.CSSProperties;
  /** Extra scale applied while the mark is hovered. */
  hover: string;
}) {
  return (
    <span
      aria-hidden
      className={`absolute block transition-transform duration-interaction ease-calm ${hover}`}
      style={style}
    >
      <svg
        viewBox="0 0 24 24"
        className="h-full w-full motion-safe:animate-[sparkle_var(--dur)_ease-in-out_var(--delay)_infinite]"
      >
        <path
          d="M12 0c0 7 5 12 12 12-7 0-12 5-12 12 0-7-5-12-12-12 7 0 12-5 12-12Z"
          fill="currentColor"
        />
      </svg>
    </span>
  );
}

/**
 * Position, size, colour, period and offset. Deliberately uneven.
 *
 * `hover` is per-star too: the outer stars throw further than the inner ones,
 * so hovering reads as the thing puffing outward rather than as five sprites
 * all scaling by the same amount.
 */
const STARS = [
  { top: "-22%", left: "62%", size: "38%", colour: "#B9A6FF", dur: "3.1s", delay: "0s", hover: "group-hover:scale-[1.6] group-hover:-translate-y-1" },
  { top: "18%", left: "-20%", size: "26%", colour: "#7DD8C0", dur: "4.3s", delay: "0.7s", hover: "group-hover:scale-[1.5] group-hover:-translate-x-1" },
  { top: "72%", left: "88%", size: "30%", colour: "#8AB6FF", dur: "5.2s", delay: "1.4s", hover: "group-hover:scale-[1.55] group-hover:translate-x-1" },
  { top: "84%", left: "6%", size: "20%", colour: "#E2A9F5", dur: "3.9s", delay: "2.1s", hover: "group-hover:scale-[1.45] group-hover:translate-y-1" },
  { top: "-6%", left: "16%", size: "16%", colour: "#FFFFFF", dur: "6.1s", delay: "0.3s", hover: "group-hover:scale-[1.35]" },
];

export default function LogoMark({ size = 36 }: { size?: number }) {
  return (
    <span
      className="group relative inline-block shrink-0"
      style={{ width: size, height: size }}
    >
      {/* The bloom. Sits behind everything and never quite stops moving. */}
      <span
        aria-hidden
        className="absolute -inset-2 rounded-full bg-[radial-gradient(circle,rgba(154,140,255,0.55),transparent_68%)]
                   blur-[6px] motion-safe:animate-[halo_7s_ease-in-out_infinite]"
      />

      {/* A second, brighter bloom that only exists on hover. Layered rather
          than tweaked, because the one underneath is mid-keyframe on opacity
          and anything set on top of it would be overwritten every frame. */}
      <span
        aria-hidden
        className="absolute -inset-3 rounded-full bg-[radial-gradient(circle,rgba(120,230,190,0.5),transparent_66%)]
                   opacity-0 blur-[10px] transition-opacity duration-interaction ease-calm
                   group-hover:opacity-100"
      />

      {/* The bob stays on the image; the hover lift and tilt go on the wrapper,
          for the same reason the stars are split in two — a keyframe writing
          `transform` every frame would erase a hover transform on the same
          element. */}
      <span className="relative block h-full w-full transition-transform duration-interaction ease-calm group-hover:-translate-y-0.5 group-hover:rotate-[6deg] group-hover:scale-110">
        <Image
          src="/logo.png"
          alt=""
          width={size * 2}
          height={size * 2}
          priority
          className="h-full w-full object-contain transition-[filter] duration-interaction ease-calm
                     group-hover:brightness-110 group-hover:saturate-150
                     motion-safe:animate-[bob_5.5s_ease-in-out_infinite]"
        />
      </span>

      {STARS.map((star) => (
        <Star
          key={star.left + star.top}
          hover={star.hover}
          style={
            {
              top: star.top,
              left: star.left,
              width: star.size,
              height: star.size,
              color: star.colour,
              "--dur": star.dur,
              "--delay": star.delay,
            } as React.CSSProperties
          }
        />
      ))}
    </span>
  );
}
