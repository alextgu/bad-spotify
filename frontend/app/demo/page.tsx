"use client";

import { useEffect, useRef, useState } from "react";
import MomentCard from "@/components/MomentCard";
import Timeline from "@/components/Timeline";
import { activeMomentIndex, loadSession } from "@/lib/session";
import type { Session } from "@/lib/types";

/**
 * The demo ground.
 *
 * Plays the sample video and pops up what the agent chose, in sync, at the
 * point in the footage where it actually landed. No backend: it reads a
 * recorded session file produced by
 *
 *     python run.py --video clip.mp4 --record sample
 *
 * TODO(team):
 *   - drop the real sample video at public/videos/sample.mp4
 *   - drag-and-drop your own video (for now it falls back to the sample)
 *   - decide whether to show the losing candidates too
 */
export default function DemoPage() {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [session, setSession] = useState<Session | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [t, setT] = useState(0);
  const [videoBroken, setVideoBroken] = useState(false);

  useEffect(() => {
    loadSession()
      .then(setSession)
      .catch((e: Error) => setError(e.message));
  }, []);

  const active = session ? activeMomentIndex(session, t) : -1;
  const moment = session && active >= 0 ? session.moments[active] : null;

  return (
    <main className="mx-auto max-w-6xl px-6 py-12">
      <header className="mb-8 flex items-baseline gap-3">
        <h1 className="text-xl font-semibold tracking-tight">Demo ground</h1>
        <p className="text-sm text-ink-muted">
          Watch it ruin a moment, and see why it chose what it chose.
        </p>
      </header>

      {error && (
        <div className="rounded-lg border border-critical/40 bg-critical/10 p-4 text-sm">
          {error}
        </div>
      )}

      <div className="grid gap-6 lg:grid-cols-[1.4fr_1fr]">
        <div>
          <video
            ref={videoRef}
            className="w-full rounded-xl border border-white/10 bg-surface-1"
            controls
            playsInline
            src="/videos/sample.mp4"
            onTimeUpdate={(e) => setT(e.currentTarget.currentTime)}
            onSeeked={(e) => setT(e.currentTarget.currentTime)}
            onError={() => setVideoBroken(true)}
          />

          {videoBroken && (
            <p className="mt-2 text-sm text-ink-muted">
              The video didn&apos;t load, but the decisions still work — click a
              dot on the timeline. (Codec support varies by browser; H.264 is
              the safe bet.)
            </p>
          )}
          {session && (
            <Timeline
              session={session}
              current={t}
              onSeek={(time) => {
                // Drive our own state first. If the video is missing or the
                // browser can't decode it, the walkthrough still works --
                // the cards are the point, the footage is context.
                setT(time);
                if (videoRef.current) {
                  try {
                    videoRef.current.currentTime = time;
                  } catch {
                    /* not loaded yet; the card is already showing */
                  }
                }
              }}
            />
          )}
        </div>

        <div>
          {moment ? (
            <MomentCard moment={moment} />
          ) : (
            <div className="rounded-xl border border-white/10 bg-surface-1 p-6 text-sm text-ink-muted">
              Press play. Cards appear as the agent makes decisions.
            </div>
          )}
        </div>
      </div>
    </main>
  );
}
