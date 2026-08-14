import Link from "next/link";
import Reveal from "@/components/Reveal";
import Wordmark from "@/components/Wordmark";
import { brand, specs, steps } from "@/lib/brand";

/**
 * The launch page.
 *
 * Deliberately restrained: one idea per screen, a lot of empty space, and no
 * decoration that isn't carrying meaning. The product is absurd — so the
 * presentation plays it completely straight. The gap between how seriously
 * this page takes itself and what it's actually announcing is the joke.
 *
 * Don't add: gradients on text, more than one accent colour, icons on
 * everything, or a second call to action. Every one of those makes it read as
 * a hackathon page instead of a product.
 */
export default function Home() {
  return (
    <>
      {/* ---------------------------------------------------------- nav -- */}
      <nav className="fixed inset-x-0 top-0 z-50 border-b border-white/[0.06]
                      bg-plane/70 backdrop-blur-xl">
        <div className="mx-auto flex h-12 max-w-5xl items-center px-6">
          <Wordmark size="nav" />
          <div className="flex-1" />
          <Link
            href="/demo"
            className="text-sm text-ink-secondary transition hover:text-white"
          >
            Watch it work
          </Link>
        </div>
      </nav>

      {/* -------------------------------------------------------- hero -- */}
      <section className="flex min-h-screen flex-col items-center justify-center px-6 text-center">
        <Reveal>
          <p className="mb-6 text-sm tracking-[0.2em] text-ink-muted uppercase">
            {brand.eyebrow}
          </p>
        </Reveal>

        <Reveal delay={120}>
          <h1>
            <Wordmark />
          </h1>
        </Reveal>

        <Reveal delay={260}>
          <p className="mt-10 max-w-xl text-[clamp(1.25rem,2.6vw,1.75rem)]
                        leading-snug tracking-[-0.02em] text-ink-secondary">
            {brand.tagline}
            <br />
            <span className="text-ink-muted">{brand.taglineSecond}</span>
          </p>
        </Reveal>

        <Reveal delay={420}>
          <Link
            href="/demo"
            className="mt-14 inline-flex items-center gap-2 rounded-full border
                       border-white/15 px-7 py-3 text-sm text-white transition
                       hover:border-white/40 hover:bg-white/[0.04]"
          >
            Watch it work
            <span aria-hidden>→</span>
          </Link>
        </Reveal>
      </section>

      {/* ------------------------------------------------------- creed -- */}
      <section className="flex min-h-[85vh] items-center justify-center px-6">
        <div className="space-y-3 text-center">
          {brand.creed.map((line, i) => (
            <Reveal key={line} delay={i * 220}>
              <p
                className={`text-[clamp(1.75rem,5.5vw,4rem)] font-medium leading-[1.1]
                            tracking-[-0.035em] ${
                              i === brand.creed.length - 1
                                ? "text-white"
                                : "text-ink-muted"
                            }`}
              >
                {line}
              </p>
            </Reveal>
          ))}
        </div>
      </section>

      {/* ------------------------------------------------------- steps -- */}
      <section className="mx-auto max-w-5xl px-6 py-40">
        <Reveal>
          <h2 className="text-[clamp(1.75rem,4vw,3rem)] font-semibold
                         tracking-[-0.035em]">
            How it ruins a moment.
          </h2>
          <p className="mt-4 max-w-md text-ink-muted">
            Six steps, about every five seconds, for as long as you leave it on.
          </p>
        </Reveal>

        <div className="mt-20 grid gap-x-12 gap-y-14 sm:grid-cols-2 lg:grid-cols-3">
          {steps.map((s, i) => (
            <Reveal key={s.n} delay={(i % 3) * 120}>
              <div className="border-t border-white/10 pt-5">
                <p className="font-mono text-xs text-ink-muted">{s.n}</p>
                <h3 className="mt-3 text-xl font-medium tracking-[-0.02em]">
                  {s.title}
                </h3>
                <p className="mt-2 text-[15px] leading-relaxed text-ink-secondary">
                  {s.body}
                </p>
              </div>
            </Reveal>
          ))}
        </div>
      </section>

      {/* -------------------------------------------------- the method -- */}
      <section className="mx-auto max-w-3xl px-6 py-40 text-center">
        <Reveal>
          <p className="text-[clamp(1.4rem,3.4vw,2.25rem)] font-medium
                        leading-[1.35] tracking-[-0.03em]">
            Anything can compute an opposite. Almost nothing knows that the
            opposite of a sunlit park is{" "}
            <span className="text-target">funeral doom</span> — or that a
            Christmas song in August is worse than either.
          </p>
        </Reveal>
        <Reveal delay={200}>
          <p className="mx-auto mt-8 max-w-lg text-ink-muted">
            So the maths makes a shortlist, and taste picks the winner. Neither
            one works alone.
          </p>
        </Reveal>
      </section>

      {/* ------------------------------------------------------- specs -- */}
      <section className="mx-auto max-w-5xl px-6 pb-40">
        <div className="grid grid-cols-2 gap-y-14 border-y border-white/10 py-16
                        lg:grid-cols-4">
          {specs.map((s, i) => (
            <Reveal key={s.label} delay={i * 100}>
              <div className="px-2 text-center">
                <p className="text-[clamp(2rem,5vw,3.25rem)] font-semibold
                              tracking-[-0.04em]">
                  {s.value}
                </p>
                <p className="mt-2 text-sm leading-snug text-ink-muted">
                  {s.label}
                </p>
              </div>
            </Reveal>
          ))}
        </div>
      </section>

      {/* --------------------------------------------------------- cta -- */}
      <section className="flex min-h-[70vh] flex-col items-center justify-center
                          px-6 text-center">
        <Reveal>
          <h2 className="text-[clamp(2rem,6vw,4.5rem)] font-semibold
                         leading-[1.05] tracking-[-0.04em]">
            See it read a room.
            <br />
            <span className="text-ink-muted">Then watch it ignore one.</span>
          </h2>
        </Reveal>
        <Reveal delay={200}>
          <Link
            href="/demo"
            className="mt-12 inline-flex items-center gap-2 rounded-full bg-white
                       px-8 py-3.5 text-sm font-medium text-plane transition
                       hover:bg-white/90"
          >
            Watch it work
            <span aria-hidden>→</span>
          </Link>
        </Reveal>
      </section>

      <footer className="border-t border-white/[0.06] px-6 py-10 text-center">
        <p className="text-xs text-ink-muted">
          {brand.name} — {brand.description}
        </p>
      </footer>
    </>
  );
}
