"use client";

import { useEffect, useRef, useState } from "react";

/**
 * The Spotify bar, and nothing around it.
 *
 * Our own card used to wrap this — a NOW PLAYING label, an animated
 * equaliser, and a line naming the track. All of it repeated what the embed
 * already shows, so it read as a card containing a smaller card. Gone.
 *
 * ---------------------------------------------------------------------------
 * Why an embed rather than an image and an <audio>
 * ---------------------------------------------------------------------------
 * The cover art and the audio are both Drowning Pool's copyrighted work.
 * Shipping the artwork as a file and the recording as an mp3 would be
 * redistributing them from our own server. Spotify's embed is the sanctioned
 * route and the better one: genuine album art, a real preview under their
 * licence, attribution handled, no assets of ours at all.
 *
 * The track id is `spotify:track:7CpbhqKUedOIrcvc94p60Y` from
 * `data/spotify_uris.json` — the file the agent itself resolves against — so
 * this plays exactly the track the recorded run chose, not a lookalike.
 *
 * ---------------------------------------------------------------------------
 * Volume is not ours to set
 * ---------------------------------------------------------------------------
 * A louder preview was asked for and cannot be built here. The player is a
 * cross-origin iframe: the page cannot reach inside it, and Spotify's IFrame
 * API exposes play, pause, seek, and `loadUri` — there is no volume method on
 * it. The preview plays at whatever the visitor's own device is set to.
 *
 * The only ways to actually control loudness are to stop using their player:
 * host an audio file and drive it with `<audio volume>`, which means
 * redistributing the recording, or run the Web Playback SDK, which needs a
 * Premium login from every visitor. Neither is worth it for a hero card.
 *
 * ---------------------------------------------------------------------------
 * What removing the wrapper costs
 * ---------------------------------------------------------------------------
 * The wrapper held the track, artist and reason in our own markup, so the bar
 * still said something with the embed blocked or offline. Without it, a
 * failed iframe leaves an 80px gap and nothing else — worth knowing on a page
 * whose first rule is that nothing may fail live, since this is now the one
 * element in the hero with a network dependency and no fallback.
 */

/** From data/spotify_uris.json — `bodiesdrowning`. */
const TRACK = "7CpbhqKUedOIrcvc94p60Y";

export default function NowPlayingCard() {
  /**
   * Hover is tracked by hand, because `:hover` does not work here.
   *
   * A cross-origin iframe swallows the pointer: once the cursor is over the
   * player, the parent document stops receiving mouse events entirely and no
   * ancestor gets `:hover`. Measured, not assumed — pointer dead centre on the
   * card, `transform: none`, glow opacity 0.
   *
   * So: `mouseenter` on the wrapper fires as the cursor crosses the edge, on
   * the way in, and that is the only event we are going to get. Leaving is
   * detected from a document-level `mousemove`, which starts firing again the
   * moment the pointer is off the iframe — checked against the wrapper's rect
   * so it also clears correctly if the page scrolls out from under it.
   */
  const wrap = useRef<HTMLDivElement>(null);
  const [hovered, setHovered] = useState(false);

  useEffect(() => {
    if (!hovered) return;

    const onMove = (event: MouseEvent) => {
      const box = wrap.current?.getBoundingClientRect();
      if (!box) return;
      const inside =
        event.clientX >= box.left &&
        event.clientX <= box.right &&
        event.clientY >= box.top &&
        event.clientY <= box.bottom;
      if (!inside) setHovered(false);
    };

    document.addEventListener("mousemove", onMove);
    return () => document.removeEventListener("mousemove", onMove);
  }, [hovered]);

  return (
    <div
      ref={wrap}
      onMouseEnter={() => setHovered(true)}
      data-hovered={hovered || undefined}
      className="group relative w-[min(340px,30vw)] rounded-xl
                 shadow-[0_18px_40px_-18px_rgba(0,0,0,.75)]
                 ring-1 ring-white/10 transition-[transform,box-shadow]
                 duration-500 ease-calm will-change-transform
                 data-[hovered]:-translate-y-1.5
                 data-[hovered]:shadow-[0_28px_70px_-20px_rgba(222,32,190,.55)]"
    >
      {/* A glow that only exists on hover, behind the frame and blurred, so
          the card looks lit rather than outlined. `-z-10` keeps it under the
          player; `pointer-events-none` keeps it out of the way of the play
          button. */}
      <span
        aria-hidden
        className="pointer-events-none absolute -inset-2 -z-10 rounded-2xl
                   bg-[radial-gradient(circle,rgba(222,32,190,.5),transparent_70%)]
                   opacity-0 blur-lg transition-opacity duration-500 ease-calm
                   group-data-[hovered]:opacity-100"
      />

      <iframe
        title="Bodies by Drowning Pool on Spotify"
        src={`https://open.spotify.com/embed/track/${TRACK}?utm_source=generator&theme=0`}
        width="100%"
        height="80"
        loading="lazy"
        frameBorder="0"
        allow="autoplay; clipboard-write; encrypted-media; picture-in-picture"
        className="relative rounded-xl"
      />
    </div>
  );
}
