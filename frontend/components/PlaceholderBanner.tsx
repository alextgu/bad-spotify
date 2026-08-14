"use client";

import { placeholderClips } from "@/lib/clips";

/**
 * A development-only reminder of what is still fake.
 *
 * Renders nothing in a production build and nothing once the placeholder
 * flags are gone, so it costs the shipped site zero bytes and disappears the
 * moment the real footage lands.
 *
 * It exists because the film is now the SECOND thing a judge sees. A green
 * test pattern in that position is the single most expensive mistake this
 * page can make, and "someone will remember to swap it" is not a plan on the
 * morning of a demo.
 *
 * Deliberately ugly. A tasteful notice gets ignored.
 */
export default function PlaceholderBanner() {
  if (process.env.NODE_ENV === "production") return null;

  const outstanding = placeholderClips();
  if (outstanding.length === 0) return null;

  return (
    <div
      role="status"
      className="fixed bottom-4 left-1/2 z-[100] w-[min(92vw,44rem)] -translate-x-1/2
                 rounded-lg border border-target bg-plane/95 px-4 py-3
                 font-mono text-xs text-target shadow-xl backdrop-blur"
    >
      <p className="font-bold">
        {outstanding.length} placeholder asset
        {outstanding.length === 1 ? "" : "s"} still on this page — dev only
      </p>
      <ul className="mt-1.5 space-y-0.5 text-ink-muted">
        {outstanding.map((c) => (
          <li key={c.id}>
            {c.video} — {c.label}
          </li>
        ))}
      </ul>
      <p className="mt-2 text-ink-muted">
        Replace the file, then delete{" "}
        <span className="text-target">placeholder: true</span> in lib/clips.ts.
        This banner goes away on its own.
      </p>
    </div>
  );
}
