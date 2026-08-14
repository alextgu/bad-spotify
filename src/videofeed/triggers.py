"""Triggers: the reason to sample *between* the fixed ticks.

A fixed cadence alone is a bad sampler. Set it slow and you miss the moment
someone walks in; set it fast and you pay for a model call every few seconds on
footage where nothing happened. So the feed does both: it samples on a cadence,
and it samples when something changes.

A trigger is anything with a `name` and a `check(probe) -> bool`. That is the
whole contract -- write your own:

    def someone_shouted(probe):
        return probe.rms > 0.3

    feed = VideoFeed("clip.mp4", triggers=[
        SceneCut(),
        AudioOnset(),
        FunctionTrigger("shouted", someone_shouted),
    ])

Triggers see a *probe*, not a segment: a cheap, downsampled look at the video
several times a second. They are called on every probe, so keep them fast --
anything that would cost a model call belongs downstream, not here.

Triggers are stateful on purpose (most compare against what they saw last), so
one instance belongs to one feed. Don't share them between runs; call `reset()`
if you must.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional, Protocol

import numpy as np


@dataclass
class Probe:
    """One cheap look at the video. Handed to every trigger, several times a second."""

    t: float
    """Seconds into the video."""

    index: int
    """0-based probe counter."""

    dt: float
    """Seconds since the previous probe."""

    gray: np.ndarray
    """Downsampled greyscale frame, float32 0..1. Small (32x32 by default)."""

    frame: Optional[np.ndarray] = None
    """The full-resolution BGR frame, if you really need it."""

    audio: Optional[np.ndarray] = None
    """The audio window ending at `t`, mono float32. None if the clip is silent."""

    sample_rate: int = 16000

    @property
    def rms(self) -> float:
        if self.audio is None or self.audio.size == 0:
            return 0.0
        return float(np.sqrt(np.mean(np.square(self.audio))))

    @property
    def brightness(self) -> float:
        return float(self.gray.mean()) if self.gray is not None else 0.0


class Trigger(Protocol):
    """Anything that can say "sample now"."""

    name: str

    def check(self, probe: Probe) -> bool: ...

    def reset(self) -> None: ...


# --------------------------------------------------------------------------
# built-ins
# --------------------------------------------------------------------------


class _Base:
    """Shared plumbing. Subclasses implement `check`."""

    name = "trigger"

    def reset(self) -> None:
        pass

    def __repr__(self) -> str:
        return f"<{type(self).__name__} name={self.name!r}>"


class SceneCut(_Base):
    """The picture changed a lot since the last probe.

    A hard cut, someone walking into frame, the lights going out. Compares mean
    absolute pixel difference on the downsampled greyscale, so it costs
    microseconds and is blind to noise and small camera shake.

    threshold is in 0..1. 0.10 is twitchy, 0.30 is only real cuts.
    """

    def __init__(self, threshold: float = 0.18, name: str = "scene_cut"):
        self.threshold = float(threshold)
        self.name = name
        self._prev: Optional[np.ndarray] = None
        self.last_value = 0.0

    def check(self, probe: Probe) -> bool:
        prev, self._prev = self._prev, probe.gray
        if prev is None or prev.shape != probe.gray.shape:
            return False
        self.last_value = float(np.abs(probe.gray - prev).mean())
        return self.last_value >= self.threshold

    def reset(self) -> None:
        self._prev = None


class MotionSpike(_Base):
    """Movement well above this clip's own baseline.

    SceneCut answers "did it change a lot?"; this answers "did it change a lot
    *for this footage*?" -- which is what you want on a handheld shot that is
    always a bit noisy, or a locked-off shot where any motion is an event.
    """

    def __init__(self, ratio: float = 2.5, history: int = 40,
                 min_delta: float = 0.01, name: str = "motion_spike"):
        self.ratio = float(ratio)
        self.history = int(history)
        self.min_delta = float(min_delta)
        self.name = name
        self._prev: Optional[np.ndarray] = None
        self._deltas: list[float] = []
        self.last_value = 0.0

    def check(self, probe: Probe) -> bool:
        prev, self._prev = self._prev, probe.gray
        if prev is None or prev.shape != probe.gray.shape:
            return False
        delta = float(np.abs(probe.gray - prev).mean())
        self.last_value = delta
        self._deltas.append(delta)
        self._deltas = self._deltas[-self.history:]
        if len(self._deltas) < 5 or delta < self.min_delta:
            return False
        median = float(np.median(self._deltas)) or 1e-6
        return delta / median >= self.ratio


class AudioOnset(_Base):
    """It got suddenly louder than this clip has been.

    Ratio against the rolling median rather than an absolute threshold, so it
    works on a quiet library and a loud bar without retuning. `min_rms` stops
    silence-to-barely-audible registering as an event.
    """

    def __init__(self, ratio: float = 1.8, history: int = 40,
                 min_rms: float = 0.02, name: str = "audio_onset"):
        self.ratio = float(ratio)
        self.history = int(history)
        self.min_rms = float(min_rms)
        self.name = name
        self._history: list[float] = []
        self.last_value = 0.0

    def check(self, probe: Probe) -> bool:
        rms = probe.rms
        self.last_value = rms
        self._history.append(rms)
        self._history = self._history[-self.history:]
        if len(self._history) < 5 or rms < self.min_rms:
            return False
        median = float(np.median(self._history)) or 1e-6
        return rms / median >= self.ratio

    def reset(self) -> None:
        self._history.clear()


class AudioDrop(_Base):
    """It went quiet. The room holding its breath is as much an event as a bang."""

    def __init__(self, ratio: float = 0.35, history: int = 40,
                 min_prev_rms: float = 0.05, name: str = "audio_drop"):
        self.ratio = float(ratio)
        self.history = int(history)
        self.min_prev_rms = float(min_prev_rms)
        self.name = name
        self._history: list[float] = []

    def check(self, probe: Probe) -> bool:
        rms = probe.rms
        self._history.append(rms)
        self._history = self._history[-self.history:]
        if len(self._history) < 5:
            return False
        median = float(np.median(self._history[:-1])) or 1e-6
        if median < self.min_prev_rms:
            return False
        return rms / median <= self.ratio

    def reset(self) -> None:
        self._history.clear()


class BrightnessShift(_Base):
    """The lights changed: indoors to outdoors, house lights down, sunset."""

    def __init__(self, delta: float = 0.12, name: str = "brightness_shift"):
        self.delta = float(delta)
        self.name = name
        self._prev: Optional[float] = None

    def check(self, probe: Probe) -> bool:
        prev, self._prev = self._prev, probe.brightness
        if prev is None:
            return False
        return abs(probe.brightness - prev) >= self.delta

    def reset(self) -> None:
        self._prev = None


class FunctionTrigger(_Base):
    """Wrap any `probe -> bool` callable. The escape hatch for your own rules."""

    def __init__(self, name: str, fn: Callable[[Probe], bool],
                 on_reset: Optional[Callable[[], None]] = None):
        self.name = name
        self.fn = fn
        self.on_reset = on_reset

    def check(self, probe: Probe) -> bool:
        return bool(self.fn(probe))

    def reset(self) -> None:
        if self.on_reset is not None:
            self.on_reset()


# Names for the CLI and for config files, so nobody has to import classes to
# pick a trigger. Keep in sync with the classes above.
BUILTIN_TRIGGERS: dict[str, Callable[[], Trigger]] = {
    "scene-cut": SceneCut,
    "motion-spike": MotionSpike,
    "audio-onset": AudioOnset,
    "audio-drop": AudioDrop,
    "brightness-shift": BrightnessShift,
}


def build_triggers(names: list[str] | str) -> list[Trigger]:
    """["scene-cut", "audio-onset"] -> instances. Unknown names raise."""
    if isinstance(names, str):
        names = [n.strip() for n in names.split(",") if n.strip()]
    out: list[Trigger] = []
    for n in names:
        key = n.strip().lower().replace("_", "-")
        if key not in BUILTIN_TRIGGERS:
            raise ValueError(
                f"unknown trigger {n!r}. Available: {', '.join(sorted(BUILTIN_TRIGGERS))}")
        out.append(BUILTIN_TRIGGERS[key]())
    return out
