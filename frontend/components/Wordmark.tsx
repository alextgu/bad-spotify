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
      ? "text-display"
      : "text-base";

  return (
    <span className={`font-semibold ${styles} ${className}`}>{brand.name}</span>
  );
}
