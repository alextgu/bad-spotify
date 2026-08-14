import { brand } from "@/lib/brand";


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
