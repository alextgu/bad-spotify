"""Perception: ONE structured call, all fields at once.

The temptation is an agent per field (mood / speed / meter / colour). Don't.
Those fields all derive from the same frame, so four calls buys you 4x cost,
4x failure surface, and the latency of the slowest one -- for information a
single structured-output call already returns. Split agents by failure mode,
not by output field.
"""
from __future__ import annotations

import base64
import importlib.util
import json
import time
from typing import Protocol

import numpy as np

from ..config import resolve_backend
from ..resilience import call_with_timeout
from ..schemas import Meter, SceneRead, TempoFeel, Vibe
from .audio_features import AudioFeatures, to_vibe_hints
from ..log import notice as print  # stdout is reserved for data

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


#Mock scene reader

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

    #Keeps mock scenes stable long enough for the DJ to confirm them
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


#Gemini scene reader

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
        self.timeout_s = float(cfg.get("timeout_s", 4.0))
        self.retries = int(cfg.get("retries", 1))
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

            resp = call_with_timeout(
                lambda: self.client.models.generate_content(
                    model=self.model,
                    contents=[types.Content(role="user", parts=parts)],
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=RESPONSE_SCHEMA,
                        temperature=0.2,
                    ),
                ),
                self.timeout_s,
                retries=self.retries,
                label="perceive",
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
            #Uses a fallback scene when reading fails so the loop can continue
            print(f"[perceive] gemini failed ({e}) -> reusing a canned read")
            return self._fallback.read(frame, audio_features, meta)


#Local open source scene reader

MOOD_PROFILES = {
    "peaceful": (dict(valence=.78, arousal=.16, density=.25, organicness=.72), Meter.STEADY),
    "joyful": (dict(valence=.92, arousal=.66, density=.62, organicness=.68), Meter.STEADY),
    "sad": (dict(valence=.14, arousal=.20, density=.30, organicness=.62), Meter.UNKNOWN),
    "tense": (dict(valence=.22, arousal=.73, density=.65, organicness=.42), Meter.IRREGULAR),
    "energetic": (dict(valence=.75, arousal=.90, density=.78, organicness=.52), Meter.STEADY),
    "romantic": (dict(valence=.82, arousal=.30, density=.38, organicness=.74), Meter.STEADY),
    "eerie": (dict(valence=.12, arousal=.47, density=.28, organicness=.38), Meter.IRREGULAR),
    "focused": (dict(valence=.56, arousal=.28, density=.34, organicness=.48), Meter.STEADY),
    "lonely": (dict(valence=.20, arousal=.14, density=.12, organicness=.60), Meter.UNKNOWN),
    "chaotic": (dict(valence=.38, arousal=.96, density=.92, organicness=.38), Meter.IRREGULAR),
}

SCENE_LABELS = (
    "a park or nature scene",
    "a party or celebration",
    "an office or classroom",
    "a restaurant or cafe",
    "a gym or sports scene",
    "a concert or performance",
    "a street or travel scene",
    "a home or bedroom",
    "a store or shopping scene",
    "a dark or empty place",
)


def _dominant_colors(frame: np.ndarray, count: int = 3) -> list[str]:
    """Find common color groups in a small copy of the frame."""
    import cv2

    small = cv2.resize(frame, (48, 48), interpolation=cv2.INTER_AREA)
    rgb = cv2.cvtColor(small, cv2.COLOR_BGR2RGB).reshape(-1, 3)
    groups = (rgb // 64).astype(np.int16)
    values, totals = np.unique(groups, axis=0, return_counts=True)
    order = np.argsort(totals)[::-1][:count]
    colors = []
    for group in values[order]:
        center = np.clip(group * 64 + 32, 0, 255)
        colors.append("#" + "".join(f"{int(value):02X}" for value in center))
    return colors


class HuggingFacePerceiver:
    """Use a local CLIP model to score a fixed scene taxonomy."""

    backend = "huggingface"

    def __init__(self, cfg: dict, classifier=None):
        self.cfg = cfg
        self.model = cfg.get("model", "openai/clip-vit-base-patch32")
        self.device = int(cfg.get("device", -1))
        self._classifier = classifier
        self._load_error: Exception | None = None
        self._previous_gray: np.ndarray | None = None
        self._fallback = MockPerceiver()
        if classifier is None and importlib.util.find_spec("transformers") is None:
            raise ImportError("transformers is not installed")

    def reset(self) -> None:
        self._previous_gray = None

    def _load(self):
        if self._classifier is not None:
            return self._classifier
        if self._load_error is not None:
            raise self._load_error
        try:
            from transformers import pipeline
            self._classifier = pipeline(
                task="zero-shot-image-classification",
                model=self.model,
                device=self.device,
            )
            return self._classifier
        except Exception as error:
            self._load_error = error
            raise

    def _visual_features(self, frame: np.ndarray) -> tuple[float, float, list[str]]:
        import cv2

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.resize(gray, (160, 90), interpolation=cv2.INTER_AREA)
        motion = 0.0
        if self._previous_gray is not None:
            motion = float(np.mean(cv2.absdiff(gray, self._previous_gray)) / 255.0)
        self._previous_gray = gray

        sharpness = float(cv2.Laplacian(gray, cv2.CV_64F).var())
        blur = 1.0 - min(sharpness / 500.0, 1.0)
        visual_speed = min(1.0, max(motion * 4.0, blur * 0.35))
        brightness = float(np.mean(gray) / 255.0)
        return visual_speed, brightness, _dominant_colors(frame)

    @staticmethod
    def _tempo(arousal: float) -> TempoFeel:
        if arousal < .16:
            return TempoFeel.STILL
        if arousal < .34:
            return TempoFeel.SLOW
        if arousal < .58:
            return TempoFeel.WALKING
        if arousal < .82:
            return TempoFeel.BRISK
        return TempoFeel.FRANTIC

    def read(self, frame, audio_features: AudioFeatures, meta: dict) -> SceneRead:
        t0 = time.time()
        if frame is None or not getattr(frame, "size", 0):
            return self._fallback.read(frame, audio_features, meta)

        try:
            import cv2
            from PIL import Image

            labels = list(MOOD_PROFILES) + list(SCENE_LABELS)
            image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            results = self._load()(image, candidate_labels=labels)
            scores = {item["label"]: float(item["score"]) for item in results}

            mood = max(MOOD_PROFILES, key=lambda label: scores.get(label, 0.0))
            setting = max(SCENE_LABELS, key=lambda label: scores.get(label, 0.0))
            mood_total = sum(scores.get(label, 0.0) for label in MOOD_PROFILES) or 1.0
            confidence = scores.get(mood, 0.0) / mood_total

            visual_speed, frame_brightness, colors = self._visual_features(frame)
            hints = to_vibe_hints(audio_features)
            profile, default_meter = MOOD_PROFILES[mood]
            arousal = (
                profile["arousal"] * .60
                + hints["arousal_hint"] * .25
                + visual_speed * .15
            )
            density = profile["density"] * .70 + hints["density_hint"] * .30
            brightness = frame_brightness * .70 + hints["brightness_hint"] * .30

            meter = default_meter
            if audio_features.pulse_regularity > .60:
                meter = Meter.STEADY
            elif audio_features.onset_rate > 0:
                meter = Meter.IRREGULAR

            activity = "little visible movement"
            if visual_speed > .65:
                activity = "fast visible movement"
            elif visual_speed > .30:
                activity = "some visible movement"

            return SceneRead(
                setting=setting,
                activity=activity,
                social_context="unknown",
                mood_label=mood,
                vibe=Vibe(
                    valence=profile["valence"],
                    arousal=arousal,
                    density=density,
                    brightness=brightness,
                    organicness=profile["organicness"],
                ),
                tempo_feel=self._tempo(arousal),
                meter=meter,
                dominant_colors=colors,
                audio_summary=audio_features.summary(),
                confidence=max(0.0, min(1.0, confidence)),
                notes=f"CLIP mood score from {self.model}",
                source="huggingface",
                latency_ms=int((time.time() - t0) * 1000),
            )
        except Exception as error:
            print(f"[perceive] huggingface failed ({error}) -> mock")
            return self._fallback.read(frame, audio_features, meta)


def build_perceiver(cfg: dict) -> ScenePerceiver:
    requested = str(cfg.get("backend", "mock")).lower()
    if requested in {"huggingface", "local", "open_source"}:
        try:
            return HuggingFacePerceiver(cfg)
        except Exception as e:
            print(f"[perceive] huggingface init failed ({e}) -> mock")
        return MockPerceiver(cfg)

    backend = resolve_backend(requested, "GOOGLE_API_KEY", "perceive")
    if backend == "gemini":
        try:
            return GeminiPerceiver(cfg)
        except Exception as e:
            print(f"[perceive] gemini init failed ({e}) -> mock")
    return MockPerceiver(cfg)


#Text scene reader

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
