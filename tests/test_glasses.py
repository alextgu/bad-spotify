"""The glasses seam.

Apps do not run on Ray-Ban Meta. The Wearables Device Access Toolkit gives a
PHONE app the camera, mics and speakers, and that app posts frames to the
agent -- so this is a receiving end, not a driver, and the contract it has to
keep is the one a companion app will be written against.

`/phone` speaks the same protocol from a phone browser, which is what makes
this testable before anyone owns a pair.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from badspotify.capture.base import build_capture           # noqa: E402
from badspotify.capture.glasses import GlassesSource        # noqa: E402


def frame(w=64, h=48):
    return np.random.RandomState(0).randint(0, 255, (h, w, 3), np.uint8)


def test_the_factory_still_knows_it():
    assert build_capture({"source": "glasses"}).name == "glasses"


def test_a_posted_frame_reaches_the_loop():
    g = GlassesSource({})
    assert g.submit(frame()) is True

    obs = next(g.stream())
    assert obs.has_frame
    assert obs.meta["source"] == "glasses"


def test_metadata_from_the_companion_app_survives():
    """The native app knows things this process cannot -- which device, which
    lens, whether the wearer asked for it. None of it should be dropped."""
    g = GlassesSource({})
    g.submit(frame(), {"device": "ray-ban-display", "wearer_requested": True})
    meta = next(g.stream()).meta
    assert meta["device"] == "ray-ban-display"
    assert meta["wearer_requested"] is True
    assert meta["source"] == "glasses", "the source must not be overwritable"


def test_a_backlog_is_dropped_rather_than_queued():
    """Perception takes ~1.2s and a companion app posts on a timer. Queueing
    the overflow would mean answering a moment that has already passed --
    the agent would narrate the past, confidently."""
    g = GlassesSource({})
    accepted = [g.submit(frame()) for _ in range(8)]

    assert accepted[0] is True
    assert accepted.count(False) >= 5, "it queued a backlog instead of dropping"
    assert g._dropped >= 5


def test_an_idle_stream_keeps_ticking_instead_of_hanging():
    """Nobody is wearing it yet. A source that blocks forever is
    indistinguishable from a hung process, and the loop counts ticks."""
    g = GlassesSource({})
    obs = next(g.stream())            # nothing submitted
    assert obs.meta.get("idle") is True
    assert not obs.has_frame


def test_it_binds_every_interface_by_default():
    """The one device that will never be wearing the glasses is the machine
    running this, so 127.0.0.1 is the one address that cannot work."""
    assert GlassesSource({}).host == "0.0.0.0"
    assert GlassesSource({"glasses_host": "127.0.0.1"}).host == "127.0.0.1"


def test_close_is_safe_before_open():
    GlassesSource({}).close()          # must not raise


@pytest.mark.parametrize("page", ["phone.html", "live.html"])
def test_the_companion_pages_ship(page):
    static = Path(__file__).resolve().parents[1] / "src" / "badspotify" / "hud" / "static"
    assert (static / page).exists(), f"{page} is routed but not present"


def test_the_phone_page_asks_for_the_rear_camera():
    """A selfie stream is the one thing a pair of glasses can never send, so
    the stand-in must not quietly demonstrate the wrong thing."""
    static = Path(__file__).resolve().parents[1] / "src" / "badspotify" / "hud" / "static"
    html = (static / "phone.html").read_text(encoding="utf-8")
    assert "environment" in html
    assert "/api/frame" in html, "the companion app must post where the native one will"
