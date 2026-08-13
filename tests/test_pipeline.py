"""Tests that actually protect the demo.

Not coverage theatre -- each of these guards a specific way the live run
could embarrass us on stage.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from badspotify.dj.controller import DJController          # noqa: E402
from badspotify.music.corpus import Corpus                 # noqa: E402
from badspotify.music.strategies import generate           # noqa: E402
from badspotify.music.vibe import build_antivibe, reflect  # noqa: E402
from badspotify.perceive.scene import scene_from_text      # noqa: E402
from badspotify.schemas import DJAction, Vibe, Verdict     # noqa: E402


def test_reflection_is_actually_opposite():
    v = Vibe(valence=.9, arousal=.1, density=.2, brightness=.95, organicness=.8)
    r = reflect(v, 1.0)
    assert abs(r.valence - .1) < 1e-6
    assert abs(r.arousal - .9) < 1e-6
    assert v.distance(r) > 1.0


def test_cruelty_zero_is_a_normal_assistant():
    v = Vibe(valence=.9, arousal=.2)
    assert reflect(v, 0.0).as_tuple() == v.as_tuple()


def test_peaceful_park_gets_something_awful():
    scene = scene_from_text("a sunlit park, people reading on the grass")
    anti = build_antivibe(scene, 0.85)
    corpus = Corpus.load()
    cands = generate(scene, anti, corpus,
                     ["genre_antipode", "tempo_clash", "lyrical_irony"])
    assert cands, "no candidates generated"
    top = cands[0].track
    # whatever wins, it must not be a calm/pleasant record
    assert top.vibe.distance(scene.vibe) > 0.5, f"{top.title} is too appropriate"


def test_every_preset_scene_produces_candidates():
    """The stage chips must never come up empty."""
    corpus = Corpus.load()
    presets = [
        "a sunlit park, people reading on the grass",
        "a hospital waiting room at 3am",
        "a toddler's birthday party, cake being cut",
        "a silent library during exam week",
        "an empty parking garage at night",
        "a first date at a candlelit restaurant",
    ]
    for p in presets:
        scene = scene_from_text(p)
        anti = build_antivibe(scene, 0.85)
        cands = generate(scene, anti, corpus,
                         ["genre_antipode", "tempo_clash", "lyrical_irony"])
        assert cands, f"no candidates for {p!r}"


def test_hysteresis_blocks_a_single_read():
    dj = DJController({"agreement_reads": 2, "min_track_seconds": 0, "cooldown_seconds": 0})
    scene = scene_from_text("a silent library during exam week")
    v = _verdict()
    d1 = dj.decide(scene, v)
    assert d1.action == DJAction.HOLD, "acted on a single unconfirmed read"
    d2 = dj.decide(scene, v)
    assert d2.action == DJAction.PLAY


def test_commitment_blocks_thrashing():
    dj = DJController({"agreement_reads": 1, "min_track_seconds": 25, "cooldown_seconds": 8})
    scene = scene_from_text("a sunlit park")
    dj.commit(_verdict(), now=time.time())
    other = scene_from_text("a toddler's birthday party, cake being cut")
    d = dj.decide(other, _verdict("other"))
    assert d.action == DJAction.HOLD
    assert d.seconds_until_eligible > 0


def test_low_confidence_is_ignored():
    dj = DJController({"agreement_reads": 1, "min_track_seconds": 0, "cooldown_seconds": 0})
    scene = scene_from_text("a sunlit park")
    scene.confidence = 0.1
    assert dj.decide(scene, _verdict()).action == DJAction.HOLD


def test_fallback_never_returns_silence():
    dj = DJController({})
    fb = dj.fallback()
    assert fb is not None and fb.track.title


def _verdict(tid: str = "sandstorm") -> Verdict:
    corpus = Corpus.load()
    track = corpus.get(tid) or corpus.tracks[0]
    return Verdict(track=track, strategy="test", cruelty=.9, quip="hello")
