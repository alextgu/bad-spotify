"""Shared contracts between every layer.

Design rule: the perception layer emits exactly ONE object per read.
Four "fields" (mood / speed / consistency / colour) are four keys on one
schema, not four agents. One vision call fills all of them.
"""
from __future__ import annotations

from enum import Enum
from typing import Literal, Optional

from pydantic import BaseModel, Field

# The vibe space. Every scene and every track lives in this 5-cube.
# All dims are 0..1 so distance and reflection are trivial.
VIBE_DIMS = ("valence", "arousal", "density", "brightness", "organicness")


class Vibe(BaseModel):
    valence: float = Field(0.5, ge=0, le=1, description="sad/bleak -> happy/bright")
    arousal: float = Field(0.5, ge=0, le=1, description="calm/still -> frantic")
    density: float = Field(0.5, ge=0, le=1, description="sparse/minimal -> wall of sound")
    brightness: float = Field(0.5, ge=0, le=1, description="dark timbre -> shrill/bright")
    organicness: float = Field(0.5, ge=0, le=1, description="machine/synthetic -> acoustic/human")

    def as_tuple(self) -> tuple[float, ...]:
        return tuple(getattr(self, d) for d in VIBE_DIMS)

    @classmethod
    def from_tuple(cls, t) -> "Vibe":
        return cls(**{d: float(v) for d, v in zip(VIBE_DIMS, t)})

    def distance(self, other: "Vibe") -> float:
        return sum((a - b) ** 2 for a, b in zip(self.as_tuple(), other.as_tuple())) ** 0.5


class TempoFeel(str, Enum):
    STILL = "still"
    SLOW = "slow"
    WALKING = "walking"
    BRISK = "brisk"
    FRANTIC = "frantic"


class Meter(str, Enum):
    """Consistent vs inconsistent, in your notes."""
    STEADY = "steady"          # 4/4, predictable
    SWUNG = "swung"            # jazz, shuffle
    IRREGULAR = "irregular"    # odd time, no pulse
    UNKNOWN = "unknown"


class SceneRead(BaseModel):
    """One structured perception of the world. Produced by ONE model call."""
    setting: str = Field(..., description="e.g. 'sunlit public park', 'crowded elevator'")
    activity: str = Field(..., description="what the wearer appears to be doing")
    social_context: Literal["alone", "one_other", "small_group", "crowd", "unknown"] = "unknown"
    mood_label: str = Field(..., description="short human label, e.g. 'peaceful', 'tense'")

    vibe: Vibe
    tempo_feel: TempoFeel = TempoFeel.WALKING
    meter: Meter = Meter.UNKNOWN

    dominant_colors: list[str] = Field(default_factory=list, description="hex strings")
    audio_summary: str = ""

    confidence: float = Field(0.5, ge=0, le=1)
    notes: str = ""

    # provenance
    source: Literal["mock", "gemini", "cached"] = "mock"
    latency_ms: int = 0

    def signature(self) -> str:
        """Coarse fingerprint used for hysteresis: did the scene really change?"""
        b = lambda x: int(x * 4)  # noqa: E731  quantise to 4 buckets
        return "|".join([
            self.mood_label.lower().strip(),
            self.social_context,
            self.tempo_feel.value,
            *[str(b(v)) for v in self.vibe.as_tuple()],
        ])


class AntiVibe(BaseModel):
    """Where we want the music to be: maximally, comedically wrong."""
    target: Vibe
    target_genres: list[str] = Field(default_factory=list)
    banned_genres: list[str] = Field(default_factory=list)
    strategy: str = "genre_antipode"
    rationale: str = ""


class Track(BaseModel):
    id: str
    title: str
    artist: str
    genres: list[str] = Field(default_factory=list)
    vibe: Vibe
    duration_s: Optional[float] = None
    uri: Optional[str] = None          # spotify:track:... or file path
    tags: list[str] = Field(default_factory=list)
    recognisability: float = Field(0.5, ge=0, le=1,
                                   description="the joke only lands if they know the song")


class Candidate(BaseModel):
    track: Track
    strategy: str
    raw_distance: float = 0.0
    notes: str = ""


class Verdict(BaseModel):
    """The judge's pick. Distance gives defensibility; the LLM gives the punchline."""
    track: Track
    strategy: str
    mismatch: float = Field(0.0, ge=0, le=1)
    """How far this pick sits from the scene, on the mood axes. Reported,
    never set by a user -- it is a measurement, not a setting."""
    quip: str = ""
    reasoning: str = ""
    runner_ups: list[str] = Field(default_factory=list)
    source: Literal["mock", "gemini", "fallback"] = "mock"


class PlayMode(str, Enum):
    """Queue is polite; interrupt is funny. The DJ picks per situation."""
    QUEUE = "queue"          # append -- lands after the current track
    INTERRUPT = "interrupt"  # cut in now -- the moment is still happening


class DJAction(str, Enum):
    PLAY = "play"
    HOLD = "hold"           # bounds say no
    FALLBACK = "fallback"   # something broke, chaos deck
    IDLE = "idle"


class DJDecision(BaseModel):
    action: DJAction
    verdict: Optional[Verdict] = None
    mode: PlayMode = PlayMode.QUEUE
    scene_delta: float = 0.0
    reason: str = ""
    seconds_until_eligible: float = 0.0


class PipelineEvent(BaseModel):
    """Everything the HUD renders is one of these."""
    kind: Literal[
        "capture", "gate", "scene", "antivibe", "candidates",
        "verdict", "dj", "play", "voice", "error"
    ]
    label: str
    detail: dict = Field(default_factory=dict)
    ts: float = 0.0
