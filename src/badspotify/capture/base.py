"""Capture is behind an interface so the glasses can drop in later.

Today: webcam + laptop mic, or deterministic replay for demos.
Later: Meta Wearables Device Access Toolkit (Developer Preview) streams
camera/mic off Ray-Ban Meta into a native app; that app posts frames to
GlassesSource over a local socket. Nothing above this file changes.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Iterator, Optional, Protocol

import numpy as np


@dataclass
class Observation:
    """One slice of the world: a frame plus the audio around it."""
    frame: Optional[np.ndarray] = None        # HxWx3 uint8 BGR
    audio: Optional[np.ndarray] = None        # mono float32
    sample_rate: int = 16000
    ts: float = field(default_factory=time.time)
    meta: dict = field(default_factory=dict)

    @property
    def has_frame(self) -> bool:
        return self.frame is not None and getattr(self.frame, "size", 0) > 0

    @property
    def has_audio(self) -> bool:
        return self.audio is not None and getattr(self.audio, "size", 0) > 0


class CaptureSource(Protocol):
    name: str

    def open(self) -> None: ...
    def close(self) -> None: ...
    def stream(self) -> Iterator[Observation]: ...


def build_capture(cfg: dict) -> CaptureSource:
    source = (cfg.get("source") or "replay").lower()
    if source == "webcam":
        from .webcam import WebcamSource
        return WebcamSource(cfg)
    if source == "glasses":
        from .glasses import GlassesSource
        return GlassesSource(cfg)
    from .replay import ReplaySource
    return ReplaySource(cfg)
