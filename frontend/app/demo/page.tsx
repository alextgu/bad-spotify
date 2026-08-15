"use client";

import { useEffect, useRef, useState } from "react";
import MomentCard from "@/components/MomentCard";
import Timeline from "@/components/Timeline";
import { activeMomentIndex, loadSession } from "@/lib/session";
import type { Session } from "@/lib/types";

const API_URL =
  process.env.NEXT_PUBLIC_BADSPOTIFY_API_URL ?? "http://127.0.0.1:8420";

export default function DemoPage() {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [session, setSession] = useState<Session | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [processing, setProcessing] = useState(false);
  const [videoUrl, setVideoUrl] = useState("/videos/sample.mp4");
  const [t, setT] = useState(0);
  const [videoBroken, setVideoBroken] = useState(false);

  useEffect(() => {
    loadSession()
      .then(setSession)
      .catch((e: Error) => setError(e.message));
  }, []);

  useEffect(() => {
    return () => {
      if (videoUrl.startsWith("blob:")) URL.revokeObjectURL(videoUrl);
    };
  }, [videoUrl]);

  async function analyze(file: File) {
    if (file.size > 200 * 1024 * 1024) {
      setError("Choose a video smaller than 200 MB.");
      return;
    }

    setError(null);
    setProcessing(true);
    setVideoBroken(false);
    setSession(null);
    setT(0);
    setVideoUrl(URL.createObjectURL(file));

    const form = new FormData();
    form.append("file", file);

    try {
      const response = await fetch(`${API_URL}/api/analyze-video`, {
        method: "POST",
        body: form,
      });
      const body = (await response.json()) as Session | { detail?: string };
      if (!response.ok) {
        const message = "detail" in body ? body.detail : null;
        throw new Error(message || "The video could not be analyzed.");
      }
      setSession(body as Session);
      videoRef.current?.load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "The video could not be analyzed.");
    } finally {
      setProcessing(false);
    }
  }

  async function restoreSample() {
    setError(null);
    setProcessing(false);
    setT(0);
    setVideoBroken(false);
    setVideoUrl("/videos/sample.mp4");
    try {
      setSession(await loadSession());
      videoRef.current?.load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "The sample could not be loaded.");
    }
  }

  const active = session ? activeMomentIndex(session, t) : -1;
  const moment = session && active >= 0 ? session.moments[active] : null;

  return (
    // The landing page moved to paper; this one has not been redesigned yet,
    // so it carries its own dark surface rather than inheriting the body's.
    // When /demo is reworked, this and the LEGACY block in tailwind.config.ts
    // go together.
    <main className="relative h-dvh overflow-hidden bg-plane text-ink-primary">
      <video
        ref={videoRef}
        className="absolute inset-0 h-full w-full object-cover"
        controls
        playsInline
        src={videoUrl}
        onTimeUpdate={(event) => setT(event.currentTarget.currentTime)}
        onSeeked={(event) => setT(event.currentTarget.currentTime)}
        onError={() => setVideoBroken(true)}
      />

      <div className="pointer-events-none absolute inset-0 bg-gradient-to-t from-black/75 via-transparent to-black/55" />

      <div className="pointer-events-none absolute inset-0 z-10 flex flex-col">
        <header className="pointer-events-auto flex flex-col gap-4 px-6 py-5 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <h1 className="text-xl font-semibold tracking-tight">Demo ground</h1>
            <p className="mt-1 text-sm text-ink-muted">
              Upload a video. The local model reads its mood every five seconds.
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <label className="cursor-pointer rounded-lg bg-white px-4 py-2 text-sm font-medium text-black transition duration-interaction ease-brand hover:bg-white/85">
              {processing ? "Analyzing video..." : "Choose video"}
              <input
                className="hidden"
                type="file"
                accept="video/mp4,video/webm,video/quicktime,video/x-msvideo,video/x-matroska"
                disabled={processing}
                onChange={(event) => {
                  const file = event.target.files?.[0];
                  if (file) void analyze(file);
                  event.currentTarget.value = "";
                }}
              />
            </label>
            <button
              type="button"
              onClick={() => void restoreSample()}
              disabled={processing}
              className="rounded-lg border border-strong px-4 py-2 text-sm text-ink-secondary transition duration-interaction ease-brand hover:border-white/30 hover:text-white disabled:opacity-50"
            >
              Use sample
            </button>
          </div>
        </header>

        {processing && (
          <div className="pointer-events-auto mx-6 mb-4 rounded-lg border border-scene/40 bg-scene/10 p-4 text-sm text-ink-secondary">
            Reading frames, audio, colour, and movement. The first run also
            downloads the local model.
          </div>
        )}

        {error && (
          <div className="pointer-events-auto mx-6 mb-4 rounded-lg border border-critical/40 bg-critical/10 p-4 text-sm">
            {error}
          </div>
        )}

        <div className="flex min-h-0 flex-1 flex-col justify-end lg:flex-row lg:items-end lg:justify-end">
          <div className="pointer-events-auto max-h-[45%] w-full overflow-y-auto px-6 pb-2 lg:max-h-full lg:w-[24rem] lg:shrink-0">
            {moment ? (
              <MomentCard moment={moment} />
            ) : (
              <div className="rounded-xl border border-subtle bg-surface-1 p-6 text-sm text-ink-muted">
                {processing
                  ? "The first mood card will appear when analysis finishes."
                  : "Choose a video or press play on the sample."}
              </div>
            )}
          </div>
        </div>

        <div className="pointer-events-auto px-6 pb-16">
          {videoBroken && (
            <p className="mb-2 text-sm text-ink-muted">
              This browser could not play the video codec. The mood timeline is
              still available below.
            </p>
          )}

          {session && session.moments.length > 0 && (
            <Timeline
              session={session}
              current={t}
              onSeek={(time) => {
                setT(time);
                if (videoRef.current) videoRef.current.currentTime = time;
              }}
            />
          )}

          {session?.model && (
            <p className="mt-3 font-mono text-xs text-ink-muted">
              {session.model} · one frame every {session.sample_interval_s ?? 5}s ·{" "}
              {session.moment_count} mood reads
            </p>
          )}
        </div>
      </div>
    </main>
  );
}
