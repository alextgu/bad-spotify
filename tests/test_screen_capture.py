"""Screen capture: whatever is on the display, treated as the camera.

The point of this source is that it needs no hardware, so the thing that must
not break is the contract -- it has to hand the pipeline the same `Observation`
a webcam does, or everything downstream quietly gets nothing.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from badspotify.capture.base import build_capture           # noqa: E402
from badspotify.capture.screen import ScreenSource          # noqa: E402


class FakeGrab:
    """Stands in for PIL.ImageGrab -- tests must not depend on a display."""

    def __init__(self, size=(1600, 900)):
        self.size = size
        self.calls = []

    def grab(self, bbox=None):
        self.calls.append(bbox)
        w, h = self.size
        if bbox:
            w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
        #RGBA, like a real grab
        return np.random.RandomState(0).randint(0, 255, (h, w, 4), dtype=np.uint8)


def source(**cfg):
    s = ScreenSource({"frame_interval_s": 0.01, **cfg})
    s._grab = FakeGrab()
    return s


def test_the_factory_knows_the_screen_source():
    assert build_capture({"source": "screen"}).name == "screen"


def test_a_grab_becomes_a_usable_observation():
    s = source()
    obs = next(s.stream())
    assert obs.has_frame, "the pipeline gets nothing to look at"
    assert obs.meta["source"] == "screen"


def test_the_frame_is_three_channel_bgr():
    """A raw grab is RGBA. Handing four channels downstream breaks the jpeg
    encode on the way to the model, and hands the colour extractor a channel
    that isn't a colour."""
    s = source()
    frame = next(s.stream()).frame
    assert frame.ndim == 3 and frame.shape[2] == 3, frame.shape
    assert frame.dtype == np.uint8


def test_a_big_screen_is_scaled_down():
    """A 4K grab is far more pixels than the model needs, and it makes the
    change gate's frame diff slow enough to matter."""
    s = source(screen_max_width=640)
    s._grab = FakeGrab(size=(3840, 2160))
    frame = next(s.stream()).frame
    assert frame.shape[1] == 640
    assert frame.shape[0] == 360, "aspect ratio was not preserved"


def test_a_small_screen_is_left_alone():
    s = source(screen_max_width=1920)
    s._grab = FakeGrab(size=(800, 600))
    assert next(s.stream()).frame.shape[1] == 800


def test_a_region_is_passed_through_to_the_grab():
    s = source(screen_region=[0, 0, 400, 300])
    next(s.stream())
    assert s._grab.calls[0] == (0, 0, 400, 300)


def test_a_failed_grab_does_not_kill_the_stream():
    """Screens lock, sessions switch, permissions get revoked mid-run. Silence
    is this project's only real bug, so a bad grab must be skipped rather than
    raised."""
    class Flaky(FakeGrab):
        def grab(self, bbox=None):
            self.calls.append(bbox)
            if len(self.calls) < 3:
                raise RuntimeError("display unavailable")
            return super().grab(bbox)

    s = source()
    s._grab = Flaky()
    obs = next(s.stream())
    assert obs.has_frame
    assert len(s._grab.calls) >= 3, "it gave up instead of trying again"


def test_video_time_advances_so_a_run_can_be_recorded():
    s = source()
    stream = s.stream()
    first = next(stream).meta["video_time"]
    second = next(stream).meta["video_time"]
    assert second >= first
