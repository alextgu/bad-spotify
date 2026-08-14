"""Video-as-live and session export. No real video file needed for most of it."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from badspotify.bus import BUS                      # noqa: E402
from badspotify.capture.base import build_capture   # noqa: E402
from badspotify.session import SessionRecorder      # noqa: E402


def test_video_source_is_selectable():
    src = build_capture({"source": "video", "video_path": "nope.mp4"})
    assert src.name == "video"


def test_missing_video_fails_with_a_useful_message():
    src = build_capture({"source": "video", "video_path": "definitely-not-here.mp4"})
    try:
        src.open()
    except FileNotFoundError as e:
        assert "--video" in str(e), "error should say how to fix it"
    else:
        raise AssertionError("opening a missing video should fail")


def test_recorder_builds_a_moment_from_the_event_stream():
    rec = SessionRecorder(name="t", source="clip.mp4")
    BUS.subscribe(rec._on_event)

    BUS.emit("scene", "peaceful", video_time=3.0, setting="a park",
             activity="sitting", confidence=0.9, vibe={"valence": 0.9})
    BUS.emit("antivibe", "because it is calm", target={"valence": 0.1},
             target_genres=["funeral doom"])
    BUS.emit("candidates", "genre_antipode", picks=[{"title": "Bodies"}])
    BUS.emit("verdict", "Bodies", artist="Drowning Pool", quip="You looked comfortable.",
             strategy="genre_antipode", mismatch=0.9, reasoning="maximally wrong")
    BUS.emit("play", "Bodies - Drowning Pool", video_time=8.0, mode="interrupt",
             track_id="bodies", genres=["nu metal"])

    assert len(rec.moments) == 1
    m = rec.moments[0]
    assert m["scene"]["setting"] == "a park"
    assert m["chosen"]["quip"] == "You looked comfortable."
    assert m["opposite"]["looking_for"] == ["funeral doom"]
    # the timeline must use when it PLAYED, not when the scene was read
    assert m["played"]["at_video_time"] == 8.0
    assert m["video_time"] == 3.0


def test_a_moment_that_never_plays_is_not_recorded():
    """Half-finished decisions are false starts, not moments."""
    rec = SessionRecorder(name="t2")
    BUS.subscribe(rec._on_event)
    BUS.emit("scene", "peaceful", setting="a park")
    BUS.emit("verdict", "Bodies", artist="Drowning Pool")
    BUS.emit("scene", "tense", setting="a garage")   # new scene, old one abandoned
    assert rec.moments == []


def test_export_is_self_describing():
    rec = SessionRecorder(name="t3", source="clip.mp4")
    BUS.subscribe(rec._on_event)
    BUS.emit("scene", "peaceful", video_time=0.0, setting="a park")
    BUS.emit("verdict", "Bodies", artist="Drowning Pool", quip="hi")
    BUS.emit("play", "Bodies", video_time=1.0, mode="queue", track_id="bodies")

    out = rec.to_dict()
    assert out["moment_count"] == 1
    assert "at_video_time" in out["README"], "the file should explain itself"
    assert out["moments"][0]["played"]["mode"] == "queue"
