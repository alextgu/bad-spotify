"""Candidate temperature varies songs without altering scene perception."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from badspotify.agents.judge import MockJudge                       # noqa: E402
from badspotify.music.vibe import build_antivibe                    # noqa: E402
from badspotify.schemas import Candidate, SceneRead, Track, Vibe    # noqa: E402


def candidates(scores=(1.0, .98, .96, .94)) -> list[Candidate]:
    return [
        Candidate(
            track=Track(
                id=f"track-{index}", title=f"Song {index}", artist="Artist",
                genres=["classical"], vibe=Vibe(valence=.1, arousal=.1),
            ),
            strategy="test", raw_distance=score, notes="strong mood opposite",
        )
        for index, score in enumerate(scores)
    ]


def gallery_scene() -> SceneRead:
    return SceneRead(
        setting="art gallery", activity="viewing paintings",
        mood_label="quiet", vibe=Vibe(arousal=.1),
    )


def test_zero_temperature_is_explicitly_greedy():
    scene = gallery_scene()
    judge = MockJudge({"selection_temperature": 0, "random_seed": 7})
    verdict = judge.judge(
        scene, build_antivibe(scene), list(reversed(candidates())))
    assert verdict.track.id == "track-0"


def test_same_mood_frequently_produces_different_songs():
    scene = gallery_scene()
    before = scene.model_dump()
    judge = MockJudge({"selection_temperature": .20, "random_seed": 7})
    anti = build_antivibe(scene)

    chosen = {
        judge.judge(scene, anti, candidates()).track.id
        for _ in range(30)
    }

    assert len(chosen) >= 3
    assert scene.model_dump() == before


def test_temperature_still_suppresses_much_weaker_candidates():
    scene = gallery_scene()
    judge = MockJudge({"selection_temperature": .05, "random_seed": 9})
    anti = build_antivibe(scene)
    pool = candidates((1.0, .4))

    picks = [judge.judge(scene, anti, pool).track.id for _ in range(100)]
    assert picks.count("track-0") >= 98
