import SectionLabel from "@/components/SectionLabel";

/**
 * A section's label and its two-tone heading, as one unit.
 *
 * **Two-tone**: the first half at full strength, the rest muted. It costs
 * nothing — two colours we already have — and it's most of the difference
 * between a headline that looks composed and one that looks typed. It also
 * does real work here: the muted half is almost always the turn in the
 * sentence ("A useless product, *built properly*"), so the emphasis lands
 * where the joke does.
 *
 * Every section heading on the page goes through this. That's the point: they
 * can't drift apart if there's only one of them.
 */
export default function SectionHeading({
  index,
  label,
  lead,
  trail,
  className = "",
}: {
  index: number;
  label: string;
  /** Full strength. */
  lead: string;
  /** Muted. The turn in the sentence. */
  trail?: string;
  className?: string;
}) {
  return (
    <div className={className}>
      <SectionLabel index={index}>{label}</SectionLabel>
      <h2 className="mt-heading-sub text-heading">
        {lead}
        {trail && <span className="text-ink-muted"> {trail}</span>}
      </h2>
    </div>
  );
}
