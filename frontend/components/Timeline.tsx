"use client";

import { momentTime, stamp, type Session } from "@/lib/types";

/**
 * Where each song lands in the footage.
 *
 * TODO(team): mark queue vs interrupt differently, and show the song title on
 * hover rather than only in the tooltip.
 */
export default function Timeline({
  session,
  current,
  onSeek,
}: {
  session: Session;
  current: number;
  onSeek: (t: number) => void;
}) {
  const times = session.moments.map(momentTime);
  const duration = Math.max(...times, current, 1) * 1.05;

  return (
    <div className="mt-4">
      <div className="relative h-10 rounded-lg border border-line bg-surface-1">
        <div
          className="absolute top-0 h-full w-px bg-ink-primary/60"
          style={{ left: `${(current / duration) * 100}%` }}
        />
        {session.moments.map((m, i) => {
          const t = momentTime(m);
          const isInterrupt = m.played?.mode === "interrupt";
          return (
            <button
              key={i}
              onClick={() => onSeek(t)}
              title={`${stamp(t)} — ${m.chosen?.title ?? "?"}`}
              aria-label={`Jump to ${stamp(t)}, ${m.chosen?.title ?? "unknown"}`}
              className="absolute top-1/2 h-3 w-3 -translate-x-1/2 -translate-y-1/2
                         rounded-full ring-2 ring-surface-1 transition hover:scale-150"
              style={{
                left: `${(t / duration) * 100}%`,
                background: isInterrupt ? "#d95926" : "#3987e5",
              }}
            />
          );
        })}
      </div>
      <div className="mt-2 flex gap-4 text-xs text-ink-muted">
        <span className="flex items-center gap-1.5">
          <i className="h-2 w-2 rounded-full bg-scene" /> queued
        </span>
        <span className="flex items-center gap-1.5">
          <i className="h-2 w-2 rounded-full bg-target" /> cut in
        </span>
        <span className="ml-auto font-mono">
          {stamp(current)} · {session.moment_count} decisions
        </span>
      </div>
    </div>
  );
}
