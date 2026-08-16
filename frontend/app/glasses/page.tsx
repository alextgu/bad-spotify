import type { Metadata } from "next";
import Link from "next/link";
import MetaGlassesSetup from "@/components/MetaGlassesSetup";

export const metadata: Metadata = {
  title: "Meta glasses live — Slopify",
  description: "Connect the native Meta glasses companion to Slopify.",
};

export default function GlassesPage() {
  return (
    <main className="min-h-svh bg-bone px-gutter py-10 text-ink sm:py-16">
      <div className="mx-auto max-w-content">
        <Link
          href="/#try"
          aria-label="Back to video demo"
          className="font-mono text-label uppercase text-graphite transition hover:text-ink"
        >
          ← Video demo
        </Link>

        <header className="mx-auto mt-16 max-w-[48rem] text-center">
          <h1 className="font-display text-headline">Meta glasses · live</h1>
          <p className="mx-auto mt-block max-w-measure-sub text-body text-graphite">
            This surface only handles the native glasses companion. Video samples and uploads
            stay in the separate video demo.
          </p>
        </header>

        <MetaGlassesSetup />
      </div>
    </main>
  );
}
