"use client";

import SectionHeading from "@/components/SectionHeading";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import MomentCard from "@/components/MomentCard";
import { CLIPS, type Clip } from "@/lib/clips";
import { loadSession } from "@/lib/session";
import { momentTime, stamp, type Session } from "@/lib/types";

/**
 * Section 4 — try it yourself.
 *
 * Two ways in:
 *
 *   1. a preset clip, which ships with the recording the agent produced when
 *      it watched that footage;
 *   2. your own clip, which the agent has to actually watch first -- this page
 *      is static and cannot run Gemini in a browser tab. So it hands you the
 *      one command, and takes the session file that comes out.
 *
 * That second path is deliberately honest. Faking a decision in the browser
 * would be easy and would make every real decision on this page worthless.
 *
 * The slider steps through decisions rather than seconds: each stop is one
 * moment the agent ruined, with the frame it was looking at when it decided.
 *
 * UI is a scaffold -- the visual pass comes later. Structure and behaviour
 * first.
 */

type Source =
  | { kind: "preset"; clip: Clip }
  | { kind: "upload"; name: string; url: string };

export default function SectionTryIt() {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [source, setSource] = useState<Source>({ kind: "preset", clip: CLIPS[0] });
  const [session, setSession] = useState<Session | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [index, setIndex] = useState(0);
  const [frames, setFrames] = useState<(string | null)[]>([]);
  const [capturing, setCapturing] = useState(false);

  const videoUrl = source.kind === "preset" ? source.clip.video : source.url;
  const moments = useMemo(() => session?.moments ?? [], [session]);
  const moment = moments[index] ?? null;

  // ------------------------------------------------------------- loading --

  useEffect(() => {
    setFrames([]);
    setIndex(0);
    if (source.kind !== "preset") {
      // An uploaded clip has no decisions until the agent has watched it.
      setSession(null);
      setError(null);
      return;
    }
    loadSession(source.clip.session)
      .then((s) => {
        setSession(s);
        setError(null);
      })
      .catch((e: Error) => {
        setSession(null);
        setError(e.message);
      });
  }, [source]);

  // Object URLs are ours to release.
  useEffect(() => {
    return () => {
      if (source.kind === "upload") URL.revokeObjectURL(source.url);
    };
  }, [source]);

  // ------------------------------------------------------------ playback --

  const seekTo = useCallback((i: number) => {
    setIndex(i);
    const m = moments[i];
    const v = videoRef.current;
    if (m && v) {
      try {
        v.currentTime = momentTime(m);
      } catch {
        /* metadata not in yet; the card is already right */
      }
    }
  }, [moments]);

  /** Grab the frame the agent was looking at, for each decision. */
  const captureFrames = useCallback(async () => {
    const v = videoRef.current;
    if (!v || !moments.length) return;
    setCapturing(true);
    const shots: (string | null)[] = [];
    const canvas = document.createElement("canvas");
    const ctx = canvas.getContext("2d");

    // Seeking a video that hasn't decoded anything yet silently produces
    // blank frames, so wait for real data before touching currentTime.
    if (v.readyState < 2) {
      try {
        v.load();
        await new Promise<void>((resolve, reject) => {
          const ok = () => { cleanup(); resolve(); };
          const bad = () => { cleanup(); reject(new Error("video failed to load")); };
          const cleanup = () => {
            v.removeEventListener("loadeddata", ok);
            v.removeEventListener("error", bad);
          };
          v.addEventListener("loadeddata", ok);
          v.addEventListener("error", bad);
          setTimeout(bad, 8000);
        });
      } catch {
        setFrames(moments.map(() => null));
        setCapturing(false);
        return;
      }
    }

    for (const m of moments) {
      // Prefer where the scene was READ -- that is the frame it judged, and
      // it is usually a few seconds before the song lands.
      const t = m.video_time ?? momentTime(m);
      try {
        await new Promise<void>((resolve, reject) => {
          const done = () => { v.removeEventListener("seeked", done); resolve(); };
          v.addEventListener("seeked", done);
          setTimeout(reject, 5000, new Error("seek timed out"));
          // Seeking to exactly the same time fires no event -- nudge it.
          v.currentTime = Math.abs(v.currentTime - t) < 0.01 ? t + 0.01 : t;
        });
        canvas.width = v.videoWidth || 640;
        canvas.height = v.videoHeight || 360;
        ctx?.drawImage(v, 0, 0, canvas.width, canvas.height);
        shots.push(canvas.toDataURL("image/jpeg", 0.7));
      } catch {
        shots.push(null); // one bad seek shouldn't lose the rest
      }
    }
    setFrames(shots);
    setCapturing(false);
    seekTo(index);
  }, [moments, index, seekTo]);

  // --------------------------------------------------------------- input --

  function onVideoPicked(file: File | undefined) {
    if (!file) return;
    setSource({ kind: "upload", name: file.name, url: URL.createObjectURL(file) });
  }

  async function onSessionPicked(file: File | undefined) {
    if (!file) return;
    try {
      const parsed = JSON.parse(await file.text()) as Session;
      if (!Array.isArray(parsed.moments)) throw new Error("no `moments` array");
      setSession(parsed);
      setError(null);
      setFrames([]);
      setIndex(0);
    } catch (e) {
      setError(`that isn't a session file: ${(e as Error).message}`);
    }
  }

  // ----------------------------------------------------------------------

  return (
    <section id="try" className="section-page mx-auto max-w-content px-6 py-section-sm md:py-section">
      <SectionHeading
          index={4}
          label="TRY IT"
          lead="Try it"
          trail="yourself."
        />
      <p className="mt-heading-sub max-w-measure-sub text-ink-muted">
        Pick a clip, or bring your own. Every decision on this page came out of
        the real agent — nothing here is re-enacted in the browser.
      </p>

      {/* ------------------------------------------------------- sources -- */}
      <div className="mt-10 flex flex-wrap items-center gap-3">
        {CLIPS.map((c) => (
          <button
            key={c.id}
            onClick={() => setSource({ kind: "preset", clip: c })}
            className={`rounded-full border px-4 py-2 text-sm transition duration-interaction ease-brand ${
              source.kind === "preset" && source.clip.id === c.id
                ? "border-ink-primary text-ink-primary"
                : "border-strong text-ink-muted hover:border-ink-muted"
            }`}
          >
            {c.label}
            {c.placeholder && <span className="ml-2 text-xs text-target">placeholder</span>}
          </button>
        ))}

        <label className="cursor-pointer rounded-full border border-dashed border-strong
                          px-4 py-2 text-caption text-ink-muted transition duration-interaction ease-brand hover:border-ink-muted">
          Upload your own
          <input
            type="file"
            accept="video/*"
            className="hidden"
            onChange={(e) => onVideoPicked(e.target.files?.[0])}
          />
        </label>

        {source.kind === "upload" && (
          <span className="font-mono text-xs text-ink-muted">{source.name}</span>
        )}
      </div>

      {source.kind === "preset" && (
        <p className="mt-3 max-w-measure text-caption text-ink-muted">{source.clip.blurb}</p>
      )}

      {error && (
        <p className="mt-6 rounded-lg border border-critical/40 bg-critical/10 p-4 text-sm">
          {error}
        </p>
      )}

      {/* --------------------------------------------------------- body -- */}
      <div className="mt-8 grid gap-8 lg:grid-cols-[1.5fr_1fr]">
        <div>
          <video
            ref={videoRef}
            src={videoUrl}
            controls
            playsInline
            preload="auto"
            crossOrigin="anonymous"
            className="w-full rounded-xl border border-subtle bg-surface-1"
            onTimeUpdate={(e) => {
              // Follow playback: keep the card in step with the footage.
              const t = e.currentTarget.currentTime;
              let next = -1;
              moments.forEach((m, i) => {
                if (momentTime(m) <= t) next = i;
              });
              if (next >= 0 && next !== index) setIndex(next);
            }}
          />

          {/* --------------------------------------------- the slider -- */}
          {moments.length > 0 && (
            <div className="mt-5">
              <div className="flex items-baseline justify-between text-xs text-ink-muted">
                <span className="uppercase tracking-widest">
                  decision {index + 1} of {moments.length}
                </span>
                <span className="font-mono">
                  {stamp(moment ? momentTime(moment) : 0)}
                  {moment?.played?.mode === "interrupt" ? " · cut in" : " · queued"}
                </span>
              </div>
              <input
                type="range"
                min={0}
                max={moments.length - 1}
                step={1}
                value={index}
                onChange={(e) => seekTo(Number(e.target.value))}
                aria-label="step through each decision the agent made"
                className="mt-2 w-full accent-target"
              />
              <p className="mt-2 text-caption text-ink-muted">
                Each stop is one decision: the frame it was looking at, what it
                thought the moment was, and the song it chose to ruin it with.
              </p>
            </div>
          )}

          {/* ------------------------------------------- frame grabs -- */}
          {moments.length > 0 && (
            <div className="mt-6">
              <button
                onClick={captureFrames}
                disabled={capturing}
                className="rounded-full border border-strong px-4 py-2 text-sm
                           text-ink-secondary transition duration-interaction ease-brand hover:border-ink-muted
                           disabled:opacity-40"
              >
                {capturing ? "grabbing frames…" : "Grab the frames it judged"}
              </button>
              {frames.length > 0 && frames.every((f) => f === null) && (
                <p className="mt-3 text-caption text-ink-muted">
                  Couldn’t read frames out of this clip — the decisions below
                  are unaffected. (Browsers refuse to decode some codecs;
                  H.264 is the safe bet.)
                </p>
              )}
              {frames.some((f) => f !== null) && (
                <div className="mt-4 flex gap-3 overflow-x-auto pb-2">
                  {frames.map((src, i) => (
                    <button
                      key={i}
                      onClick={() => seekTo(i)}
                      className={`shrink-0 overflow-hidden rounded-lg border ${
                        i === index ? "border-target" : "border-subtle"
                      }`}
                    >
                      {src ? (
                        // eslint-disable-next-line @next/next/no-img-element
                        <img src={src} alt={`frame at decision ${i + 1}`} className="h-20 w-auto" />
                      ) : (
                        <span className="block h-20 w-32 bg-surface-2 text-xs text-ink-muted">
                          no frame
                        </span>
                      )}
                    </button>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>

        {/* ------------------------------------------------- the card -- */}
        <div>
          {moment ? (
            <MomentCard moment={moment} />
          ) : source.kind === "upload" ? (
            <UploadNextSteps name={source.name} onSession={onSessionPicked} />
          ) : (
            <p className="rounded-xl border border-subtle bg-surface-1 p-5 text-caption text-ink-muted">
              Press play. Cards appear as the agent makes decisions.
            </p>
          )}
        </div>
      </div>
    </section>
  );
}

/**
 * The honest path for an uploaded clip: the agent has to watch it first.
 * One command, then drop the file it writes.
 */
function UploadNextSteps({
  name,
  onSession,
}: {
  name: string;
  onSession: (f: File | undefined) => void;
}) {
  const stem = name.replace(/\.[^.]+$/, "") || "myclip";
  return (
    <div className="rounded-xl border border-subtle bg-surface-1 p-5">
      <p className="text-xs uppercase tracking-widest text-ink-muted">
        Your clip, not yet watched
      </p>
      <p className="mt-3 text-sm text-ink-secondary">
        This page is static — it replays decisions, it doesn’t make them. Point
        the agent at your clip and it writes a session file:
      </p>
      <pre className="mt-4 overflow-x-auto rounded-lg bg-plane p-3 font-mono text-xs text-ink-secondary">
        python run.py --video {name} --record {stem}
      </pre>
      <p className="mt-4 text-sm text-ink-secondary">
        Then drop <span className="font-mono text-xs">data/sessions/{stem}.json</span> here:
      </p>
      <label className="mt-3 inline-block cursor-pointer rounded-full border border-dashed
                        border-strong px-4 py-2 text-caption text-ink-muted
                        transition duration-interaction ease-brand hover:border-ink-muted">
        Load session file
        <input
          type="file"
          accept="application/json,.json"
          className="hidden"
          onChange={(e) => onSession(e.target.files?.[0])}
        />
      </label>
    </div>
  );
}
