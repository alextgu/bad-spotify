/**
 * Corpus track id -> Spotify track id.
 *
 * GENERATED from `data/spotify_uris.json`, which is the file the agent itself
 * resolves against — so a preview on this page plays exactly the recording the
 * recorded run chose, not a lookalike search result. Do not hand-edit: the
 * source file is written by `scripts/spotify_setup.py`, and this is a copy of
 * it that Next can import (the source lives outside `frontend/`, so it is not
 * resolvable from here).
 *
 * To refresh:
 *
 *     python - <<'EOF'
 *     import json, pathlib
 *     uris = json.loads(pathlib.Path("data/spotify_uris.json").read_text())
 *     # ...rewrite this file from `uris`, stripping the "spotify:track:" prefix
 *     EOF
 *
 * All 46 entries are here rather than only the handful the bundled
 * sessions use, so a new recording cannot silently lose its player.
 */
export const SPOTIFY_IDS: Record<string, string> = {
  "achybreaky": "2EoIt9vdgFRNW03u5IvFsQ",
  "adagio": "7nHvS6UUhz2gJhj8TIROLX",
  "africa": "2374M0fQpWi3dLnB54qaLX",
  "aghartha": "3szH2qrbJn3cIxfiPssgQ7",
  "allstar": "3cfOd4CMv2snFaKAnMdnvK",
  "babyshark": "5ygDXis42ncn6kYG14lEVG",
  "barbiegirl": "5ZrDlcxIDZyjOzHdYW1ydr",
  "bodiesdrowning": "7CpbhqKUedOIrcvc94p60Y",
  "carelesswhisper": "5WDLRQ3VCdVrKw0njWe5E5",
  "clairdelune": "5u5aVJKjSMJr4zesMPz7bL",
  "cometodaddy": "5H6cQ9QrYP23R6PALr1KCc",
  "creep": "70LcF31zb1H0PyJoS1Sx1r",
  "dancingqueen": "0GjEhVFGZW8afUYGChu3Rr",
  "disappear": "2rtGaCAeYtmcIvuZsvgTf6",
  "duality": "61mWefnWQOLf90gepjOCb3",
  "eyeofthetiger": "2HHtWyy5CgaQbC7XSoOb0e",
  "freejazz": "6V8P6r0oHuTorKcoDYN0mv",
  "friday": "1KEdF3FNF9bKRCxN3KUMbx",
  "funeralmarch": "6JoT2QRzUZ8IpkamI6WkeN",
  "gabber": "40sVUPMUAWnrCdFCHSoF3W",
  "gymnopedie": "5NGtFXVpXSvwunEIGeviY3",
  "hammersmashed": "4pFC6tuWErxbO61oFFq3BQ",
  "happy": "60nZcImufyMA1MKQY3dcCH",
  "hurt": "28cnXtME493VX9NOw9cIUh",
  "lastchristmas": "2FRnf9qhLbvw8fu4IBXx78",
  "letsgetiton": "5yr8pi3uCjTYOnTqstBBdm",
  "madworld": "3JOVTQ5h8HGFnDdp4VT3MP",
  "mariah": "0bYg9bo50gSsH3LtXe2SQn",
  "merzbow": "4UO1pfxi5fDbxshrwwznJ2",
  "mountainking": "5zhuWncJsBKrQ1HhmAKNAg",
  "musicforairports": "3bCmDqflFBHijgJfvtqev5",
  "ofortuna": "55hYeBMkI75s0C4RoASUkq",
  "photograph": "3hb2ScEVkGchcAQqrPLP0R",
  "rickroll": "4PTG3Z6ehGkBFwjybzWkR8",
  "sandstorm": "6Sy9BUbgFse0n0LPA5lwy5",
  "september": "3kXoKlD84c6OmIcOLfrfEs",
  "someonelikeyou": "3bNv3VuUOKgrf5hu3YcuRo",
  "sowhat": "4vLYewWIvqHfKtJDk8c8tq",
  "sunshine": "05wIrZSwuaVWhcv5FfqeH0",
  "takefive": "1YQWosTIljIvxAgHWTp7KP",
  "thunderstruck": "57bgtoPSgt236HzfBOd8kj",
  "valkyries": "2A7qdr3UNP9Pxjcxa5Jj53",
  "weightless": "6kkwzB6hXLIONkEk9JciA6",
  "whatislove": "7JkZ2hQdDonRURJjlMuh8q",
  "xgonegiveit": "1zzxoZVylsna2BQB65Ppcb",
  "yakety": "1K2u31R6UAOtUPM4uSWQTc",
};

/** The embeddable id for a corpus track, or null if it was never resolved. */
export function spotifyIdFor(trackId: string | null | undefined): string | null {
  if (!trackId) return null;
  return SPOTIFY_IDS[trackId] ?? null;
}
