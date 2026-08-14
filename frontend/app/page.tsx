import SectionAd from "@/components/SectionAd";
import SectionBuild from "@/components/SectionBuild";
import SectionDepth from "@/components/SectionDepth";
import SectionFilm from "@/components/SectionFilm";
import SectionLearned from "@/components/SectionLearned";
import SectionNext from "@/components/SectionNext";
import SectionProduct from "@/components/SectionProduct";
import SectionTryIt from "@/components/SectionTryIt";
import Wordmark from "@/components/Wordmark";
import { brand } from "@/lib/brand";

/**
 * The launch page. Seven sections, no navbar.
 *
 * Each one answers a Devpost field without ever using its heading — the copy
 * satisfies the form when pasted in, but the page reads as a product launch
 * rather than a report. "Challenges we ran into" as a headline breaks the
 * deadpan instantly; "A useless product, built properly" says the same thing
 * and stays in character.
 *
 *   1  SectionAd       Inspiration
 *   2  SectionProduct  What it does          (+ SectionTryIt — poke it yourself)
 *   3  SectionBuild    How we built it
 *   4  SectionDepth    Challenges we ran into
 *   5  SectionFilm     Accomplishments we're proud of
 *   6  SectionLearned  What we learned
 *   7  SectionNext     What's next
 *
 * The film gets a screen to itself, and it sits AFTER the two sections that
 * explain the machinery. That ordering is deliberate and it is the one most
 * hackathon pages get backwards: a demo video shown first is a claim, and a
 * demo video shown after the explanation is proof. By the time it plays, a
 * judge already knows what should have happened — so watching it not happen
 * is the payoff rather than the setup.
 *
 * Seven is the ceiling, not a target. Every extra screen costs pacing, and
 * this layout only works because each one holds a single idea. If something
 * new has to go in, something already here comes out.
 *
 * Cut on purpose: SectionLogo and SectionFAQ. Both are good, neither survives
 * the seven-section budget — the FAQ's best answer (why the cruelty dial was
 * removed) now lives in SectionLearned, where it was always stronger.
 */
export default function Home() {
  return (
    <>
      {/* No navbar. One product, one page — a nav would only offer to take
          you away from the single thing we want you to read. */}
      <header className="fixed left-0 top-0 z-50 p-6">
        <Wordmark size="nav" />
      </header>

      <main>
        <SectionAd />

        {/* "Try it yourself" sits with "what it does", not with the film.
            Reading a capability and immediately poking it is one thought;
            splitting them makes the reader wait for permission. */}
        <SectionProduct />
        <SectionTryIt />

        <SectionBuild />
        <SectionDepth />

        {/* The film, alone on a screen. Nothing above or beside it — this is
            the one moment the page stops arguing and just shows you. */}
        <SectionFilm />

        <SectionLearned />
        <SectionNext />
      </main>

      <footer className="border-t border-line px-6 py-10 text-center">
        <p className="text-xs text-ink-muted">
          {brand.name} — {brand.description}
        </p>
      </footer>
    </>
  );
}
