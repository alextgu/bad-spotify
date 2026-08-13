import { brand } from "@/lib/brand";

/**
 * PLACEHOLDER wordmark — set in type, not drawn.
 *
 * That's deliberate for now: a name set cleanly in tight-tracked type reads as
 * more considered than a rushed logo, and it costs nothing to replace. When
 * the real name is chosen, this is where the drawn mark goes.
 */
export default function Wordmark({
  className = "",
  size = "hero",
}: {
  className?: string;
  size?: "hero" | "nav";
}) {
  const styles =
    size === "hero"
      ? "text-[clamp(3rem,11vw,8.5rem)] leading-[0.92] tracking-[-0.045em]"
      : "text-base tracking-[-0.02em]";

  return (
    <span className={`font-semibold ${styles} ${className}`}>{brand.name}</span>
  );
}
