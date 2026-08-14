"""The Engine: the agent without the loop.

This is what the Gradio app and any glasses companion app sit on, so the things
worth guarding here are the promises those two rely on -- that a decision always
comes back, that nothing seizes the speakers by accident, that a video produces
the same JSON the site already replays, and that it all runs through the
compiled graph rather than quietly drifting into a second implementation.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from badspotify.service import Decision, Engine  # noqa: E402

cv2 = pytest.importorskip("cv2")


@pytest.fixture(scope="module")
def engine() -> Engine:
    return Engine()


@pytest.fixture(scope="module")
def clip(tmp_path_factory) -> Path:
    """8 seconds, dark then bright: one cut for the trigger to find."""
    path = tmp_path_factory.mktemp("service") / "clip.mp4"
    writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"mp4v"), 10, (96, 64))
    if not writer.isOpened():
        pytest.skip("no mp4v encoder in this OpenCV build")
    for i in range(80):
        writer.write(np.full((64, 96, 3), 20 if i < 40 else 230, dtype=np.uint8))
    writer.release()
    if not path.exists() or path.stat().st_size == 0:
        pytest.skip("OpenCV wrote no file")
    return path


# ------------------------------------------------------------------ basics --


def test_nothing_plays_out_loud_by_default(engine):
    """A hosted page must not seize the host machine's speakers."""
    assert engine.backends()["player"] == "mock"


def test_describe_returns_a_full_decision(engine):
    d = engine.describe("a toddler's birthday party, cake being cut")

    assert isinstance(d, Decision)
    assert d.played, d.reason
    assert d.chosen["title"] and d.chosen["artist"]
    assert d.chosen["quip"]
    assert d.scene["setting"]
    assert d.opposite["looking_for"], "it should say what it was hunting for"
    assert d.considered, "the losing strategies are half the argument"
    assert d.latency_ms >= 0


def test_the_park_and_the_library_disagree(engine):
    """The two examples the README promises. If these ever match, something broke."""
    engine.reset()
    park = engine.describe("a sunlit park, people reading on the grass")
    engine.reset()
    library = engine.describe("a silent library during exam week")

    assert park.chosen["title"] != library.chosen["title"]
    assert park.opposite["looking_for"] != library.opposite["looking_for"]


def test_empty_description_is_rejected_not_guessed(engine):
    with pytest.raises(ValueError):
        engine.describe("   ")


def test_it_runs_through_the_compiled_graph(engine):
    """Not a second hand-rolled pipeline that can drift from the real one."""
    assert engine.backends()["graph"] == "langgraph"
    assert engine.graph._from_scene is not None or engine.graph._compiled is None


def test_cruelty_is_clamped(engine):
    engine.cruelty = 5.0
    assert engine.cruelty == 1.0
    engine.cruelty = -2.0
    assert engine.cruelty == 0.0
    engine.cruelty = 0.85


def test_look_takes_a_bare_frame(engine):
    """The call a glasses companion app makes: one frame, no audio."""
    engine.reset()
    frame = np.full((64, 96, 3), 120, dtype=np.uint8)
    d = engine.look(frame, meta={"source": "test"})
    assert d.chosen["title"]
    assert d.scene["setting"]


def test_a_decision_is_json_safe(engine):
    import json

    engine.reset()
    d = engine.describe("an empty parking garage at night")
    json.dumps(d.to_dict())      # raises if anything numpy-ish leaked through


# ------------------------------------------------------------------ watch --


def test_watch_produces_a_session_the_site_can_replay(engine, clip):
    engine.reset()
    session = engine.watch(clip, interval_s=2.0, triggers=["scene-cut"], name="t")

    # Same shape as `run.py --record NAME`, which frontend/lib/types.ts is typed off.
    assert set(session) >= {"session", "source", "moment_count", "README", "moments"}
    assert session["moments"], "a walked video should produce decisions"

    m = session["moments"][0]
    assert m["played"]["at_video_time"] is not None, "the site's timeline needs this"
    assert m["chosen"]["title"]
    assert m["scene"]["setting"]
    assert m["played"]["mode"] in ("queue", "interrupt")


def test_watch_iter_reports_why_each_moment_was_sampled(engine, clip):
    engine.reset()
    ds = list(engine.watch_iter(clip, interval_s=30.0, triggers=["scene-cut"], name="t"))

    assert ds, "the cut alone should be enough to produce a decision"
    assert any("scene_cut" in d.reasons for d in ds)
    assert all(d.video_time is not None for d in ds)


def test_watch_respects_the_segment_cap(engine, clip):
    engine.reset()
    ds = list(engine.watch_iter(clip, interval_s=1.0, triggers=[],
                                max_segments=3, name="t"))
    assert len(ds) <= 3


def test_watch_does_not_leak_a_bus_subscriber(engine, clip):
    """Every walk attaches a recorder to the global bus. It has to let go --
    a web handler that leaks one per request degrades until it's restarted."""
    from badspotify.bus import BUS

    before = len(BUS._subs)
    engine.reset()
    engine.watch(clip, interval_s=4.0, triggers=[], max_segments=2, name="t")
    assert len(BUS._subs) == before
