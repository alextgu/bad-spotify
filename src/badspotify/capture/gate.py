"""The change gate.

Calling a vision model every 5s regardless of whether anything happened is
the single easiest way to burn your quota and your latency budget. This runs
locally in ~1ms and answers one question: did the world change enough to be
worth an expensive opinion?

Your instinct in the notes was right (spike in audio == something happened),
but visual change matters too, so we gate on either.
"""
from __future__ import annotations

import time
from dataclasses import dataclass

import numpy as np

from .base import Observation


@dataclass
class GateVerdict:
    escalate: bool
    reason: str
    frame_delta: float = 0.0
    audio_delta: float = 0.0
    onset_ratio: float = 1.0


class ChangeGate:
    def __init__(self, cfg: dict):
        self.frame_thr = float(cfg.get("frame_diff_threshold", 0.18))
        self.audio_thr = float(cfg.get("audio_rms_delta", 0.12))
        self.onset_thr = float(cfg.get("onset_spike_ratio", 1.8))
        self.force_after = float(cfg.get("force_escalate_after_s", 45))

        self._prev_small: np.ndarray | None = None
        self._prev_rms: float | None = None
        self._rms_history: list[float] = []
        self._last_escalate: float = 0.0

    @staticmethod
    def _downsample(frame: np.ndarray, size: int = 32) -> np.ndarray:
        h, w = frame.shape[:2]
        ys = np.linspace(0, h - 1, size).astype(int)
        xs = np.linspace(0, w - 1, size).astype(int)
        small = frame[np.ix_(ys, xs)]
        if small.ndim == 3:
            small = small.mean(axis=2)
        return small.astype(np.float32) / 255.0

    def check(self, obs: Observation) -> GateVerdict:
        now = obs.ts or time.time()
        frame_delta = 0.0
        audio_delta = 0.0
        onset_ratio = 1.0

        if obs.has_frame:
            small = self._downsample(obs.frame)
            if self._prev_small is not None:
                frame_delta = float(np.abs(small - self._prev_small).mean())
            self._prev_small = small

        if obs.has_audio:
            rms = float(np.sqrt(np.mean(np.square(obs.audio.astype(np.float32)))))
            if self._prev_rms is not None:
                audio_delta = abs(rms - self._prev_rms)
            self._prev_rms = rms
            self._rms_history.append(rms)
            self._rms_history = self._rms_history[-40:]
            median = float(np.median(self._rms_history)) or 1e-6
            onset_ratio = rms / median

        elapsed = now - self._last_escalate
        reasons = []
        if frame_delta >= self.frame_thr:
            reasons.append(f"visual change {frame_delta:.3f}")
        if audio_delta >= self.audio_thr:
            reasons.append(f"audio change {audio_delta:.3f}")
        if onset_ratio >= self.onset_thr:
            reasons.append(f"audio spike x{onset_ratio:.2f}")
        if self._last_escalate == 0.0:
            reasons.append("first read")
        elif elapsed >= self.force_after:
            reasons.append(f"blind for {elapsed:.0f}s")

        escalate = bool(reasons)
        if escalate:
            self._last_escalate = now
        return GateVerdict(
            escalate=escalate,
            reason=", ".join(reasons) if reasons else "world is boring",
            frame_delta=frame_delta,
            audio_delta=audio_delta,
            onset_ratio=onset_ratio,
        )
