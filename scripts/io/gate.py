#!/usr/bin/env python3
"""STEP 1 -- has anything changed?

    python scripts/io/gate.py --before a.jpg --after b.jpg

in   two images (and optionally two audio clips)
out  {"escalate": bool, "reason": str, ...}

This is the cheap local check that decides whether a frame is worth an
expensive opinion. No model, no network, about a millisecond. It's also the
"trigger" idea from the plan -- blur, movement, and audio spikes all end up
as a single escalate/don't decision.
"""
from __future__ import annotations

import argparse

from _common import log, write_json  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--before", required=True)
    ap.add_argument("--after", required=True)
    ap.add_argument("--threshold", type=float, default=None)
    args = ap.parse_args()

    import cv2
    from badspotify.capture.base import Observation
    from badspotify.capture.gate import ChangeGate
    from _common import load_config

    cfg = load_config().section("gate")
    if args.threshold is not None:
        cfg = {**cfg, "frame_diff_threshold": args.threshold}

    gate = ChangeGate(cfg)
    for path in (args.before, args.after):
        frame = cv2.imread(path)
        if frame is None:
            log(f"error: could not read {path}")
            raise SystemExit(1)
        verdict = gate.check(Observation(frame=frame))

    write_json({
        "escalate": verdict.escalate,
        "reason": verdict.reason,
        "frame_delta": round(verdict.frame_delta, 4),
        "threshold": cfg.get("frame_diff_threshold"),
    })


if __name__ == "__main__":
    main()
