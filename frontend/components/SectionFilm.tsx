import SectionHeading from "@/components/SectionHeading";
import BlurFade from "@/components/BlurFade";
import HeroVideoDialog from "@/components/HeroVideoDialog";
import { FILM } from "@/lib/clips";

/**
 * Section 2 — the film. A screen to itself, immediately after the pitch.
 *
 * One uninterrupted watch-it-happen. No cards, no annotation, nothing beside
 * it, and nothing explained yet. An ad that explains before it shows has
 * already lost the reader — nobody watches a product film because they were
 * persuaded to. The explaining starts on the next screen, once they have
 * something to attach it to.
 *
 * The player is a poster that expands, not a bare `<video controls>`. Browser
 * chrome and a grey rectangle at the most important point on the page is one
 * of the loudest tells that a page wasn't designed — and a still gives the
 * caption somewhere to land before anyone presses play.
 *
 * TODO(team): this currently points at the placeholder clip. Swap in the real
 * demo film — with the music overlaid onto the footage, which is the decision
 * that sidesteps licensing and live playback entirely.
 */
export default function SectionFilm() {
  const clip = FILM;

  return (
    <section
      id="film"
      className="flex min-h-screen flex-col justify-center px-6 py-section-sm md:py-section"
    >
      <div className="mx-auto w-full max-w-content">
        <BlurFade>
          <SectionHeading
          index={1}
          label="THE FILM"
          lead="Watch it ruin"
          trail="a moment."
        />
        </BlurFade>

        <BlurFade delay={0.08}>
          <p className="mt-heading-sub max-w-measure-sub text-body text-ink-muted">
            One run, start to finish, with what it played overlaid. Everything
            you hear was chosen by the agent while the footage was happening.
          </p>
        </BlurFade>

        <BlurFade delay={0.16}>
          <HeroVideoDialog
            className="mt-sub-content"
            src={clip.video}
            caption="One run, uninterrupted."
            subcaption={
              clip.placeholder
                ? "Placeholder footage — the real film hasn’t been shot yet"
                : "Press play"
            }
          />
        </BlurFade>
      </div>
    </section>
  );
}
