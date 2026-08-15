import ScrollController from "@/components/ScrollController";
import SectionDemo from "@/components/SectionDemo";
import SectionDescription from "@/components/SectionDescription";
import SectionFAQ from "@/components/SectionFAQ";
import SectionHero from "@/components/SectionHero";
import SectionPipeline from "@/components/SectionPipeline";
import SectionResults from "@/components/SectionResults";
import SectionTryIt from "@/components/SectionTryIt";

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

      <main>
        {/* 1 */}
        <div>
          <SectionHero />
        </div>

        {/* 2 — the claim, then two worked examples that flood in from
            opposite sides. Pinned, so it is longer than one screen: the stops
            are the beats, and both examples are real recorded output. */}
        <div data-stops="0,0.5,1">
          <SectionDescription />
        </div>

        {/* 3 */}
        <div>
          <SectionDemo />
        </div>

        {/* 4 — letting someone run it is worth more than describing it.

            The only block that is longer than one screen, and it has to be:
            it pins itself and spends that scroll moving the clip. `data-stops`
            are the moments the agent did something, so a gesture lands on a
            decision rather than on an arbitrary screenful — see
            ScrollController. Three of them, because the recorded run in
            public/sessions/sample.json contains exactly one decision: the read,
            the commit five seconds later, and the end of the clip.

            It carries its own opaque background because this is the one screen
            with fine detail and a moving control on it. */}
        <div data-stops="0,0.2,1">
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

        {/* 7 — the one screen anybody reads at length. */}
        <div>
          <SectionFAQ />
        </div>
      </main>
    </>
  );
}
