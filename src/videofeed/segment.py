"""What comes out of the feed: one segment of video, ready for a model.

A Segment is the unit of handoff. It is deliberately dumb -- a frame, the audio
around it, when it happened, and *why* it was sampled. It knows nothing about
models, prompts, or what anyone plans to do with it.

`reasons` is the field worth reading. A segment sampled on the fixed cadence
carries `["interval"]`; one sampled because something happened carries the
trigger names, e.g. `["scene_cut", "audio_onset"]`. Both at once is normal and
means the cadence and a trigger landed on the same probe.
"""
from __future__ import annotations

import json
import wave
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import numpy as np


@dataclass
class Segment:
    """One sampled moment: a frame, the audio just before it, and why."""

    index: int
    """0-based, in emission order."""

    t: float
    """Seconds into the video. This is the number downstream cares about."""

    reasons: list[str]
    """Why this was sampled: "interval", or the trigger names that fired."""

    frame: Optional[np.ndarray] = None
    """HxWx3 uint8, BGR (OpenCV's order). None if the decoder gave us nothing."""

    audio: Optional[np.ndarray] = None
    """Mono float32 in [-1, 1], the window ENDING at `t`. None if no audio."""

    sample_rate: int = 16000
    audio_window_s: float = 0.0
    wall_ts: float = 0.0
    source: str = ""
    duration_s: float = 0.0

    meta: dict = field(default_factory=dict)
    """Yours. Triggers may add detail here; nothing in this package reads it."""

    # ------------------------------------------------------------- helpers --

    @property
    def has_frame(self) -> bool:
        return self.frame is not None and getattr(self.frame, "size", 0) > 0

    @property
    def has_audio(self) -> bool:
        return self.audio is not None and getattr(self.audio, "size", 0) > 0

    @property
    def triggered(self) -> bool:
        """True if anything other than the fixed cadence caused this sample."""
        return any(r != "interval" for r in self.reasons)

    def to_dict(self) -> dict:
        """JSON-safe. Arrays are described, not included."""
        h, w = (self.frame.shape[:2] if self.has_frame else (0, 0))
        return {
            "index": self.index,
            "t": round(self.t, 3),
            "reasons": list(self.reasons),
            "triggered": self.triggered,
            "wall_ts": self.wall_ts,
            "source": self.source,
            "duration_s": round(self.duration_s, 3),
            "frame": {"width": int(w), "height": int(h)} if self.has_frame else None,
            "audio": {
                "samples": int(self.audio.size),
                "sample_rate": self.sample_rate,
                "seconds": round(self.audio.size / self.sample_rate, 3),
            } if self.has_audio else None,
            "meta": self.meta,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict())

    # -------------------------------------------------------------- saving --

    def save_frame(self, path: str | Path, quality: int = 90) -> Optional[Path]:
        """Write the frame as JPEG. Returns the path, or None if there wasn't one."""
        if not self.has_frame:
            return None
        import cv2

        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(path), self.frame, [int(cv2.IMWRITE_JPEG_QUALITY), quality])
        return path

    def save_audio(self, path: str | Path) -> Optional[Path]:
        """Write the audio window as a 16-bit mono WAV."""
        if not self.has_audio:
            return None
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        pcm = np.clip(self.audio, -1.0, 1.0)
        pcm = (pcm * 32767.0).astype(np.int16)
        with wave.open(str(path), "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(self.sample_rate)
            w.writeframes(pcm.tobytes())
        return path

    def frame_jpeg(self, quality: int = 90) -> Optional[bytes]:
        """The frame as JPEG bytes, for handing straight to an API."""
        if not self.has_frame:
            return None
        import cv2

        ok, buf = cv2.imencode(".jpg", self.frame, [int(cv2.IMWRITE_JPEG_QUALITY), quality])
        return buf.tobytes() if ok else None

    def __repr__(self) -> str:  # keeps logs readable
        return (f"Segment(#{self.index} t={self.t:.2f}s "
                f"reasons={'+'.join(self.reasons)} "
                f"frame={'y' if self.has_frame else 'n'} "
                f"audio={'y' if self.has_audio else 'n'})")
