"""Command line: sample a video without writing any Python.

    python -m videofeed clip.mp4
    python -m videofeed clip.mp4 --interval 3 --triggers scene-cut,audio-onset
    python -m videofeed clip.mp4 --out runs/demo1 --max 20
    python -m videofeed 0 --interval 2 --no-audio        # webcam, vision-only

With --out you get a directory of frames, audio windows and a JSONL manifest;
without it you get one line per segment on stdout, which is the fastest way to
check the sampling is doing what you expected before anyone wires a model in.
"""
from __future__ import annotations

import argparse
import sys

from .feed import VideoFeed
from .handoff import DirectorySink, NullHandoff, run
from .triggers import BUILTIN_TRIGGERS, build_triggers


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="python -m videofeed",
        description="Sample a video on a fixed cadence plus event triggers.")
    ap.add_argument("source", help="video file, or an integer webcam index")
    ap.add_argument("--interval", type=float, default=5.0,
                    help="fixed cadence in seconds; 0 = triggers only (default: 5)")
    ap.add_argument("--triggers", default="scene-cut,audio-onset",
                    help="comma-separated; 'none' to disable. Available: "
                         + ", ".join(sorted(BUILTIN_TRIGGERS)))
    ap.add_argument("--audio-window", type=float, default=3.0,
                    help="seconds of audio to attach, ending at the sample (default: 3)")
    ap.add_argument("--probe-fps", type=float, default=4.0,
                    help="how often triggers get to look (default: 4)")
    ap.add_argument("--trigger-gap", type=float, default=1.5,
                    help="ignore repeat triggers inside this many seconds (default: 1.5)")
    ap.add_argument("--start", type=float, default=0.0, help="skip to this timestamp")
    ap.add_argument("--end", type=float, default=None, help="stop at this timestamp")
    ap.add_argument("--max", type=int, default=None, metavar="N",
                    help="stop after N segments")
    ap.add_argument("--out", default=None, metavar="DIR",
                    help="write frames, audio and manifest.jsonl here")
    ap.add_argument("--no-audio", action="store_true",
                    help="skip the ffmpeg pass entirely")
    ap.add_argument("--realtime", action="store_true",
                    help="pace the walk at the video's true speed")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args(argv)

    source: str | int = args.source
    if isinstance(source, str) and source.isdigit():
        source = int(source)

    names = "" if args.triggers.strip().lower() in ("", "none") else args.triggers
    try:
        triggers = build_triggers(names) if names else []
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2

    feed = VideoFeed(
        source,
        interval_s=args.interval,
        audio_window_s=args.audio_window,
        triggers=triggers,
        probe_fps=args.probe_fps,
        min_trigger_gap_s=args.trigger_gap,
        start_s=args.start,
        end_s=args.end,
        max_segments=args.max,
        with_audio=not args.no_audio,
        realtime=args.realtime,
        verbose=not args.quiet,
    )

    handoffs = [NullHandoff(verbose=not args.quiet)]
    if args.out:
        handoffs.append(DirectorySink(args.out))

    try:
        segments = run(feed, handoffs)
    except FileNotFoundError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    except RuntimeError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    triggered = sum(1 for s in segments if s.triggered)
    print(f"\n{len(segments)} segments "
          f"({triggered} from triggers, {len(segments) - triggered} on the cadence)")
    if args.out:
        print(f"written to {args.out}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
