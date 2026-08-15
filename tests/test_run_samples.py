"""The sample runner, and the honesty of what it writes.

`scripts/run_samples.py` produces the only file on the site that claims to be
a batch of real decisions, so the thing worth guarding is not that it runs --
it is that its output can never be mistaken for something it isn't. Two of
these tests exist because the first run of it on this machine silently used
the offline reader (no GOOGLE_API_KEY) and produced a table that looked
exactly like a live one.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

SCRIPT = ROOT / "scripts" / "run_samples.py"
SCENES = ROOT / "data" / "sample_scenes.json"


@pytest.fixture(scope="module")
def spec() -> dict:
    return json.loads(SCENES.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def gallery(tmp_path_factory) -> dict:
    """One mock run, shared. Writing outside the repo is part of the test."""
    out = tmp_path_factory.mktemp("samples") / "gallery.json"
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "--backend", "mock", "--out", str(out)],
        capture_output=True, text=True, cwd=str(ROOT),
    )
    assert proc.returncode == 0, proc.stderr
    return json.loads(out.read_text(encoding="utf-8"))


# ------------------------------------------------------------------ inputs --

def test_the_scene_ids_are_unique(spec):
    """The id is the row key on the site; two rows cannot share one."""
    ids = [s["id"] for s in spec["scenes"]]
    assert len(ids) == len(set(ids))


def test_every_scene_says_why_it_is_in_the_set(spec):
    """A scene without a reason is a scene chosen because it was funny."""
    for scene in spec["scenes"]:
        assert scene.get("why_this_one", "").strip(), scene["id"]


# ----------------------------------------------------------------- outputs --

def test_it_records_one_entry_per_scene(spec, gallery):
    assert gallery["scene_count"] == len(spec["scenes"])
    assert [e["id"] for e in gallery["scenes"]] == [s["id"] for s in spec["scenes"]]


def test_it_names_the_backend_it_actually_ran_on(gallery):
    """The whole guard.

    Perception downgrades to mock when GOOGLE_API_KEY is unset, and it says so
    on stderr -- which nobody reads once the JSON exists. The file itself has
    to carry the answer, because the site decides whether to publish a row on
    it. `--backend mock` was passed, so anything but "mock" here means the
    field is being reported from configuration rather than from what was
    built.
    """
    assert gallery["backends"]["perceive"] == "mock"


def test_it_never_takes_the_speakers(gallery):
    """A file writer with a live player is a demo that plays over the demo."""
    assert gallery["backends"]["player"] == "mock"


def test_each_entry_carries_the_losers_as_well_as_the_winner(gallery):
    """A gallery of only winners is a slideshow.

    The losing candidates and their scores are what let a reader check that
    the strategies disagreed, which is the claim the wall is making.
    """
    for entry in gallery["scenes"]:
        assert entry["considered"], entry["id"]
        assert any(cands for cands in entry["considered"].values()), entry["id"]


def test_the_played_count_matches_the_entries(gallery):
    """The summary is derived, not asserted.

    `played_count` is the number the site would quote, and a summary that can
    drift from the rows underneath it is worse than no summary. This is the
    deterministic half of the independence guarantee -- the runner resets the
    engine between scenes, so every scene gets a full corpus and an action,
    rather than the later ones running out of tracks and holding.

    The tempting test here was "twelve scenes should produce some repeats,
    because a live run's exclusion set would forbid them". It would have been
    flaky: the judge samples at temperature 0.20 from an unseeded
    SystemRandom, which is exactly what made test_service flake one run in
    four before it was seeded.
    """
    played = [e for e in gallery["scenes"] if e["action"] in ("play", "fallback")]
    assert gallery["played_count"] == len(played)
    for entry in gallery["scenes"]:
        assert entry["action"], entry["id"]
