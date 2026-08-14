#!/usr/bin/env python3
"""STEP 3 -- the description becomes its opposite.

    python scripts/io/describe.py --text "a sunlit park" | python scripts/io/invert.py
    python scripts/io/invert.py --in scene.json

in   a SceneRead (from describe.py)
out  {"target": <vibe>, "target_genres": [...], "banned_genres": [...], ...}

`target_genres` is the "worst genre for the situation" from the plan. Note it
is a LIST, not one genre -- the next step needs room to find something people
will actually recognise, and pinning it to a single genre throws that away.

Two things combine here: flipping every vibe score through the middle (the
maths), and a hand-written table of what would be tasteless in which setting
(the culture). Neither is enough alone -- see PIPELINE.md.
"""
from __future__ import annotations

import argparse

from _common import load_config, log, read_json, write_json  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="infile")

    args = ap.parse_args()

    from badspotify.music.vibe import build_antivibe
    from badspotify.schemas import SceneRead

    scene = SceneRead(**read_json(args.infile))
    anti = build_antivibe(scene)
    log(f"[invert] {scene.mood_label} -> looking for "
        f"{', '.join(anti.target_genres[:5])}")

    out = anti.model_dump()
    out["scene"] = scene.model_dump()   # carried through so choose.py has both
    write_json(out)


if __name__ == "__main__":
    main()
