import SectionBroke from "@/components/SectionBroke";
import SectionDay from "@/components/SectionDay";
import SectionEvidence from "@/components/SectionEvidence";
import SectionFAQ from "@/components/SectionFAQ";
import SectionHero from "@/components/SectionHero";
import SectionInvite from "@/components/SectionInvite";
import SectionStatement from "@/components/SectionStatement";
import SectionTrio from "@/components/SectionTrio";
import SectionUnderHood from "@/components/SectionUnderHood";
import Smoother from "@/components/Smoother";

/**
 * The launch page. Nine sections, no navbar.
 *
 * ---------------------------------------------------------------------------
 * THE ORDER IS THE WIREFRAME. It is the one part of this page that has been
 * agreed, and it survived the visual restart. Everything else — type, colour,
 * spacing, motion — is open; this is not.
 * ---------------------------------------------------------------------------
 *
 *   1  Hero        the film, framed in paper       one image carries the pitch
 *   2  Statement   one sentence, alone             the turn
 *   3  Trio        what it does, in three moves
 *   4  Evidence    the film, then three moments    proof
 *   5  Day         one day, six cues, pinned       the argument at length
 *   6  Under hood  the numbers, on dark            rest, and precision
 *   7  Broke       what failed, struck through     credibility
 *   8  Invite      the ask
 *   9  FAQ         the awkward questions
 *
 * **Sections 4 and 5 of the original mockup are section 4 here.** They were a
 * full-bleed film and then a separate three-up grid; grouped, they read as one
 * piece of evidence rather than as a film followed by an unexplained grid.
 *
 * The film sits at 4, after the statement and the trio but before anything is
 * argued at length. It is the hook, not the proof — a page that explains
 * before it shows has already lost the reader.
 *
 * Nine is a ceiling, not a target. Each screen holds one idea; if something
 * new goes in, something here comes out.
 *
 * `data-snap` on a section marks it as somewhere the page is allowed to settle
 * — see `Smoother`. Not every section carries it: the ones that are taller
 * than a screen would drag you back out of themselves.
 */
export default function Home() {
  return (
    <Smoother>
      <main>
        {/* 1 — one image, and the promise. */}
        <div data-snap>
          <SectionHero />
        </div>

        {/* 2 — the turn. One sentence, and a lot of nothing around it. */}
        <div data-snap>
          <SectionStatement />
        </div>

        {/* 3 — what it actually does. */}
        <SectionTrio />

        {/* 4 — proof. The film and the three moments are one section now. */}
        <div data-snap>
          <SectionEvidence />
        </div>

        {/* 5 — the long argument. Pins itself; marks its own snap point. */}
        <SectionDay />

        {/* 6 — the eye rests, and the claims get precise. */}
        <div data-snap>
          <SectionUnderHood />
        </div>

        {/* 7 — and here is what didn't work. */}
        <SectionBroke />

        {/* 8 — the ask. */}
        <div data-snap>
          <SectionInvite />
        </div>

        {/* 9 — the questions a sceptic is already forming. */}
        <div data-snap>
          <SectionFAQ />
        </div>
      </main>
    </Smoother>
  );
}
