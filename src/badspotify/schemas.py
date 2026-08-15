"""Shared contracts between every layer.

Design rule: the perception layer emits exactly ONE object per read.
Four "fields" (mood / speed / consistency / colour) are four keys on one
schema, not four agents. One vision call fills all of them.
"""
from __future__ import annotations

from enum import Enum
from typing import Literal, Optional

from pydantic import BaseModel, Field

#Stores scene and track moods as five values from zero to one
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
    STEADY = "steady"          #Predictable rhythm
    SWUNG = "swung"            #Jazz or shuffle rhythm
    IRREGULAR = "irregular"    #Uneven rhythm or no clear beat
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

    #What KIND of moment this is, culturally -- the occasion and the register,
    #so a pick can be wrong about the event and not merely about the acoustics.
    #"a wedding", "a funeral", "a boardroom", "a rave", "a children's party".
    #
    #Strictly the situation, never the people in it. The project has one hard
    #rule at the top of AGENTS.md -- no notion of anyone's race, sex, religion,
    #politics or identity -- and this field is the obvious place that would
    #leak in. A wedding is an occasion; who is attending it is not our business
    #and is not what makes the joke work.
    references: list[str] = Field(
        default_factory=list,
        description="occasion / setting / cultural register of the MOMENT, "
                    "never attributes of the people in it")
    setting_attributes: list[str] = Field(
        default_factory=list,
        description="non-person traits associated with the setting, such as casual or fast")
    opposite_attributes: list[str] = Field(
        default_factory=list,
        description="semantic opposites of setting_attributes, never traits of people")
    opposite_genres: list[str] = Field(
        default_factory=list,
        description="music genres culturally associated with opposite_attributes")

    confidence: float = Field(0.5, ge=0, le=1)
    notes: str = ""

    #Source details
    source: Literal["mock", "gemini", "huggingface", "cached"] = "mock"
    latency_ms: int = 0

    def signature(self) -> str:
        """Coarse fingerprint used for hysteresis: did the scene really change?"""
        b = lambda x: int(x * 4)  #noqa: E731
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
    uri: Optional[str] = None          #Spotify track address or local file path
    tags: list[str] = Field(default_factory=list)
    recognisability: float = Field(0.5, ge=0, le=1,
                                   description="the joke only lands if they know the song")
    #Set only for tracks found outside the corpus: the specific clash that
    #earned the pick ("Madrid anthem in Barcelona"). It is shown to the
    #audience, and seeing WHY is the difference between an agent and shuffle.
    why: str = ""


class Candidate(BaseModel):
    track: Track
    strategy: str
    raw_distance: float = 0.0
    notes: str = ""


# The widest possible gap in the 5-cube: one corner to the opposite corner.
MAX_VIBE_DISTANCE = 5 ** 0.5


class Verdict(BaseModel):
    """The judge's pick. Distance gives defensibility; the LLM gives the punchline."""
    track: Track
    strategy: str
    mismatch: float = Field(
        0.0, ge=0, le=1,
        description="How far apart the moment and the music actually turned out "
                    "to be, 0-1. MEASURED after the fact -- not a setting. There "
                    "is deliberately no dial for this: an agent whose whole "
                    "premise is that it ignores you should not take a parameter "
                    "for how much to ignore you.")
    quip: str = ""
    reasoning: str = ""
    runner_ups: list[str] = Field(default_factory=list)
    source: Literal["mock", "gemini", "fallback"] = "mock"


class PlayMode(str, Enum):
    """Queue is polite; interrupt is funny. The DJ picks per situation."""
    QUEUE = "queue"          #Adds the song to the queue
    INTERRUPT = "interrupt"  #Starts the song immediately


class DJAction(str, Enum):
    PLAY = "play"
    HOLD = "hold"           #Waits without changing the music
    FALLBACK = "fallback"   #Uses an emergency music choice
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
