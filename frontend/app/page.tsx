import SectionAd from "@/components/SectionAd";
import SectionBuild from "@/components/SectionBuild";
import SectionDepth from "@/components/SectionDepth";
import SectionFAQ from "@/components/SectionFAQ";
import SectionFilm from "@/components/SectionFilm";
import SectionLearned from "@/components/SectionLearned";
import SectionNext from "@/components/SectionNext";
import SectionProduct from "@/components/SectionProduct";
import PlaceholderBanner from "@/components/PlaceholderBanner";
import SectionTryIt from "@/components/SectionTryIt";
import Wordmark from "@/components/Wordmark";
import { brand } from "@/lib/brand";

/**
 * The launch page. Seven sections, no navbar.
 *
 * Ordered the way a product page is ordered, not the way a submission form is.
 * Every Devpost field is still answered — inspiration, what it does, how we
 * built it, challenges, accomplishments, what we learned, what's next — but
 * the page never uses those headings. "Challenges we ran into" as a headline
 * breaks the deadpan instantly; "A useless product, built properly" says the
 * same thing and stays in character.
 *
 *   1  Ad          the pitch                      → Inspiration
 *   2  Film        watch it happen                → the hook
 *   3  Product     what it actually does          → What it does
 *   4  Build+TryIt how, in detail, and proof      → How we built it / Accomplishments
 *   5  Depth+Learn what was hard, what we changed → Challenges / What we learned
 *   6  Next        the ask                        → What's next
 *   7  FAQ         the awkward questions
 *
 * The film sits at 2, before anything is explained. That is the opposite of
 * how a technical writeup should be ordered — there, a video is proof and
 * belongs after the argument. Here it is the hook, and an ad that explains
 * before it shows has already lost the reader. Nobody watches a product film
 * because they were persuaded to.
 *
 * Seven is a ceiling, not a target. This layout only works because each screen
 * holds one idea, so if something new goes in, something here comes out.
 */
export default function Home() {
  return (
    <>
      {/* No navbar. One product, one page — navigation would only offer to
          take you away from the single thing we want you to read. */}
      <header className="fixed left-0 top-0 z-50 p-6">
        <Wordmark size="nav" />
      </header>

      <main>
        {/* 1 — the pitch. */}
        <SectionAd />

        {/* 2 — the hook. Show it before explaining a thing. */}
        <SectionFilm />

        {/* 3 — now that they've seen it, what it is. */}
        <SectionProduct />

        {/* 4 — how, in detail, and then the part they can poke. Letting them
            run it themselves is the accomplishment; saying so would be worth
            much less than handing it over. */}
        <SectionBuild />
        <SectionTryIt />

        {/* 5 — what was hard, and what we got wrong. Kept adjacent on purpose:
            one is decisions we'd defend, the other is decisions we reversed. A
            page with only the first reads as marketing. */}
        <SectionDepth />
        <SectionLearned />

        {/* 6 — the ask. */}
        <SectionNext />

        {/* 7 — the questions a sceptical judge is already forming. */}
        <SectionFAQ />
      </main>

      {/* Dev-only. Renders nothing in production, and nothing once the real
          footage is in — see lib/clips.ts. */}
      <PlaceholderBanner />

      <footer className="border-t border-subtle px-6 py-10 text-center">
        <p className="text-xs text-ink-muted">
          {brand.name} — {brand.description}
        </p>
      </footer>
    </>
  );
}
