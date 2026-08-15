import ScrollController from "@/components/ScrollController";
import SectionDemo from "@/components/SectionDemo";
import SectionDescription from "@/components/SectionDescription";
import SectionFAQ from "@/components/SectionFAQ";
import SectionHero from "@/components/SectionHero";
import SectionPipeline from "@/components/SectionPipeline";
import SectionResults from "@/components/SectionResults";
import SectionTryIt from "@/components/SectionTryIt";
import Strings from "@/components/Strings";

/**
 * The launch page. Seven screens, no navbar.
 *
 * ---------------------------------------------------------------------------
 * SEVEN SECTIONS, AND EACH ONE IS EXACTLY ONE VIEWPORT
 * ---------------------------------------------------------------------------
 *
 *   1  Hero          one image, and the promise
 *   2  Description   what it is — the statement, then the three moves
 *   3  Demo          the film, full bleed
 *   4  Try it        hand it over; the whole screen is one link
 *   5  Pipeline      a closer look at the actual mechanism
 *   6  Results       the numbers, and three things worth being pleased about
 *   7  FAQ           the awkward questions, and the end of the page
 *
 * This order is the wireframe and is not open. The one-viewport rule is not
 * open either, and it is enforced by `Screen` rather than by good intentions:
 * a section that outgrows a screen clips visibly instead of quietly pushing
 * the page back out to nine-and-a-half screens.
 *
 * The page got here by losing things, and it is worth knowing what, because
 * every one of them was built and works and is still in git: a pinned
 * horizontal timeline of six cues across one day, a three-up grid of moments
 * under the film, a struck-through list of what broke in the first six hours,
 * and a full-bleed closing ask. They were cut because they are not among the
 * seven, not because they failed. If one comes back, something here goes.
 *
 * `ScrollController` moves one screen per gesture; because every block is now
 * exactly one viewport, every stop is a section boundary and nothing lands in
 * the middle of anything. The wrapping `<div>`s are what it measures, so they
 * are structural rather than decorative.
 */
export default function Home() {
  return (
    <>
      <ScrollController />
      <Strings />

      <main>
        {/* 1 */}
        <div>
          <SectionHero />
        </div>

        {/* 2 — the sentence poses the problem, the three moves answer it.
            One screen, because splitting them put a scroll between a question
            and its answer. */}
        <div data-strings="off">
          <SectionDescription />
        </div>

        {/* 3 */}
        <div>
          <SectionDemo />
        </div>

        {/* 4 — letting someone run it is worth more than describing it.

            The only block that is longer than one screen, and it has to be:
            it pins itself and spends that scroll moving the clip. `data-stops`
            are the cue fractions from lib/cues.ts, so a gesture lands on a
            moment the agent did something rather than on an arbitrary
            screenful — see ScrollController.

            Strings off, and it carries its own opaque background: this is the
            one screen with fine detail and a moving control on it, and
            drifting lines behind a timeline is noise exactly where precision
            is wanted. */}
        <div data-strings="off" data-stops="0,0.26,0.45,0.68,0.92,1">
          <SectionTryIt />
        </div>

        {/* 5 — the screen that decides whether this reads as an agent or as a
            shuffle button, so it shows the mechanism rather than claiming it. */}
        <div>
          <SectionPipeline />
        </div>

        {/* 6 */}
        <div>
          <SectionResults />
        </div>

        {/* 7 — strings out; the one screen anybody reads at length. */}
        <div data-strings="off">
          <SectionFAQ />
        </div>
      </main>
    </>
  );
}
