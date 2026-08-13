import Link from "next/link";

/**
 * Landing page.
 *
 * TODO(team): this is a skeleton. What it needs:
 *   - the pipeline diagram (see components/PipelineDiagram.tsx)
 *   - a couple of example moments as a teaser
 *   - whatever framing we want judges to read first
 */
export default function Home() {
  return (
    <main className="mx-auto max-w-3xl px-6 py-24">
      <h1 className="text-5xl font-semibold tracking-tight">bad spotify</h1>

      <p className="mt-6 text-lg text-ink-secondary">
        A wearable agent whose only feature is playing the worst possible music
        for the moment. It watches what is around you, works out what the moment
        feels like, computes the opposite, and plays that. It talks to you, but
        only to announce what it has done.
      </p>

      <div className="mt-10 space-y-2 font-mono text-sm text-ink-muted">
        <p>sunlit park, people reading → Drowning Pool, <em>Bodies</em></p>
        <p>toddler&apos;s birthday party → Johnny Cash, <em>Hurt</em></p>
        <p>silent library during exams → Darude, <em>Sandstorm</em></p>
      </div>

      <Link
        href="/demo"
        className="mt-12 inline-block rounded-lg bg-scene px-5 py-3 font-semibold
                   text-white transition hover:brightness-110"
      >
        See it work →
      </Link>

      <p className="mt-16 border-t border-white/10 pt-6 text-sm text-ink-muted">
        TODO(team): pipeline diagram goes here.
      </p>
    </main>
  );
}
