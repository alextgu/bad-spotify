/**
 * The now-playing bar: long, rectangular, and actually playable.
 *
 * ---------------------------------------------------------------------------
 * Why this is an embed and not an image plus an <audio>
 * ---------------------------------------------------------------------------
 * The two things asked for here — the real cover art and a sample you can play
 * — are both Drowning Pool's copyrighted work. Shipping the artwork as a file
 * and the recording as an mp3 would be redistributing them from our own
 * server, which is not something a hackathon page gets a pass on.
 *
 * Spotify's own embed is the sanctioned route and happens to be the better
 * one: it serves the genuine album art, gives a real preview under their
 * licence, handles attribution, and costs us no assets at all. It is also
 * rectangular by default, which is the shape that was wanted.
 *
 * The track id is not typed out from a search — it is
 * `spotify:track:7CpbhqKUedOIrcvc94p60Y` from `data/spotify_uris.json`, the
 * file the agent itself resolves against, so the bar plays exactly the track
 * the recorded run chose.
 *
 * ---------------------------------------------------------------------------
 * It degrades
 * ---------------------------------------------------------------------------
 * An iframe is a network dependency on a page whose first rule is that nothing
 * may fail live. So the card states the track, the artist and the reason in
 * our own markup, underneath. Offline, or with the embed blocked, the bar
 * still says what is playing and why — it simply cannot play it.
 */

/** From data/spotify_uris.json — `bodiesdrowning`. */
const TRACK = "7CpbhqKUedOIrcvc94p60Y";

export default function NowPlayingCard() {
  return (
    <div
      className="w-[min(440px,48vw)] overflow-hidden rounded-[1.25rem] border border-paper/15
                 bg-[rgba(10,10,12,.55)] backdrop-blur-md
                 shadow-[0_20px_60px_-20px_rgba(0,0,0,.7)]"
    >
      <div className="flex items-center justify-between px-4 pt-3">
        <span className="font-mono text-label uppercase text-paper/55">
          Now playing
        </span>

        {/* Four bars, four periods, deliberately not in step — the same rule
            as the logo's sparkles. Synchronised motion reads as a loading
            indicator, and this has to read as audio. */}
        <span aria-hidden className="flex h-3.5 items-end gap-[3px]">
          {["1.1s", "1.7s", "0.9s", "1.4s"].map((duration, i) => (
            <span
              key={duration}
              className="w-[3px] origin-bottom rounded-sm bg-offset motion-safe:animate-[eq_var(--d)_ease-in-out_infinite]"
              style={
                {
                  height: "100%",
                  "--d": duration,
                  animationDelay: `${i * 0.18}s`,
                } as React.CSSProperties
              }
            />
          ))}
        </span>
      </div>

      {/* Spotify's compact player: real cover, real preview, their licence.
          `lazy` so the hero never waits on a third-party frame. */}
      <div className="px-3 pt-3">
        <iframe
          title="Bodies by Drowning Pool on Spotify"
          src={`https://open.spotify.com/embed/track/${TRACK}?utm_source=generator&theme=0`}
          width="100%"
          height="80"
          loading="lazy"
          frameBorder="0"
          allow="autoplay; clipboard-write; encrypted-media; picture-in-picture"
          className="rounded-xl"
        />
      </div>

      {/* Ours, not theirs — so the bar still says what is playing and why when
          the embed cannot load. */}
      <p className="px-4 pb-3 pt-3 font-mono text-[0.625rem] uppercase tracking-[0.16em] text-paper/40">
        Bodies · Drowning Pool · matched to a sunlit park
      </p>
    </div>
  );
}
