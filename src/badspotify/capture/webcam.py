"""Laptop webcam + mic. The 'regular video input' path we ship first."""
from __future__ import annotations

import time
from typing import Iterator

import numpy as np

from .base import Observation
from ..log import notice as print  # stdout is reserved for data


class WebcamSource:
    name = "webcam"

    def __init__(self, cfg: dict):
        self.cfg = cfg
        self.interval = float(cfg.get("frame_interval_s", 5.0))
        self.audio_window = float(cfg.get("audio_window_s", 3.0))
        self.device = int(cfg.get("camera_index", 0))
        self.sample_rate = 16000
        self._cap = None
        self._stream = None
        self._ring: list[np.ndarray] = []

    def open(self) -> None:
        import cv2
        self._cap = cv2.VideoCapture(self.device)
        if not self._cap.isOpened():
            raise RuntimeError(f"could not open camera {self.device}")
        try:
            import sounddevice as sd

            def _cb(indata, frames, time_info, status):  # noqa: ANN001
                self._ring.append(indata[:, 0].copy())
                max_chunks = int(self.audio_window * self.sample_rate / 1024) + 2
                if len(self._ring) > max_chunks:
                    self._ring = self._ring[-max_chunks:]

            self._stream = sd.InputStream(
                samplerate=self.sample_rate, channels=1, blocksize=1024, callback=_cb
            )
            self._stream.start()
        except Exception as e:
            print(f"[capture] mic unavailable ({e}); running vision-only")

    def close(self) -> None:
        if self._cap is not None:
            self._cap.release()
        if self._stream is not None:
            try:
                self._stream.stop()
                self._stream.close()
            except Exception:
                pass

    def _audio(self) -> np.ndarray | None:
        if not self._ring:
            return None
        return np.concatenate(self._ring[-64:])

    def stream(self) -> Iterator[Observation]:
        while True:
            ok, frame = self._cap.read() if self._cap else (False, None)
            yield Observation(
                frame=frame if ok else None,
                audio=self._audio(),
                sample_rate=self.sample_rate,
                ts=time.time(),
                meta={"device": self.device},
            )
            time.sleep(self.interval)
