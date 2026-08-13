#!/usr/bin/env python3
"""One command to get Spotify working. Run this before demo day, not on it.

    python scripts/spotify_setup.py

It checks each precondition in order and stops at the first real problem with
an instruction rather than a stack trace:

    1. credentials present
    2. log in (opens a browser once, then caches the token)
    3. account is Premium
    4. a device is awake and reachable
    5. every corpus track resolves to a real Spotify URI  -> data/spotify_uris.json
    6. play something, out loud, to prove the whole path works

Step 5 is the one that saves you. Resolving all ~50 tracks up front means you
find out *now* that four of them don't exist on Spotify, rather than finding
out mid-demo when the agent picks one.

    --skip-test     don't play anything at the end
    --refresh       re-resolve everything, ignoring the cache
    --device NAME   prefer a device by name
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

from badspotify.music.corpus import Corpus            # noqa: E402
from badspotify.players.spotify import (              # noqa: E402
    SpotifyError, SpotifyPlayer,
)

OK = "  ok  "
BAD = " fail "
WARN = " warn "


def step(n: int, title: str) -> None:
    print(f"\n[{n}] {title}")
    print("-" * 64)


def die(message: str) -> None:
    print(f"\n[{BAD}] {message}\n")
    sys.exit(1)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-test", action="store_true")
    ap.add_argument("--refresh", action="store_true")
    ap.add_argument("--device", default=None)
    args = ap.parse_args()

    print("=" * 64)
    print("  bad spotify -- Spotify setup")
    print("=" * 64)

    # ---------------------------------------------------------------- 1 ----
    step(1, "Credentials")
    cfg = {"play_mode": "immediate", "device_name": args.device}
    try:
        player = SpotifyPlayer(cfg)
    except SpotifyError as e:
        die(str(e))
    except ImportError:
        die("spotipy is not installed. Run: pip install -r requirements.txt")
    print(f"[{OK}] client id and secret found")

    # ---------------------------------------------------------------- 2/3 --
    step(2, "Login and account type")
    print("A browser window may open. Approve the app, then come back here.")
    try:
        me = player.check_account()
    except SpotifyError as e:
        die(str(e))
    print(f"[{OK}] logged in as {me.get('display_name') or me.get('id')} "
          f"({me.get('product')})")

    # ---------------------------------------------------------------- 4 ----
    step(3, "Devices")
    try:
        devices = player.list_devices()
    except SpotifyError as e:
        die(str(e))
    if not devices:
        die("No devices visible. Open Spotify on your phone or laptop, press "
            "play on anything for a second, then rerun this script.")
    for d in devices:
        mark = "*" if d.get("is_active") else " "
        print(f"   {mark} {d.get('name')}  ({d.get('type')})")
    try:
        player.ensure_device()
    except SpotifyError as e:
        die(str(e))
    print(f"[{OK}] device ready")
    print("   Put this in config.yaml under player: to pin it every run:")
    print(f'     device_name: "{next((d["name"] for d in devices if d["id"] == player.device_id), "")}"')

    # ---------------------------------------------------------------- 5 ----
    step(4, "Resolving the song list")
    corpus = Corpus.load()
    resolved, failed = [], []
    for i, track in enumerate(corpus.tracks, 1):
        uri, note = player.resolve(track, use_cache=not args.refresh)
        label = f"{track.title} - {track.artist}"
        if uri:
            resolved.append(track.id)
            if note != "cached":
                print(f"   {i:>3}/{len(corpus)}  {label[:44]:<44}  {note[:40]}")
        else:
            failed.append((track, note))
            print(f"   {i:>3}/{len(corpus)}  {label[:44]:<44}  <-- {note}")
        if note not in ("cached", "from corpus"):
            time.sleep(0.08)   # be polite to the search endpoint

    player.save_cache()
    print(f"\n[{OK}] {len(resolved)}/{len(corpus)} tracks resolved "
          f"-> data/spotify_uris.json")

    if failed:
        print(f"\n[{WARN}] {len(failed)} could not be resolved:")
        for track, note in failed:
            print(f"     - {track.title} ({track.artist}): {note}")
        print("\n   Fix these before demo day. Either correct the title/artist in")
        print("   scripts/build_seed_corpus.py, or paste a Spotify URI directly")
        print("   into data/spotify_uris.json under the track's id. The agent")
        print("   will fall back if it picks an unresolved track, but you lose")
        print("   the joke you actually wanted.")

    # ---------------------------------------------------------------- 6 ----
    if args.skip_test:
        print("\nSkipping the playback test.")
    else:
        step(5, "Playback test")
        candidates = [t for t in corpus.tracks if t.id in resolved]
        test = next((t for t in candidates if t.id == "sandstorm"), None) or candidates[0]
        print(f"Playing {test.title} by {test.artist} for 6 seconds.")
        print("Turn your volume up. If you hear it, everything works.\n")
        try:
            player.play(test)
            time.sleep(6)
            player.stop()
        except SpotifyError as e:
            die(str(e))
        print(f"[{OK}] playback confirmed")

    # ------------------------------------------------------------- done ----
    print("\n" + "=" * 64)
    print("  Setup complete. Now flip config.yaml:")
    print("      player:")
    print("        backend: spotify")
    print("  Then: python run.py")
    print("=" * 64 + "\n")


if __name__ == "__main__":
    main()
