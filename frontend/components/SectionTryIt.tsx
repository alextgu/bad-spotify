import Label from "@/components/Label";
import Reveal from "@/components/Reveal";
import Screen from "@/components/Screen";
import { tryIt } from "@/lib/site";

/**
 * 4 — hand it over.
 *
 * The whole screen is one link. Letting someone run it themselves is worth
 * more than any amount of describing it, so this screen does as little as
 * possible on the way to the button.
 *
 * `/demo` is a real route in this app, not a promise: it takes a video, reads
 * its mood every few seconds and returns the track it would have played. It
 * also ships a sample, so the link works on a machine with nothing configured
 * — which matters, because the one thing worse than not offering this is
 * offering it and having it fail in front of someone.
 */
export default function SectionTryIt() {
  return (
    <Screen id="try">
      <div className="mx-auto w-full max-w-content text-center">
        <Reveal>
          <Label tone="offset" className="block">
            Try it
          </Label>
          <h2 className="mx-auto mt-block max-w-[16ch] font-display text-headline">
            {tryIt.title}
          </h2>
          <p className="mx-auto mt-block max-w-measure-sub text-body text-graphite">
            {tryIt.body}
          </p>
        </Reveal>

        <Reveal delay={0.12}>
          <a
            href={tryIt.action.href}
            className="mt-section-sm inline-flex items-center gap-3 rounded-full bg-ink px-9 py-4
                       font-mono text-label uppercase text-paper transition-[transform,background-color]
                       duration-interaction ease-calm hover:-translate-y-0.5 hover:bg-offset-ink"
          >
            {tryIt.action.label}
            <span aria-hidden>→</span>
          </a>

          <p className="mx-auto mt-rest max-w-measure-sub text-caption text-graphite">
            {tryIt.note}
          </p>
        </Reveal>
      </div>
    </Screen>
  );
}
