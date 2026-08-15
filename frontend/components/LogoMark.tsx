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

/** The four-pointed star that is already drawn inside the icon art. */
function Star({
  className,
  style,
}: {
  className?: string;
  style?: React.CSSProperties;
}) {
  return (
    <svg
      viewBox="0 0 24 24"
      aria-hidden
      className={`absolute ${className}`}
      style={style}
    >
      <path
        d="M12 0c0 7 5 12 12 12-7 0-12 5-12 12 0-7-5-12-12-12 7 0 12-5 12-12Z"
        fill="currentColor"
      />
    </svg>
  );
}

/** Position, size, colour, period and offset. Deliberately uneven. */
const STARS = [
  { top: "-22%", left: "62%", size: "38%", colour: "#B9A6FF", dur: "3.1s", delay: "0s" },
  { top: "18%", left: "-20%", size: "26%", colour: "#7DD8C0", dur: "4.3s", delay: "0.7s" },
  { top: "72%", left: "88%", size: "30%", colour: "#8AB6FF", dur: "5.2s", delay: "1.4s" },
  { top: "84%", left: "6%", size: "20%", colour: "#E2A9F5", dur: "3.9s", delay: "2.1s" },
  { top: "-6%", left: "16%", size: "16%", colour: "#FFFFFF", dur: "6.1s", delay: "0.3s" },
];

export default function LogoMark({ size = 36 }: { size?: number }) {
  return (
    <span
      className="relative inline-block shrink-0"
      style={{ width: size, height: size }}
    >
      {/* The bloom. Sits behind everything and never quite stops moving. */}
      <span
        aria-hidden
        className="absolute -inset-2 rounded-full bg-[radial-gradient(circle,rgba(154,140,255,0.55),transparent_68%)]
                   blur-[6px] motion-safe:animate-[halo_7s_ease-in-out_infinite]"
      />

      <Image
        src="/logo.png"
        alt=""
        width={size * 2}
        height={size * 2}
        priority
        className="relative h-full w-full object-contain motion-safe:animate-[bob_5.5s_ease-in-out_infinite]"
      />

      {STARS.map((star) => (
        <Star
          key={star.left + star.top}
          className="motion-safe:animate-[sparkle_var(--dur)_ease-in-out_var(--delay)_infinite]"
          style={
            {
              top: star.top,
              left: star.left,
              width: star.size,
              height: star.size,
              color: star.colour,
              opacity: 0,
              "--dur": star.dur,
              "--delay": star.delay,
            } as React.CSSProperties
          }
        />
      ))}
    </span>
  );
}
