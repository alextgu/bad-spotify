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
    <main className="mx-auto max-w-6xl px-6 py-12">
      <header className="mb-8 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h1 className="text-xl font-semibold tracking-tight">Demo ground</h1>
          <p className="mt-1 text-sm text-ink-muted">
            Upload a video. The local model reads its mood every five seconds.
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <label className="cursor-pointer rounded-lg bg-white px-4 py-2 text-sm font-medium text-black transition hover:bg-white/85">
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
            className="rounded-lg border border-white/15 px-4 py-2 text-sm text-ink-secondary transition hover:border-white/30 hover:text-white disabled:opacity-50"
          >
            Use sample
          </button>
        </div>
      </header>

      {processing && (
        <div className="mb-6 rounded-lg border border-scene/40 bg-scene/10 p-4 text-sm text-ink-secondary">
          Reading frames, audio, colour, and movement. The first run also
          downloads the local model.
        </div>
      )}

      {error && (
        <div className="mb-6 rounded-lg border border-critical/40 bg-critical/10 p-4 text-sm">
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
            src={videoUrl}
            onTimeUpdate={(event) => setT(event.currentTarget.currentTime)}
            onSeeked={(event) => setT(event.currentTarget.currentTime)}
            onError={() => setVideoBroken(true)}
          />

          {videoBroken && (
            <p className="mt-2 text-sm text-ink-muted">
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

        <div>
          {moment ? (
            <MomentCard moment={moment} />
          ) : (
            <div className="rounded-xl border border-white/10 bg-surface-1 p-6 text-sm text-ink-muted">
              {processing
                ? "The first mood card will appear when analysis finishes."
                : "Choose a video or press play on the sample."}
            </div>
          )}
        </div>
      </div>
    </main>
  );
}
