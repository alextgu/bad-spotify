/**
 * `§03 / THE PRODUCT` — the marker above a section heading.
 *
 * Eight sections on one page all looked identical, so nothing told you where
 * you were or how much was left. A numbered label fixes that for the cost of
 * one line, and it reads as a document rather than as a landing page — which
 * suits a product that takes itself extremely seriously.
 *
 * Deliberately the smallest, quietest thing on the screen: mono, caption size,
 * letter-spaced, muted. If it competes with the heading it has failed.
 */
export default function SectionLabel({
  index,
  children,
}: {
  /** 1-based. Matches the order in app/page.tsx — keep them in step. */
  index: number;
  children: React.ReactNode;
}) {
  return (
    <p className="font-mono text-caption uppercase tracking-eyebrow text-ink-muted">
      §{String(index).padStart(2, "0")} / {children}
    </p>
  );
}
