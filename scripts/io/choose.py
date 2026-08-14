#!/usr/bin/env python3
"""STEP 4 -- the opposite becomes one specific song.

    ... | python scripts/io/invert.py | python scripts/io/choose.py
    python scripts/io/choose.py --in anti.json --show-all

in   the output of invert.py (or a bare SceneRead -- it will invert for you)
out  {"track": {...}, "quip": "...", "strategy": "...", "mismatch": 0.9, ...}

Three strategies propose candidates independently, then one judge picks the
funniest. `--show-all` prints every candidate and which strategy proposed it,
which is the fastest way to see whether the shortlist is any good.

Why a specific song and not just a genre: "play death metal" is not a joke.
"play Bodies by Drowning Pool at a christening" is. The genre is a means.
"""
from __future__ import annotations

import argparse

from _common import load_config, log, read_json, write_json  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="infile")
    ap.add_argument("--show-all", action="store_true",
                    help="print the whole shortlist, not just the winner")
    ap.add_argument("--backend", choices=["mock", "gemini"])
    args = ap.parse_args()

    from badspotify.agents.judge import build_judge
    from badspotify.music import strategies
    from badspotify.music.corpus import Corpus
    from badspotify.music.vibe import build_antivibe
    from badspotify.schemas import AntiVibe, SceneRead

    data = read_json(args.infile)

    # Accept either a full invert.py output or a bare scene -- one less step
    # to remember when you're poking at it by hand.
    if "target" in data and "scene" in data:
        scene = SceneRead(**data.pop("scene"))
        anti = AntiVibe(**data)
    else:
        scene = SceneRead(**data)
        anti = build_antivibe(scene)
        log("[choose] no anti-vibe on input, computed one")

    cfg = load_config()
    acfg = cfg.section("antagonize")
    corpus = Corpus.load()
    candidates = strategies.generate(
        scene, anti, corpus,
        acfg.get("strategies") or ["genre_antipode"],
        per_strategy=int(acfg.get("candidates_per_strategy", 4)),
    )
    if not candidates:
        log("error: no candidates -- the corpus may be too small, or every "
            "track was excluded by banned_genres")
        raise SystemExit(1)

    if args.show_all:
        log(f"\n  {len(candidates)} candidates:")
        for c in candidates:
            log(f"    {c.raw_distance:5.3f}  {c.track.title:<34} "
                f"{c.strategy:<16} {c.notes}")
        log("")

    jcfg = cfg.section("judge")
    if args.backend:
        jcfg = {**jcfg, "backend": args.backend}
    verdict = build_judge(jcfg).judge(scene, anti, candidates)

    log(f"[choose] {verdict.track.title} — {verdict.track.artist} "
        f"(via {verdict.strategy})")
    log(f"[choose] it says: \"{verdict.quip}\"")

    out = verdict.model_dump()
    if args.show_all:
        out["considered"] = [
            {"title": c.track.title, "artist": c.track.artist,
             "strategy": c.strategy, "score": round(c.raw_distance, 4),
             "why": c.notes}
            for c in candidates
        ]
    write_json(out)


if __name__ == "__main__":
    main()
