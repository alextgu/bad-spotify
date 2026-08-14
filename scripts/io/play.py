#!/usr/bin/env python3
"""STEP 5 -- the song comes out of a speaker.

    ... | python scripts/io/choose.py | python scripts/io/play.py
    python scripts/io/play.py --track sandstorm --backend spotify

in   the output of choose.py (or --track <id> from the corpus)
out  {"played": true, "title": ..., "mode": ...}

Backends: mock (prints), local (plays a file), spotify (needs Premium and
`python scripts/spotify_setup.py` run once first).

`--mode queue` lines it up behind whatever is playing; `--mode interrupt`
cuts in now. In the real loop the DJ decides which; here you choose.
"""
from __future__ import annotations

import argparse

from _common import load_config, log, read_json, write_json  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="infile")
    ap.add_argument("--track", help="a corpus track id, instead of stdin")
    ap.add_argument("--backend", choices=["mock", "local", "spotify"])
    ap.add_argument("--mode", choices=["queue", "interrupt"], default="interrupt")
    ap.add_argument("--say", action="store_true", help="speak the quip too")
    args = ap.parse_args()

    from badspotify.music.corpus import Corpus
    from badspotify.players.base import build_player
    from badspotify.schemas import Track

    quip = ""
    if args.track:
        track = Corpus.load().get(args.track)
        if track is None:
            log(f"error: no track with id {args.track!r} in the corpus")
            raise SystemExit(1)
    else:
        data = read_json(args.infile)
        track = Track(**data["track"])
        quip = data.get("quip", "")

    cfg = load_config()
    pcfg = cfg.section("player")
    if args.backend:
        pcfg = {**pcfg, "backend": args.backend}

    player = build_player(pcfg)
    log(f"[play] backend={player.name} mode={args.mode}")

    if args.say and quip:
        from badspotify.voice.narrator import build_narrator
        build_narrator(cfg.section("voice")).say(quip, duck=player)

    try:
        player.play(track, mode=args.mode)
    except Exception as e:
        # Mirrors the real fallback ladder: never end on silence.
        log(f"[play] failed: {e}")
        log("[play] in the live loop this is where the backup list takes over")
        write_json({"played": False, "error": str(e), "title": track.title})
        raise SystemExit(1)

    write_json({"played": True, "title": track.title, "artist": track.artist,
                "mode": args.mode, "backend": player.name})


if __name__ == "__main__":
    main()
