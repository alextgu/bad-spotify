/**
 * The mono label. Section markers, timecodes, captions under film.
 *
 * `tone="offset"` tints it with the accent — the only place the accent
 * appears in type. Used sparingly enough that it still means "this one".
 *
 * It resolves to the *deep* green, not the bright one: this type is 10.5px,
 * and the bright accent on paper sits near 2.3:1, which is unreadable at that
 * size regardless of what it looks like at a glance. On dark sections the
 * bright green is applied directly via `className`.
 */
export default function Label({
  children,
  tone = "quiet",
  className = "",
}: {
  children: React.ReactNode;
  tone?: "quiet" | "offset";
  className?: string;
}) {
  const colour = tone === "offset" ? "text-offset-ink" : "text-graphite";
  return (
    <span className={`font-mono text-label uppercase ${colour} ${className}`}>
      {children}
    </span>
  );
}
