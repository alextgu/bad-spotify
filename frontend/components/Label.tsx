/**
 * The mono label. Section markers, timecodes, captions under film.
 *
 * `tone="offset"` tints it with the accent — the only place the accent
 * appears in type. Used sparingly enough that it still means "this one".
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
  const colour = tone === "offset" ? "text-offset" : "text-graphite";
  return (
    <span className={`font-mono text-label uppercase ${colour} ${className}`}>
      {children}
    </span>
  );
}
