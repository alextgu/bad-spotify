import { CLIPS } from "@/lib/clips";

/**
 * Section 5 — the film. A screen to itself.
 *
 * One uninterrupted watch-it-happen. No cards, no annotation, nothing beside
 * it. By the time this plays the page has already explained the machinery, so
 * the video is proof rather than a claim — the judge knows what should have
 * happened and gets to watch it not happen.
 *
 * Full-bleed on purpose: this is the only section that isn't argument.
 *
 * TODO(team): this currently points at the placeholder clip. Swap in the real
 * demo film — with the music overlaid onto the footage, which is the decision
 * that sidesteps licensing and live playback entirely.
 */
export default function SectionFilm() {
  const clip = CLIPS[0];

  return (
    <section
      id="film"
      className="flex min-h-screen flex-col justify-center px-6 py-32"
    >
      <div className="mx-auto w-full max-w-5xl">
        <h2 className="text-[clamp(1.75rem,4vw,3rem)] font-semibold tracking-[-0.035em]">
          Watch it ruin a moment.
        </h2>
        <p className="mt-4 max-w-xl text-ink-muted">
          One run, start to finish, with what it played overlaid. Everything you
          hear was chosen by the agent while the footage was happening.
        </p>

        <video
          className="mt-10 w-full rounded-xl border border-line bg-surface-1"
          controls
          playsInline
          preload="metadata"
          src={clip.video}
        />

        {clip.placeholder && (
          <p className="mt-4 text-sm text-target">
            Placeholder footage — the real film hasn’t been shot yet.
          </p>
        )}
      </div>
    </section>
  );
}
