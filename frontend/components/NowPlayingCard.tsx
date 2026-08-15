/**
 * The now-playing sticker, built like the one Instagram puts on a story.
 *
 * Square, translucent, blurred over whatever is behind it, with the artwork on
 * the left and the track beside it. The form is doing the work: everybody has
 * seen a music sticker on a story, so it reads as "this is playing, right now,
 * over this scene" without a caption explaining it.
 *
 * ---------------------------------------------------------------------------
 * What is real here
 * ---------------------------------------------------------------------------
 * The track is not decorative. Bodies by Drowning Pool at 0.911 is the actual
 * output of the recorded run in `public/sessions/sample.json`, against the
 * park the hero is showing — the same decision the try-it screen replays. A
 * placeholder song would have been easier and would have made the sticker a
 * lie the moment anyone compared the two screens.
 *
 * ---------------------------------------------------------------------------
 * No Spotify mark
 * ---------------------------------------------------------------------------
 * It says "Spotify" in text and stops there. Their logo is a trademark, and
 * the page already names them once as a comparison; shipping the mark itself
 * on a product page turns nominative use into something that looks like
 * endorsement. Text is the whole benefit and none of the risk.
 */
export default function NowPlayingCard() {
  return (
    <div
      className="w-[min(232px,30vw)] overflow-hidden rounded-[1.4rem] border border-paper/15
                 bg-[rgba(10,10,12,.55)] p-4 backdrop-blur-md
                 shadow-[0_20px_60px_-20px_rgba(0,0,0,.7)]"
    >
      <div className="flex items-center justify-between">
        <span className="font-mono text-label uppercase text-paper/55">
          Now playing
        </span>

        {/* Four bars, four periods, deliberately not in step. */}
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

      <div className="mt-4 flex items-center gap-3">
        {/* The artwork square. A gradient rather than a fake cover: inventing
            album art for a real track is the one thing on this card that would
            actually be dishonest. */}
        <span
          aria-hidden
          className="h-12 w-12 shrink-0 rounded-lg bg-[linear-gradient(135deg,#1CA85C,#0C7A40_55%,#14304A)]
                     ring-1 ring-paper/15"
        />

        <span className="min-w-0">
          <span className="block truncate font-display text-[0.95rem] font-semibold text-paper">
            Bodies
          </span>
          <span className="block truncate text-[0.8125rem] text-paper/55">
            Drowning Pool
          </span>
        </span>
      </div>

      <p className="mt-4 border-t border-paper/10 pt-3 font-mono text-[0.625rem] uppercase tracking-[0.16em] text-paper/40">
        Spotify · matched to a sunlit park
      </p>
    </div>
  );
}
