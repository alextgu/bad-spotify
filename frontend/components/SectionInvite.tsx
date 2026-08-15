import Slot from "@/components/Slot";
import { invite } from "@/lib/site";

/**
 * 8 — the ask.
 *
 * Full-bleed warm frame, two lines, two buttons. The numbers are the offer:
 * twenty people, one week each, which is a smaller and more specific promise
 * than a waitlist and therefore a more believable one.
 *
 * Hover moves 2px over 600ms rather than the mockup's 300ms. At 300ms a button
 * flinches when the cursor crosses it; at 600ms it acknowledges you.
 */
export default function SectionInvite() {
  return (
    <section className="relative h-[88svh] overflow-hidden">
      <Slot shot={invite.shot} className="absolute inset-0 scale-110" />

      <div
        aria-hidden
        className="pointer-events-none absolute inset-0 bg-[linear-gradient(to_bottom,rgba(10,10,12,.28),rgba(10,10,12,.5))]"
      />

      <div className="absolute inset-0 flex flex-col items-center justify-center px-gutter text-center text-paper">
        <h2 className="font-serif text-headline">
          {invite.lines.map((line) => (
            <span key={line} className="block">
              {line}
            </span>
          ))}
        </h2>

        <div className="mt-block flex flex-wrap justify-center gap-3">
          {invite.actions.map((action) => (
            <a
              key={action.label}
              href={action.href}
              className={`rounded-full px-8 py-4 font-mono text-label uppercase transition-[transform,background-color,border-color] duration-interaction ease-calm hover:-translate-y-0.5 ${
                action.primary
                  ? "bg-paper text-ink"
                  : "border border-paper/35 text-paper hover:border-offset hover:bg-offset"
              }`}
            >
              {action.label}
            </a>
          ))}
        </div>
      </div>
    </section>
  );
}
