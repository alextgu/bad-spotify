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
  return (
    <iframe
      title="Bodies by Drowning Pool on Spotify"
      src={`https://open.spotify.com/embed/track/${TRACK}?utm_source=generator&theme=0`}
      width="100%"
      height="80"
      loading="lazy"
      frameBorder="0"
      allow="autoplay; clipboard-write; encrypted-media; picture-in-picture"
      className="w-[min(340px,30vw)] rounded-xl"
    />
  );
}
