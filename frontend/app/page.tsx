import Link from "next/link";
import SectionAd from "@/components/SectionAd";
import SectionDepth from "@/components/SectionDepth";
import SectionFAQ from "@/components/SectionFAQ";
import SectionLogo from "@/components/SectionLogo";
import SectionFilm from "@/components/SectionFilm";
import SectionNext from "@/components/SectionNext";
import SectionProduct from "@/components/SectionProduct";
import SectionTryIt from "@/components/SectionTryIt";
import Wordmark from "@/components/Wordmark";
import { brand } from "@/lib/brand";

/**
 * The page, in eight movements:
 *
 *   1. the advertisement   full-bleed product ad, played completely straight
 *   2. the mark            the orb, rippling, and slightly derpy
 *   3. the product         what it is, what it does, what it's built on
 *   4. the film            watch it happen, uninterrupted
 *   5. try it yourself     preset clips, or bring your own
 *   6. the depth           why any of this was hard
 *   7. what's next         the roadmap, and the ask
 *   8. the FAQ            the only section played completely straight
 *
 * The order is the argument: be sold it, meet it, understand it, watch it,
 * poke at it, respect the engineering, see where it goes. Don't reorder
 * without a reason.
 *
 * FRAMEWORK, NOT DESIGN. Sections 1 and 2 are structural placeholders with the
 * slots named in their own files. The look is a clean white high-tech
 * showcase; every colour comes from the tokens in app/globals.css, so the
 * visual pass is an edit there plus the two lead sections — not a rewrite of
 * everything below them. Copy lives in lib/brand.ts and lib/content.ts.
 */
export default function Home() {
  return (
    <>
      {/* ---------------------------------------------------------- nav -- */}
      <nav className="fixed inset-x-0 top-0 z-50 border-b border-line
                      bg-plane/80 backdrop-blur-xl">
        <div className="mx-auto flex h-12 max-w-6xl items-center gap-6 px-6">
          <Wordmark size="nav" />
          <div className="flex-1" />
          {[
            ["Meet it", "#logo"],
            ["Product", "#product"],
            ["Film", "#film"],
            ["Try it", "#try"],
            ["How", "#how"],
            ["Next", "#next"],
            ["FAQ", "#faq"],
          ].map(([label, href]) => (
            <a
              key={href}
              href={href}
              className="hidden text-sm text-ink-secondary transition hover:text-ink-primary sm:block"
            >
              {label}
            </a>
          ))}
        </div>
      </nav>

      {/* --------------------------------------- 1. the advertisement -- */}
      <SectionAd />

      {/* ---------------------------------------- 2. the mark, rippling -- */}
      <SectionLogo />

      {/* ------------------------------ 3. the product, rotating -- */}
      <SectionProduct />

      {/* ------------------------------------------------ 4. the film -- */}
      <SectionFilm />

      {/* --------------------------------------- 5. try it yourself -- */}
      <SectionTryIt />

      {/* ----------------------------------------------- 6. the depth -- */}
      <SectionDepth />

      {/* ---------------------------------------------- 7. what's next -- */}
      <SectionNext />

      {/* --------------------------------------------------- 8. the FAQ -- */}
      <SectionFAQ />

      <footer className="border-t border-line px-6 py-10 text-center">
        <p className="text-xs text-ink-muted">
          {brand.name} — {brand.description}
        </p>
        <p className="mt-2 text-xs text-ink-muted">
          <Link href="/demo" className="underline underline-offset-4 hover:text-ink-primary">
            the full decision replay
          </Link>
        </p>
      </footer>
    </>
  );
}
