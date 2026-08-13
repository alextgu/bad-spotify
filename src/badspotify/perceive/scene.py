"""Perception: ONE structured call, all fields at once.

The temptation is an agent per field (mood / speed / meter / colour). Don't.
Those fields all derive from the same frame, so four calls buys you 4x cost,
4x failure surface, and the latency of the slowest one -- for information a
single structured-output call already returns. Split agents by failure mode,
not by output field.
"""
from __future__ import annotations

import base64
import json
import time
from typing import Protocol

import numpy as np

from ..config import resolve_backend
from ..schemas import Meter, SceneRead, TempoFeel, Vibe
from .audio_features import AudioFeatures, to_vibe_hints

SYSTEM_PROMPT = """You are the perception module of a wearable agent.
You receive one still frame from a body-worn camera plus numeric audio features.
Report the scene as it IS. You are NOT choosing music. You are NOT being funny.
Another module handles that. Your only job is an accurate, calibrated read.

Fill every field. Be specific about `setting` and `activity` -- downstream
comedy depends on specificity ("toddler's birthday party, cake being cut"
is useful; "indoor event" is not).

The vibe axes, all 0..1:
  valence     0 = bleak/sad,      1 = joyful/bright
  arousal     0 = still/calm,     1 = frantic/intense
  density     0 = sparse/empty,   1 = crowded/busy/overwhelming
  brightness  0 = dark/dim,       1 = glaring/bright
  organicness 0 = synthetic/manmade, 1 = natural/human/acoustic

Set `confidence` honestly. A blurry or ambiguous frame should score low --
downstream logic uses this to decide whether to act at all."""


class ScenePerceiver(Protocol):
    def read(self, frame, audio_features: AudioFeatures, meta: dict) -> SceneRead: ...


# ----------------------------------------------------------------- mock ---

_MOCK_TABLE = [
    dict(setting="sunlit public park, people reading on the grass",
         activity="walking slowly on a path", social_context="small_group",
         mood_label="peaceful", vibe=dict(valence=0.85, arousal=0.15, density=0.25,
                                          brightness=0.9, organicness=0.9),
         tempo=TempoFeel.SLOW, meter=Meter.STEADY, colors=["#8FBF6A", "#CFE8A0", "#4A7BC8"]),
    dict(setting="quiet library aisle between tall shelves",
         activity="browsing books", social_context="alone",
         mood_label="hushed", vibe=dict(valence=0.55, arousal=0.08, density=0.3,
                                        brightness=0.35, organicness=0.6),
         tempo=TempoFeel.STILL, meter=Meter.UNKNOWN, colors=["#6B5A45", "#A08C6E", "#2E2A24"]),
    dict(setting="child's birthday party, cake with candles",
         activity="singing around a table", social_context="crowd",
         mood_label="joyful", vibe=dict(valence=0.95, arousal=0.7, density=0.8,
                                        brightness=0.8, organicness=0.7),
         tempo=TempoFeel.BRISK, meter=Meter.STEADY, colors=["#FF6FA5", "#FFD166", "#7FD4F0"]),
    dict(setting="empty concrete parking garage at night",
         activity="walking alone to a car", social_context="alone",
         mood_label="uneasy", vibe=dict(valence=0.2, arousal=0.35, density=0.15,
                                        brightness=0.12, organicness=0.1),
         tempo=TempoFeel.WALKING, meter=Meter.IRREGULAR, colors=["#2B2F3A", "#4A4F5C", "#8A8F99"]),
    dict(setting="crowded coffee shop, espresso machine hissing",
         activity="waiting in line", social_context="crowd",
         mood_label="busy", vibe=dict(valence=0.6, arousal=0.55, density=0.75,
                                      brightness=0.55, organicness=0.5),
         tempo=TempoFeel.BRISK, meter=Meter.IRREGULAR, colors=["#A9714B", "#D9B48F", "#3B2A20"]),
]


class MockPerceiver:
    """Deterministic, offline, and good enough to build the whole graph against."""
    backend = "mock"

    def __init__(self, cfg: dict | None = None):
        self._i = 0

    #: how many consecutive reads return the same scene. The real world does
    #: not change every 5 seconds, and if the mock does, hysteresis can never
    #: confirm a change and nothing ever plays.
    HOLD_TICKS = 3

    def read(self, frame, audio_features: AudioFeatures, meta: dict) -> SceneRead:
        t0 = time.time()
        idx = meta.get("index", self._i)
        row = _MOCK_TABLE[(idx // self.HOLD_TICKS) % len(_MOCK_TABLE)]
        self._i += 1
        return SceneRead(
            setting=row["setting"],
            activity=row["activity"],
            social_context=row["social_context"],
            mood_label=row["mood_label"],
            vibe=Vibe(**row["vibe"]),
            tempo_feel=row["tempo"],
            meter=row["meter"],
            dominant_colors=row["colors"],
            audio_summary=audio_features.summary(),
            confidence=0.9,
            notes="mock perceiver",
            source="mock",
            latency_ms=int((time.time() - t0) * 1000),
        )


# --------------------------------------------------------------- gemini ---

RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "setting": {"type": "string"},
        "activity": {"type": "string"},
        "social_context": {"type": "string",
                           "enum": ["alone", "one_other", "small_group", "crowd", "unknown"]},
        "mood_label": {"type": "string"},
        "valence": {"type": "number"},
        "arousal": {"type": "number"},
        "density": {"type": "number"},
        "brightness": {"type": "number"},
        "organicness": {"type": "number"},
        "tempo_feel": {"type": "string",
                       "enum": ["still", "slow", "walking", "brisk", "frantic"]},
        "meter": {"type": "string", "enum": ["steady", "swung", "irregular", "unknown"]},
        "dominant_colors": {"type": "array", "items": {"type": "string"}},
        "confidence": {"type": "number"},
        "notes": {"type": "string"},
    },
    "required": ["setting", "activity", "mood_label", "valence", "arousal",
                 "density", "brightness", "organicness", "confidence"],
}


class GeminiPerceiver:
    backend = "gemini"

    def __init__(self, cfg: dict):
        from google import genai
        self.cfg = cfg
        self.model = cfg.get("model", "gemini-2.5-flash")
        self.client = genai.Client()
        self._fallback = MockPerceiver()

    @staticmethod
    def _encode(frame: np.ndarray) -> bytes:
        import cv2
        ok, buf = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
        if not ok:
            raise RuntimeError("jpeg encode failed")
        return buf.tobytes()

    def read(self, frame, audio_features: AudioFeatures, meta: dict) -> SceneRead:
        t0 = time.time()
        try:
            from google.genai import types

            hints = to_vibe_hints(audio_features)
            prompt = (
                f"{SYSTEM_PROMPT}\n\n"
                f"Audio features from the last few seconds: "
                f"{json.dumps(audio_features.as_dict())}\n"
                f"Derived hints (weak priors, override them if the image disagrees): "
                f"{json.dumps(hints)}\n"
            )
            parts = [types.Part.from_text(text=prompt)]
            if frame is not None and getattr(frame, "size", 0):
                parts.append(types.Part.from_bytes(
                    data=self._encode(frame), mime_type="image/jpeg"))

            resp = self.client.models.generate_content(
                model=self.model,
                contents=[types.Content(role="user", parts=parts)],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=RESPONSE_SCHEMA,
                    temperature=0.2,
                ),
            )
            d = json.loads(resp.text)
            return SceneRead(
                setting=d["setting"],
                activity=d.get("activity", ""),
                social_context=d.get("social_context", "unknown"),
                mood_label=d["mood_label"],
                vibe=Vibe(
                    valence=d["valence"], arousal=d["arousal"], density=d["density"],
                    brightness=d["brightness"], organicness=d["organicness"],
                ),
                tempo_feel=TempoFeel(d.get("tempo_feel", "walking")),
                meter=Meter(d.get("meter", "unknown")),
                dominant_colors=d.get("dominant_colors", []),
                audio_summary=audio_features.summary(),
                confidence=float(d.get("confidence", 0.5)),
                notes=d.get("notes", ""),
                source="gemini",
                latency_ms=int((time.time() - t0) * 1000),
            )
        except Exception as e:
            print(f"[perceive] gemini failed ({e}) -> mock read")
            return self._fallback.read(frame, audio_features, meta)


def build_perceiver(cfg: dict) -> ScenePerceiver:
    backend = resolve_backend(cfg.get("backend", "mock"), "GOOGLE_API_KEY", "perceive")
    if backend == "gemini":
        try:
            return GeminiPerceiver(cfg)
        except Exception as e:
            print(f"[perceive] gemini init failed ({e}) -> mock")
    return MockPerceiver(cfg)


# ------------------------------------------------------- text injection ---

_TEXT_RULES = [
    (("funeral", "hospital", "memorial", "grief", "vigil", "3am"),
     dict(valence=.1, arousal=.2, density=.3, brightness=.25, organicness=.6),
     "solemn", TempoFeel.SLOW, Meter.UNKNOWN, ["#3A3F4A"]),
    (("birthday", "party", "wedding", "celebration", "cake"),
     dict(valence=.92, arousal=.7, density=.8, brightness=.8, organicness=.7),
     "joyful", TempoFeel.BRISK, Meter.STEADY, ["#FF6FA5", "#FFD166"]),
    (("library", "exam", "silent", "quiet", "study"),
     dict(valence=.5, arousal=.08, density=.25, brightness=.4, organicness=.55),
     "hushed", TempoFeel.STILL, Meter.UNKNOWN, ["#6B5A45", "#A08C6E"]),
    (("park", "sunlit", "sunny", "beach", "picnic", "grass"),
     dict(valence=.85, arousal=.15, density=.25, brightness=.9, organicness=.9),
     "peaceful", TempoFeel.SLOW, Meter.STEADY, ["#8FBF6A", "#CFE8A0"]),
    (("garage", "alley", "night", "empty", "alone", "dark"),
     dict(valence=.2, arousal=.35, density=.15, brightness=.12, organicness=.15),
     "uneasy", TempoFeel.WALKING, Meter.IRREGULAR, ["#2B2F3A", "#4A4F5C"]),
    (("date", "candlelit", "romantic", "dinner"),
     dict(valence=.75, arousal=.25, density=.35, brightness=.35, organicness=.8),
     "intimate", TempoFeel.SLOW, Meter.STEADY, ["#7A2E3A", "#D9A25F"]),
    (("gym", "run", "workout", "training"),
     dict(valence=.7, arousal=.85, density=.7, brightness=.7, organicness=.5),
     "driven", TempoFeel.FRANTIC, Meter.STEADY, ["#222", "#E24"]),
    (("meeting", "office", "interview", "presentation", "desk"),
     dict(valence=.5, arousal=.4, density=.45, brightness=.6, organicness=.35),
     "professional", TempoFeel.WALKING, Meter.STEADY, ["#8892A0", "#D7DBE0"]),
]


def scene_from_text(text: str) -> SceneRead:
    """Build a SceneRead from a typed description.

    Powers the stage button: no camera, no network, fully deterministic,
    and it exercises the exact same downstream graph as a real frame.
    """
    low = text.lower()
    for keywords, vibe, mood, tempo, meter, colors in _TEXT_RULES:
        if any(k in low for k in keywords):
            return SceneRead(
                setting=text, activity="injected scene", social_context="unknown",
                mood_label=mood, vibe=Vibe(**vibe), tempo_feel=tempo, meter=meter,
                dominant_colors=colors, audio_summary="(injected, no audio)",
                confidence=0.95, notes="scene injection", source="mock",
            )
    return SceneRead(
        setting=text, activity="injected scene", social_context="unknown",
        mood_label="neutral", vibe=Vibe(), tempo_feel=TempoFeel.WALKING,
        meter=Meter.UNKNOWN, dominant_colors=[],
        audio_summary="(injected, no audio)", confidence=0.9,
        notes="scene injection (no rule matched)", source="mock",
    )
