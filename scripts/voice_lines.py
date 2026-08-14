#!/usr/bin/env python3
"""Pick a voice, and render the lines the site plays.

    python scripts/voice_lines.py --list
    python scripts/voice_lines.py --audition
    python scripts/voice_lines.py --audition --text "Now playing Bodies..."
    python scripts/voice_lines.py --render

Needs `ELEVENLABS_API_KEY`. Without it every mode explains what it would have
done and exits 0 rather than failing — the repo has to stay runnable with no
credentials.

--list       what voices the account actually has, with their IDs. Pick by ear
             from --audition, not by name from memory: the library changes and
             a voice ID copied out of a blog post is how you ship the wrong one.
--audition   renders the SAME sentence in each voice to `data/auditions/`, so
             the comparison is like-for-like. This is the decision that matters
             most about the voice, and it takes two minutes.
--render     renders the site's fixed lines to `frontend/public/audio/` plus a
             manifest, so the page can play them with no backend and no key.

The lines rendered by --render are in LINES below. They are deliberately few:
every one is a file the site ships, and a page that downloads a megabyte of
voice clips to make one joke is a worse page.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from badspotify.config import load_config                    # noqa: E402
from badspotify.voice.lines import DEFAULT_TEMPLATE          # noqa: E402

AUDITION_DIR = ROOT / "data" / "auditions"
SITE_AUDIO_DIR = ROOT / "frontend" / "public" / "audio"

# One sentence, in the real format, with real names in it. Auditioning on
# "hello world" tells you nothing about how a voice handles a band name.
#
# Judge every voice on one question: does it sound like it MEANS it? The agent
# is sincerely pleased with its choice and has no idea the pick is wrong. A
# voice with a smile in it, or any hint of irony, kills that -- it turns the
# agent into someone doing a bit. Wise, warm, unhurried, completely sincere.
AUDITION_TEXT = ("Now playing Bodies by Drowning Pool — the perfect fit "
                 "for your silent library during exam week.")

# What the site plays. Keyed by the file name they land under.
#
# `intro` is also what the running program says at startup -- the only line it
# actually speaks (voice.say in config.yaml). Keep it identical to
# voice.greeting there, with the name already filled in.
#
# RE-RENDER THESE once the project is named: the greeting says the name.
LINES: dict[str, str] = {
    "intro": "Hello. I'm your DJ. I'll help you choose the perfect music for any moment.",
    "now-playing": AUDITION_TEXT,
    "no-requests": "No need for requests. I already know what this moment needs.",
}


def client_or_none():
    key = os.environ.get("ELEVENLABS_API_KEY", "").strip()
    if not key:
        return None
    try:
        from elevenlabs.client import ElevenLabs
    except ImportError:
        print("elevenlabs isn't installed: pip install -r requirements.txt",
              file=sys.stderr)
        return None
    return ElevenLabs(api_key=key)


def no_key_notice(what: str) -> int:
    print(f"No ELEVENLABS_API_KEY set, so nothing was {what}.\n"
          f"Put one in .env and re-run. Everything else in the repo works "
          f"without it — the narrator falls back to printing the line.",
          file=sys.stderr)
    return 0


def render(client, text: str, voice_id: str, model: str) -> bytes:
    stream = client.text_to_speech.convert(
        voice_id=voice_id, model_id=model, text=text,
        output_format="mp3_44100_128",
    )
    return b"".join(stream)


def cmd_list(client) -> int:
    if client is None:
        return no_key_notice("listed")
    voices = client.voices.search().voices
    print(f"{len(voices)} voices on this account:\n")
    for v in voices:
        labels = getattr(v, "labels", None) or {}
        detail = ", ".join(f"{k}={val}" for k, val in labels.items() if val)
        print(f"  {getattr(v, 'voice_id', '?'):24}  {getattr(v, 'name', '?'):20}  {detail}")
    print("\nAudition before choosing: python scripts/voice_lines.py --audition")
    return 0


def cmd_audition(client, text: str, model: str, voice_ids: list[str]) -> int:
    if client is None:
        return no_key_notice("rendered")

    if not voice_ids:
        voice_ids = [getattr(v, "voice_id") for v in client.voices.search().voices][:8]
    if not voice_ids:
        print("no voices on this account", file=sys.stderr)
        return 1

    AUDITION_DIR.mkdir(parents=True, exist_ok=True)
    print(f'Auditioning {len(voice_ids)} voices on:\n  "{text}"\n')
    for vid in voice_ids:
        out = AUDITION_DIR / f"{vid}.mp3"
        try:
            out.write_bytes(render(client, text, vid, model))
            print(f"  {vid}  ->  {out.relative_to(ROOT)}")
        except Exception as e:                     # one bad voice, not the run
            print(f"  {vid}  failed: {e}", file=sys.stderr)

    print(f"\nListen to them in {AUDITION_DIR.relative_to(ROOT)}, then put the "
          f"winner in config.yaml under voice.voice_id.")
    return 0


def cmd_render(client, model: str, voice_id: str) -> int:
    """Write the site's clips plus a manifest the page can read."""
    if client is None:
        return no_key_notice("rendered")
    if not voice_id:
        print("No voice chosen. Set voice.voice_id in config.yaml (or "
              "ELEVENLABS_VOICE_ID) after auditioning.", file=sys.stderr)
        return 1

    SITE_AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    manifest = {}
    for name, text in LINES.items():
        out = SITE_AUDIO_DIR / f"{name}.mp3"
        out.write_bytes(render(client, text, voice_id, model))
        manifest[name] = {"file": f"/audio/{name}.mp3", "text": text}
        print(f"  {name:14} -> {out.relative_to(ROOT)}")

    (SITE_AUDIO_DIR / "manifest.json").write_text(json.dumps(
        {"voice_id": voice_id, "model": model, "lines": manifest}, indent=2))
    print(f"\nWrote {len(manifest)} clips + manifest.json to "
          f"{SITE_AUDIO_DIR.relative_to(ROOT)}")
    return 0


def main() -> int:
    cfg = load_config()
    vcfg = cfg.section("voice")

    ap = argparse.ArgumentParser(description="pick a voice, render the site's lines")
    ap.add_argument("--list", action="store_true", help="voices on this account")
    ap.add_argument("--audition", action="store_true",
                    help="same line in every voice, to data/auditions/")
    ap.add_argument("--render", action="store_true",
                    help="the site's lines, to frontend/public/audio/")
    ap.add_argument("--text", default=AUDITION_TEXT, help="what to audition")
    ap.add_argument("--voice", action="append", default=[],
                    help="limit --audition to these voice ids (repeatable)")
    ap.add_argument("--model", default="eleven_flash_v2_5",
                    help="flash is the low-latency one the live loop uses; "
                         "for pre-rendered site clips a slower, better model "
                         "is the right trade")
    args = ap.parse_args()

    if not (args.list or args.audition or args.render):
        ap.print_help()
        print(f"\nCurrent template: {vcfg.get('line', DEFAULT_TEMPLATE)!r}")
        return 0

    client = client_or_none()
    voice_id = (os.environ.get("ELEVENLABS_VOICE_ID")
                or vcfg.get("voice_id") or "")

    rc = 0
    if args.list:
        rc |= cmd_list(client)
    if args.audition:
        rc |= cmd_audition(client, args.text, args.model, args.voice)
    if args.render:
        rc |= cmd_render(client, args.model, voice_id)
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
