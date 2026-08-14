"""videofeed: sampling a real file, on cadence and on triggers.

These build an actual mp4 with OpenCV and walk it, rather than mocking the
decoder -- the failure modes worth catching here (a codec that won't seek, a
trigger that fires on every probe, audio windows off by a second) only show up
against a real file.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from videofeed import (  # noqa: E402
    AudioOnset,
    DirectorySink,
    FunctionTrigger,
    NullHandoff,
    SceneCut,
    VideoFeed,
    build_triggers,
    run,
)

cv2 = pytest.importorskip("cv2")

FPS = 10
WIDTH, HEIGHT = 96, 64


@pytest.fixture(scope="module")
def clip(tmp_path_factory) -> Path:
    """12 seconds: dark until 6s, bright after. One hard cut, nothing else."""
    path = tmp_path_factory.mktemp("videofeed") / "clip.mp4"
    writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"mp4v"),
                             FPS, (WIDTH, HEIGHT))
    if not writer.isOpened():
        pytest.skip("no mp4v encoder available in this OpenCV build")

    for i in range(12 * FPS):
        value = 20 if i < 6 * FPS else 230
        frame = np.full((HEIGHT, WIDTH, 3), value, dtype=np.uint8)
        writer.write(frame)
    writer.release()

    if not path.exists() or path.stat().st_size == 0:
        pytest.skip("OpenCV wrote no file")
    return path


def _feed(clip: Path, **kw) -> VideoFeed:
    kw.setdefault("with_audio", False)   # the generated clip is silent
    kw.setdefault("verbose", False)
    return VideoFeed(clip, **kw)


# --------------------------------------------------------------- the cadence --


def test_samples_on_the_fixed_interval(clip):
    with _feed(clip, interval_s=2.0) as feed:
        segs = list(feed.segments())

    assert len(segs) >= 5, "12s at one sample every 2s should give ~6"
    assert all(s.reasons == ["interval"] for s in segs)
    gaps = np.diff([s.t for s in segs])
    assert all(abs(g - 2.0) < 0.5 for g in gaps), f"uneven cadence: {gaps}"


def test_first_sample_is_immediate(clip):
    """Don't make the caller wait a whole interval for the first frame."""
    with _feed(clip, interval_s=5.0) as feed:
        first = next(feed.segments())
    assert first.t < 0.5
    assert first.index == 0


def test_interval_zero_means_triggers_only(clip):
    with _feed(clip, interval_s=0.0, triggers=[SceneCut(threshold=0.3)]) as feed:
        segs = list(feed.segments())
    assert segs, "the cut should still be sampled"
    assert all("interval" not in s.reasons for s in segs)


def test_max_segments_stops_the_walk(clip):
    with _feed(clip, interval_s=1.0, max_segments=3) as feed:
        assert len(list(feed.segments())) == 3


def test_start_and_end_bound_the_walk(clip):
    with _feed(clip, interval_s=1.0, start_s=4.0, end_s=7.0) as feed:
        segs = list(feed.segments())
    assert segs
    assert all(3.9 <= s.t <= 7.1 for s in segs), [s.t for s in segs]


# --------------------------------------------------------------- the triggers --


def test_scene_cut_fires_between_ticks(clip):
    """The whole point: a slow cadence must not miss the cut at 6s."""
    with _feed(clip, interval_s=30.0, triggers=[SceneCut(threshold=0.3)]) as feed:
        segs = list(feed.segments())

    cuts = [s for s in segs if "scene_cut" in s.reasons]
    assert len(cuts) == 1, f"expected one cut, got {[s.reasons for s in segs]}"
    assert 5.8 <= cuts[0].t <= 6.5, f"cut landed at {cuts[0].t}s, expected ~6s"


def test_trigger_gap_suppresses_repeats(clip):
    """A trigger that fires constantly must not produce a segment per probe."""
    always = FunctionTrigger("always", lambda p: True)
    with _feed(clip, interval_s=0.0, triggers=[always],
               min_trigger_gap_s=2.0, probe_fps=4.0) as feed:
        segs = list(feed.segments())

    assert 4 <= len(segs) <= 7, f"gap not respected: {len(segs)} segments"
    gaps = np.diff([s.t for s in segs])
    assert all(g >= 1.9 for g in gaps), f"too close together: {gaps}"


def test_a_broken_trigger_does_not_kill_the_run(clip):
    """Silence is the only real failure -- one bad trigger shouldn't stop the walk."""
    def boom(_probe):
        raise ValueError("this trigger is broken")

    with _feed(clip, interval_s=2.0,
               triggers=[FunctionTrigger("boom", boom), SceneCut()]) as feed:
        segs = list(feed.segments())
    assert len(segs) >= 5


def test_cadence_and_trigger_can_land_together(clip):
    """Both reasons should be recorded, not one silently dropped."""
    always = FunctionTrigger("always", lambda p: True)
    with _feed(clip, interval_s=1.0, triggers=[always], min_trigger_gap_s=0.0) as feed:
        segs = list(feed.segments())
    assert any(set(s.reasons) >= {"interval", "always"} for s in segs)


def test_build_triggers_by_name():
    names = [t.name for t in build_triggers("scene-cut,audio-onset")]
    assert names == ["scene_cut", "audio_onset"]
    with pytest.raises(ValueError):
        build_triggers("does-not-exist")


def test_audio_onset_is_quiet_on_a_silent_clip(clip):
    with _feed(clip, interval_s=30.0, triggers=[AudioOnset()]) as feed:
        segs = list(feed.segments())
    assert all("audio_onset" not in s.reasons for s in segs)


# ---------------------------------------------------------------- the output --


def test_segment_carries_a_usable_frame(clip):
    with _feed(clip, interval_s=5.0) as feed:
        seg = next(feed.segments())
    assert seg.has_frame
    assert seg.frame.shape == (HEIGHT, WIDTH, 3)
    assert seg.frame_jpeg() is not None
    assert seg.to_dict()["frame"] == {"width": WIDTH, "height": HEIGHT}


def test_no_audio_track_degrades_instead_of_failing(clip):
    """A silent clip is vision-only, not an exception."""
    with _feed(clip, interval_s=5.0, with_audio=True) as feed:
        seg = next(feed.segments())
    assert seg.has_frame
    assert not seg.has_audio


def test_directory_sink_writes_a_replayable_run(clip, tmp_path):
    out = tmp_path / "run1"
    with _feed(clip, interval_s=3.0) as feed:
        segs = run(feed, [DirectorySink(out)], close_feed=False)

    lines = (out / "manifest.jsonl").read_text().strip().splitlines()
    assert len(lines) == len(segs)

    first = json.loads(lines[0])
    assert first["index"] == 0
    assert first["frame_file"] == "0000.jpg"
    assert (out / "0000.jpg").exists()
    assert first["audio_file"] is None          # silent clip


def test_null_handoff_counts_everything(clip):
    with _feed(clip, interval_s=2.0) as feed:
        sink = NullHandoff(verbose=False)
        segs = run(feed, [sink], close_feed=False)
    assert sink.count == len(segs)


def test_a_failing_handoff_does_not_stop_the_walk(clip):
    class Angry:
        name = "angry"
        def handle(self, segment):
            raise RuntimeError("no")
        def close(self):
            pass

    with _feed(clip, interval_s=2.0) as feed:
        segs = run(feed, [Angry(), NullHandoff(verbose=False)], close_feed=False)
    assert len(segs) >= 5


def test_missing_file_says_so():
    with pytest.raises(FileNotFoundError):
        VideoFeed("nope-does-not-exist.mp4", verbose=False).open()
