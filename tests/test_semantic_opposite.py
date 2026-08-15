"""Model-inferred setting traits become a locally ranked opposite genre."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from badspotify.dj.controller import DJController                    # noqa: E402
from badspotify.music import strategies                              # noqa: E402
from badspotify.music.corpus import Corpus                           # noqa: E402
from badspotify.music.strategies import REGISTRY, semantic_opposite  # noqa: E402
from badspotify.music.vibe import build_antivibe                     # noqa: E402
from badspotify.perceive.audio_features import AudioFeatures         # noqa: E402
from badspotify.perceive.scene import (                              # noqa: E402
    SYSTEM_PROMPT, GeminiPerceiver, MockPerceiver,
    _clean_setting_terms, scene_from_text,
)
from badspotify.schemas import (                                     # noqa: E402
    Meter, PlayMode, SceneRead, TempoFeel, Verdict, Vibe,
)

CORPUS = Corpus.load()
FAST_FOOD = "inside a McDonald's fast food restaurant during lunch rush"
FAST_FOOD_RESPONSE = {
    "setting": "McDonald's fast food restaurant during lunch rush",
    "activity": "customers ordering and eating lunch",
    "social_context": "crowd",
    "mood_label": "busy",
    "valence": .62,
    "arousal": .68,
    "density": .72,
    "brightness": .72,
    "organicness": .2,
    "tempo_feel": "brisk",
    "meter": "steady",
    "dominant_colors": ["#E52521", "#FFC72C"],
    "references": ["fast food restaurant", "lunch rush"],
    "setting_attributes": ["inexpensive", "casual", "quick-service"],
    "opposite_attributes": ["luxurious", "formal", "leisurely"],
    "opposite_genres": ["opera", "classical"],
    "confidence": .93,
    "notes": "venue traits only",
}


def model_fast_food_scene() -> SceneRead:
    return SceneRead(
        setting=FAST_FOOD_RESPONSE["setting"],
        activity=FAST_FOOD_RESPONSE["activity"], social_context="crowd",
        mood_label="busy",
        vibe=Vibe(valence=.62, arousal=.68, density=.72,
                  brightness=.72, organicness=.2),
        tempo_feel=TempoFeel.BRISK, meter=Meter.STEADY,
        setting_attributes=FAST_FOOD_RESPONSE["setting_attributes"],
        opposite_attributes=FAST_FOOD_RESPONSE["opposite_attributes"],
        opposite_genres=FAST_FOOD_RESPONSE["opposite_genres"],
        confidence=.93, source="gemini",
    )


def test_fast_food_has_no_deterministic_lookup():
    scene = scene_from_text(FAST_FOOD)
    assert scene.mood_label == "neutral"
    assert scene.setting_attributes == []
    assert scene.opposite_attributes == []
    assert scene.opposite_genres == []
    assert "fast food" not in SYSTEM_PROMPT.lower()


def test_one_structured_model_read_builds_the_reasoning_chain(monkeypatch):
    calls = []

    class Models:
        def generate_content(self, **kwargs):
            calls.append(kwargs)
            return SimpleNamespace(text=json.dumps(FAST_FOOD_RESPONSE))

    perceiver = GeminiPerceiver.__new__(GeminiPerceiver)
    perceiver.model = "test-model"
    perceiver.timeout_s = 1
    perceiver.retries = 0
    perceiver.client = SimpleNamespace(models=Models())
    perceiver._fallback = MockPerceiver()
    monkeypatch.setattr(
        "badspotify.perceive.scene.call_with_timeout",
        lambda fn, *_args, **_kwargs: fn(),
    )

    scene = perceiver.read(
        None, AudioFeatures(), {"description": FAST_FOOD, "source": "text"})

    assert len(calls) == 1
    assert FAST_FOOD in str(calls[0]["contents"])
    assert set(scene.setting_attributes) >= {"inexpensive", "casual"}
    assert set(scene.opposite_attributes) >= {"luxurious", "formal"}
    assert scene.opposite_genres == ["opera", "classical"]


def test_semantic_strategy_is_registered_and_selects_opposite_genres():
    scene = model_fast_food_scene()
    picks = semantic_opposite(
        scene, build_antivibe(scene), CORPUS, set(), 4)

    assert REGISTRY["semantic_opposite"] is semantic_opposite
    assert picks
    assert all(
        set(genre.lower() for genre in pick.track.genres)
        & set(scene.opposite_genres)
        for pick in picks
    )
    assert "casual" in picks[0].notes
    assert "luxurious" in picks[0].notes


def test_candidate_generation_makes_no_spotify_call(monkeypatch):
    def fail(*_args, **_kwargs):
        raise AssertionError("semantic candidate generation touched Spotify")

    monkeypatch.setattr(strategies.discover, "_spotify", fail)
    scene = model_fast_food_scene()
    got = strategies.generate(
        scene, build_antivibe(scene), CORPUS, ["semantic_opposite"])
    assert got


def test_people_and_social_class_are_not_setting_attributes():
    cleaned = _clean_setting_terms([
        "inexpensive venue", "poor people", "upper class customers", "formal",
        "instrumental atmosphere",
    ])
    assert cleaned == ["inexpensive venue", "formal", "instrumental atmosphere"]


def test_engine_routes_typed_input_through_active_perception():
    from badspotify.service import Engine

    class Perceiver:
        backend = "gemini"

        def __init__(self):
            self.meta = None

        def read(self, frame, audio_features, meta):
            self.meta = meta
            return model_fast_food_scene()

    engine = Engine()
    engine.perceiver = Perceiver()
    decision = engine.describe(FAST_FOOD)

    assert engine.perceiver.meta["description"] == FAST_FOOD
    assert decision.opposite["looking_for"][:2] == ["opera", "classical"]
    assert decision.considered["semantic_opposite"]


def test_dj_reconsiders_when_only_the_semantic_genre_changes():
    scene = model_fast_food_scene()
    anti = build_antivibe(scene)
    track = CORPUS.tracks[0]
    dj = DJController({
        "agreement_reads": 2, "min_change_seconds": 0,
        "hold_threshold": .3, "jump_threshold": .55,
    })
    dj.commit(
        Verdict(track=track, strategy="test"), scene, now=0,
        mode=PlayMode.INTERRUPT, target=anti.target,
        target_genres=anti.target_genres,
    )

    changed = model_fast_food_scene()
    changed.opposite_genres = ["metal"]
    changed_anti = build_antivibe(changed)
    first, _ = dj.should_reconsider(
        changed, changed_anti.target,
        target_genres=changed_anti.target_genres, now=50)

    jitter = model_fast_food_scene()
    jitter.opposite_genres = ["jazz"]
    jitter_anti = build_antivibe(jitter)
    second, _ = dj.should_reconsider(
        jitter, jitter_anti.target,
        target_genres=jitter_anti.target_genres, now=52)
    third, why = dj.should_reconsider(
        jitter, jitter_anti.target,
        target_genres=jitter_anti.target_genres, now=54)

    assert not first
    assert not second
    assert third and "genre target changed" in why
