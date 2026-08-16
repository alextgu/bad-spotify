"use client";

import { useEffect, useRef, useState } from "react";
import MomentCard from "@/components/MomentCard";
import Timeline from "@/components/Timeline";
import {
  playbackStatus,
  playTrack,
  stopPlayback,
  type PlaybackStatus,
} from "@/lib/playback";
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
  const [playback, setPlayback] = useState<PlaybackStatus | null>(null);
  const [checkingPlayback, setCheckingPlayback] = useState(true);
  const [playbackError, setPlaybackError] = useState<string | null>(null);
  const [nowPlaying, setNowPlaying] = useState<string | null>(null);
  const lastTrackRef = useRef<string | null>(null);
  const playbackGenerationRef = useRef(0);

  useEffect(() => {
    loadSession()
      .then(setSession)
      .catch((e: Error) => setError(e.message));
    void refreshPlayback();
  }, []);

  useEffect(() => {
    return () => {
      if (videoUrl.startsWith("blob:")) URL.revokeObjectURL(videoUrl);
    };
  }, [videoUrl]);

  async function refreshPlayback() {
    setCheckingPlayback(true);
    try {
      setPlayback(await playbackStatus(API_URL));
    } catch {
      setPlayback({
        backend: null,
        connected: false,
        message: "Start the local agent with run.py --serve.",
      });
    } finally {
      setCheckingPlayback(false);
    }
  }

  async function playMomentAt(videoTime: number) {
    if (!playback?.connected || !session) return;
    const index = activeMomentIndex(session, videoTime);
    const selected = index >= 0 ? session.moments[index] : null;
    const trackId = selected?.played?.track_id;
    if (!selected || !trackId || trackId === lastTrackRef.current) return;

    const generation = ++playbackGenerationRef.current;
    lastTrackRef.current = trackId;
    setPlaybackError(null);
    try {
      await playTrack(API_URL, trackId);
      if (generation === playbackGenerationRef.current) {
        setNowPlaying(
          `${selected.chosen?.title ?? "Selected song"}${
            selected.chosen?.artist ? ` — ${selected.chosen.artist}` : ""
          }`,
        );
      }
    } catch (e) {
      if (generation === playbackGenerationRef.current) {
        lastTrackRef.current = null;
        setNowPlaying(null);
        setPlaybackError(
          e instanceof Error ? e.message : "Spotify playback failed.",
        );
      }
    }
  }

  async function pauseSong() {
    if (!playback?.connected) return;
    ++playbackGenerationRef.current;
    lastTrackRef.current = null;
    setNowPlaying(null);
    try {
      await stopPlayback(API_URL);
    } catch (e) {
      setPlaybackError(
        e instanceof Error ? e.message : "Spotify playback could not be paused.",
      );
    }
  }

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
    void pauseSong();
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
      void refreshPlayback();
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
    void pauseSong();
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
        onTimeUpdate={(event) => {
          const time = event.currentTarget.currentTime;
          setT(time);
          if (!event.currentTarget.paused) void playMomentAt(time);
        }}
        onSeeked={(event) => {
          const time = event.currentTarget.currentTime;
          setT(time);
          if (!event.currentTarget.paused) void playMomentAt(time);
        }}
        onPlay={(event) => void playMomentAt(event.currentTarget.currentTime)}
        onPause={() => void pauseSong()}
        onEnded={() => void pauseSong()}
        onError={() => setVideoBroken(true)}
      />

      <div className="pointer-events-none absolute inset-0 bg-gradient-to-t from-black/75 via-transparent to-black/55" />

      <div className="pointer-events-none absolute inset-0 z-10 flex flex-col">
        <header className="pointer-events-auto flex flex-col gap-4 px-6 py-5 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <h1 className="text-xl font-semibold tracking-tight">Demo ground</h1>
            <p className="mt-1 text-sm text-ink-muted">
              Upload a video. The agent reads its mood every five seconds.
            </p>
            <div
              className={`mt-2 inline-flex max-w-full items-center gap-2 rounded-full border px-3 py-1 text-xs ${
                playback?.connected
                  ? "border-scene/40 bg-scene/10 text-ink-secondary"
                  : "border-strong bg-surface-1 text-ink-muted"
              }`}
            >
              <span
                className={`h-2 w-2 shrink-0 rounded-full ${
                  playback?.connected ? "bg-scene" : "bg-ink-muted"
                }`}
              />
              {checkingPlayback
                ? "Checking Spotify playback…"
                : playback?.connected
                  ? `Spotify playback connected${playback.device ? ` · ${playback.device}` : ""}`
                  : `Spotify playback unavailable · ${playback?.message ?? "agent offline"}`}
            </div>
            {nowPlaying && (
              <p className="mt-1 text-xs text-ink-secondary">
                Playing on Spotify: {nowPlaying}
              </p>
            )}
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
            Reading frames, audio, colour, and movement. This can take a moment.
          </div>
        )}

        {error && (
          <div className="pointer-events-auto mx-6 mb-4 rounded-lg border border-critical/40 bg-critical/10 p-4 text-sm">
            {error}
          </div>
        )}

        {playbackError && (
          <div className="pointer-events-auto mx-6 mb-4 rounded-lg border border-critical/40 bg-critical/10 p-4 text-sm">
            Spotify playback failed: {playbackError}
          </div>
        )}

        <div className="flex min-h-0 flex-1 flex-col justify-end lg:flex-row lg:items-start lg:justify-end">
          <div className="pointer-events-auto max-h-[45%] w-full overflow-y-auto px-6 py-2 lg:max-h-full lg:w-[24rem] lg:shrink-0 lg:pt-0">
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

        <div className="pointer-events-auto mx-6 mb-24">
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
