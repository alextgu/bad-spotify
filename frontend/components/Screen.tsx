/**
 * One section, exactly one viewport. No more, no less.
 *
 * This is the rule the page is built on now, so it is enforced in one place
 * rather than trusted to seven components: `h-svh` fixes the height, and
 * `overflow-hidden` means a section that outgrows a screen visibly clips
 * instead of quietly pushing the next one down. That is deliberate — a clipped
 * section is a bug you can see, and the alternative is a page that drifts back
 * to nine-and-a-half screens one paragraph at a time.
 *
 * `svh` rather than `vh`: on mobile, `vh` includes the browser chrome that
 * retracts as you scroll, so a "full height" section is taller than the
 * visible area and every screen starts slightly clipped.
 *
 * If something genuinely doesn't fit, cut the content. Don't shrink the type
 * and don't reach for a scrollbar inside a section.
 */
export default function Screen({
  children,
  id,
  className = "",
  padded = true,
}: {
  children: React.ReactNode;
  id?: string;
  className?: string;
  /** Off for full-bleed screens that manage their own edges. */
  padded?: boolean;
}) {
  return (
    <section
      id={id}
      className={`flex h-svh flex-col justify-center overflow-hidden ${
        padded ? "px-gutter py-rest" : ""
      } ${className}`}
    >
      {children}
    </section>
  );
}
