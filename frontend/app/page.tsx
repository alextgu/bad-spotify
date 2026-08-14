import Link from "next/link";
import Reveal from "@/components/Reveal";
import SectionDepth from "@/components/SectionDepth";
import SectionFilm from "@/components/SectionFilm";
import SectionNext from "@/components/SectionNext";
import SectionProduct from "@/components/SectionProduct";
import SectionTryIt from "@/components/SectionTryIt";
import Wordmark from "@/components/Wordmark";
import { brand } from "@/lib/brand";

/**
 * The page, in six movements:
 *
 *   1. the launch          it's a product, played completely straight
 *   2. the product         what it is, what it does, what it's built on
 *   3. the film            watch it happen, uninterrupted
 *   4. try it yourself     preset clips, or bring your own
 *   5. the depth           why any of this was hard
 *   6. what's next         the roadmap, and the ask
 *
 * The order is the argument: laugh, understand, watch, poke at it, respect the
 * engineering, see where it goes. Don't reorder without a reason.
 *
 * UI is deliberately restrained scaffolding right now — structure first, the
 * visual pass comes after. Copy lives in `lib/brand.ts` and `lib/content.ts`.
 */
export default function Home() {
  return (
    <>
      {/* ---------------------------------------------------------- nav -- */}
      <nav className="fixed inset-x-0 top-0 z-50 border-b border-white/[0.06]
                      bg-plane/70 backdrop-blur-xl">
        <div className="mx-auto flex h-12 max-w-6xl items-center gap-6 px-6">
          <Wordmark size="nav" />
          <div className="flex-1" />
          {[
            ["Product", "#product"],
            ["Film", "#film"],
            ["Try it", "#try"],
            ["How", "#how"],
            ["Next", "#next"],
          ].map(([label, href]) => (
            <a
              key={href}
              href={href}
              className="hidden text-sm text-ink-secondary transition hover:text-white sm:block"
            >
              {label}
            </a>
          ))}
        </div>
      </nav>

      {/* --------------------------------------------- 1. the launch -- */}
      <section className="flex min-h-screen flex-col items-center justify-center px-6 text-center">
        <Reveal>
          <p className="mb-6 text-sm uppercase tracking-[0.2em] text-ink-muted">
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
          <div className="mt-14 flex flex-wrap items-center justify-center gap-3">
            <a
              href="#film"
              className="inline-flex items-center gap-2 rounded-full bg-white px-7 py-3
                         text-sm font-medium text-plane transition hover:bg-white/90"
            >
              Watch it work
              <span aria-hidden>→</span>
            </a>
            <a
              href="#try"
              className="inline-flex items-center gap-2 rounded-full border border-white/15
                         px-7 py-3 text-sm text-white transition hover:border-white/40"
            >
              Try it yourself
            </a>
          </div>
        </Reveal>

        <Reveal delay={560}>
          <div className="mt-24 space-y-1.5 text-center">
            {brand.creed.map((line, i) => (
              <p
                key={line}
                className={`text-sm ${
                  i === brand.creed.length - 1 ? "text-white" : "text-ink-muted"
                }`}
              >
                {line}
              </p>
            ))}
          </div>
        </Reveal>
      </section>

      {/* ------------------------------ 2. the product, rotating -- */}
      <SectionProduct />

      {/* ------------------------------------------------ 3. the film -- */}
      <SectionFilm />

      {/* --------------------------------------- 4. try it yourself -- */}
      <SectionTryIt />

      {/* ----------------------------------------------- 5. the depth -- */}
      <SectionDepth />

      {/* ---------------------------------------------- 6. what's next -- */}
      <SectionNext />

      <footer className="border-t border-white/[0.06] px-6 py-10 text-center">
        <p className="text-xs text-ink-muted">
          {brand.name} — {brand.description}
        </p>
        <p className="mt-2 text-xs text-ink-muted">
          <Link href="/demo" className="underline underline-offset-4 hover:text-white">
            the full decision replay
          </Link>
        </p>
      </footer>
    </>
  );
}
