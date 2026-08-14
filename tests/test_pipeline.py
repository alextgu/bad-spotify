"""Tests that actually protect the demo.

Not coverage theatre -- each of these guards a specific way the live run
could embarrass us on stage.
"""
from __future__ import annotations

import sys
import time

import pytest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from badspotify.dj.controller import DJController          #noqa: E402
from badspotify.music.corpus import Corpus                 #noqa: E402
from badspotify.music.strategies import generate           #noqa: E402
from badspotify.music.vibe import build_antivibe, reflect  #noqa: E402
from badspotify.perceive.scene import scene_from_text      #noqa: E402
from badspotify.schemas import DJAction, Vibe, Verdict     #noqa: E402


def test_reflection_is_actually_opposite():
    v = Vibe(valence=.9, arousal=.1, density=.2, brightness=.95, organicness=.8)
    r = reflect(v)
    assert abs(r.valence - .1) < 1e-6
    assert abs(r.arousal - .9) < 1e-6
    assert v.distance(r) > 1.0


def test_reflection_has_no_dial():
    """Removed on purpose. The product reads a mood and inverts a mood; a knob
    labelled "how far past inappropriate to go" described something else."""
    import inspect
    assert list(inspect.signature(reflect).parameters) == ["v"], \
        "reflect() should take only a vibe -- no intensity parameter"


def test_peaceful_park_gets_something_awful():
    scene = scene_from_text("a sunlit park, people reading on the grass")
    anti = build_antivibe(scene)
    corpus = Corpus.load()
    cands = generate(scene, anti, corpus,
                     ["genre_antipode", "tempo_clash", "lyrical_irony"])
    assert cands, "no candidates generated"
    top = cands[0].track
    #The selected track should feel unpleasant for a calm scene
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
        anti = build_antivibe(scene)
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
    return Verdict(track=track, strategy="test", mismatch=.9, quip="hello")


#Queue and interrupt behavior

def test_small_scene_change_queues_instead_of_cutting():
    """A slight shift should never cut the music off."""
    from badspotify.schemas import PlayMode
    dj = DJController({"agreement_reads": 1, "cooldown_seconds": 0,
                       "min_interrupt_seconds": 15, "interrupt_threshold": 0.55})
    park = scene_from_text("a sunlit park, people reading on the grass")
    dj.commit(_verdict(), scene=park, now=time.time() - 60)

    nudged = scene_from_text("a sunlit park, people reading on the grass")
    nudged.vibe.valence -= 0.05
    d = dj.decide(nudged, _verdict("mariah"))
    assert d.action == DJAction.PLAY
    assert d.mode == PlayMode.QUEUE, f"cut the music off for a {d.scene_delta:.2f} shift"


def test_big_scene_change_interrupts_once_the_track_has_had_a_run():
    from badspotify.schemas import PlayMode
    dj = DJController({"agreement_reads": 1, "cooldown_seconds": 0,
                       "min_interrupt_seconds": 15, "interrupt_threshold": 0.55})
    park = scene_from_text("a sunlit park, people reading on the grass")
    dj.commit(_verdict(), scene=park, now=time.time() - 60)   #Track has played for sixty seconds

    funeral = scene_from_text("a hospital waiting room at 3am")
    d = dj.decide(funeral, _verdict("mariah"))
    assert d.action == DJAction.PLAY
    assert d.mode == PlayMode.INTERRUPT
    assert d.scene_delta > 0.55


def test_big_change_still_queues_if_the_track_just_started():
    """The world can change all it likes; we don't cut in after two seconds."""
    from badspotify.schemas import PlayMode
    dj = DJController({"agreement_reads": 1, "cooldown_seconds": 0,
                       "min_interrupt_seconds": 15, "interrupt_threshold": 0.55})
    park = scene_from_text("a sunlit park, people reading on the grass")
    dj.commit(_verdict(), scene=park, now=time.time() - 2)    #Track has played for two seconds

    funeral = scene_from_text("a hospital waiting room at 3am")
    d = dj.decide(funeral, _verdict("mariah"))
    assert d.mode == PlayMode.QUEUE


def test_nothing_playing_starts_immediately():
    from badspotify.schemas import PlayMode
    dj = DJController({"agreement_reads": 1})
    d = dj.decide(scene_from_text("a silent library during exam week"), _verdict())
    assert d.action == DJAction.PLAY and d.mode == PlayMode.INTERRUPT


#Timeout and retry behavior

def test_a_slow_call_is_abandoned_not_waited_on():
    """A late answer is worth less than a fast fallback. On stage, a stalled
    loop reads as the whole project being frozen."""
    import time as _t
    from badspotify.resilience import ModelTimeout, call_with_timeout
    with pytest.raises(ModelTimeout):
        call_with_timeout(lambda: _t.sleep(5), 0.2, retries=0, label="test")


def test_a_flaky_call_is_retried():
    from badspotify.resilience import call_with_timeout
    state = {"n": 0}

    def flaky():
        state["n"] += 1
        if state["n"] == 1:
            raise ConnectionError("network blip")
        return "recovered"

    assert call_with_timeout(flaky, 2.0, retries=1, backoff_s=0.01,
                             label="test") == "recovered"
    assert state["n"] == 2


def test_a_fast_call_is_unaffected():
    from badspotify.resilience import call_with_timeout
    assert call_with_timeout(lambda: 42, 2.0, label="test") == 42
