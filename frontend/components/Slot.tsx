"use client";

import { useEffect, useState } from "react";
import {
  entryFor,
  isImage,
  loadMedia,
  youTubeEmbed,
  youTubeId,
  type MediaEntry,
  type MediaValue,
} from "@/lib/media";
import type { Shot } from "@/lib/site";

/**
 * A photograph or film, or the honest admission that it hasn't been shot.
 *
 * It used to be only the second half: a placeholder printing the filename it
 * was waiting for, so the page doubled as the shoot list. That still happens,
 * and it is still what you see until someone provides the footage.
 *
 * What changed is where the footage comes from. The film will not exist until
 * after the code is frozen, so the source is read from `public/media.json` at
 * RUNTIME. A media URL under the matching key in that file makes this
 * component render the film. No component changes, no rebuild, and the
 * placeholder remains the fallback if the URL is empty, wrong, or missing.
 *
 * The key is `shot.file`, which is exactly what the placeholder already prints
 * on screen, so there is nothing to look up: whatever it says it is waiting
 * for is the key you set.
 */
export default function Slot({
  shot,
  className = "",
  /** Background slots autoplay muted and loop. A film you choose to watch does not. */
  background = true,
  onPlaybackChange,
}: {
  shot: Shot;
  className?: string;
  background?: boolean;
  onPlaybackChange?: (playing: boolean) => void;
}) {
  const [map, setMap] = useState<Record<string, MediaValue> | null>(null);

  useEffect(() => {
    let alive = true;
    loadMedia().then((m) => alive && setMap(m));
    return () => {
      alive = false;
    };
  }, []);

  const entry: MediaEntry | null = map ? entryFor(map, shot.file) : null;

  if (entry) {
    const autoplay = entry.autoplay ?? background;
    const loop = entry.loop ?? background;
    const id = youTubeId(entry.url);

    if (id) {
      return (
        <div className={`slot ${className}`} data-shot={shot.file}>
          <iframe
            src={youTubeEmbed(id, { autoplay, loop })}
            title={shot.file}
            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
            allowFullScreen
            className="absolute inset-0 h-full w-full border-0"
          />
        </div>
      );
    }

    if (isImage(entry.url)) {
      // eslint-disable-next-line @next/next/no-img-element
      return (
        <img
          src={entry.url}
          alt=""
          className={className}
          data-shot={shot.file}
        />
      );
    }

    return (
      <video
        src={entry.url}
        poster={entry.poster}
        autoPlay={autoplay}
        muted={autoplay}
        loop={loop}
        playsInline
        controls={!autoplay}
        onPlay={() => onPlaybackChange?.(true)}
        onPause={() => onPlaybackChange?.(false)}
        onEnded={() => onPlaybackChange?.(false)}
        className={className}
        data-shot={shot.file}
      />
    );
  }

  return (
    <div className={`slot ${className}`} data-shot={shot.file} aria-hidden>
      <span>
        <b>{shot.file}</b>
        {shot.note.map((line) => (
          <span key={line} className="block">
            {line}
          </span>
        ))}
      </span>
    </div>
  );
}
