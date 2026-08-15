"""Deterministic replay source.

This is the most important file in the repo on demo day. Live webcam +
live network + a stage = one of them will betray you. Replay lets you press
one button and get the exact same run every time, and it lets you develop
the whole graph on a plane.

Layout:
    data/replay/<scene>/
        scene.json          # optional ground-truth hints for the mock backend
        0001.jpg 0002.jpg   # frames, in order
        audio.wav           # optional; sliced to match frame timing

With no directory present it synthesises frames so the repo runs on a fresh
clone with nothing downloaded.
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Iterator

import numpy as np

from .base import Observation

SYNTHETIC_SCENES = [
    {"label": "sunlit park, people reading", "rgb": (150, 200, 120), "noise": 0.02},
    {"label": "quiet library aisle", "rgb": (120, 110, 95), "noise": 0.01},
    {"label": "birthday party, cake", "rgb": (230, 180, 200), "noise": 0.25},
    {"label": "empty parking garage at night", "rgb": (40, 42, 55), "noise": 0.05},
    {"label": "crowded coffee shop", "rgb": (160, 130, 100), "noise": 0.18},
]


class ReplaySource:
    name = "replay"

    def __init__(self, cfg: dict):
        self.cfg = cfg
        self.interval = float(cfg.get("frame_interval_s", 5.0))
        self.dir = Path(cfg.get("replay_dir") or "")
        self.realtime = bool(cfg.get("replay_realtime", False))
        self.loop = bool(cfg.get("replay_loop", True))
        self._frames: list[Path] = []
        self._hints: dict = {}

    def open(self) -> None:
        if self.dir and self.dir.exists():
            self._frames = sorted(
                p for p in self.dir.iterdir()
                if p.suffix.lower() in {".jpg", ".jpeg", ".png"}
            )
            hint_file = self.dir / "scene.json"
            if hint_file.exists():
                self._hints = json.loads(hint_file.read_text(encoding="utf-8"))

    def close(self) -> None:
        pass

    def _synthetic(self, i: int) -> Observation:
        spec = SYNTHETIC_SCENES[i % len(SYNTHETIC_SCENES)]
        rng = np.random.default_rng(i)  #Keeps each generated frame repeatable
        base = np.array(spec["rgb"], dtype=np.float32)
        frame = np.tile(base, (240, 320, 1))
        frame += rng.normal(0, 12, frame.shape)
        frame = np.clip(frame, 0, 255).astype(np.uint8)

        n = 16000 * 3
        audio = rng.normal(0, spec["noise"], n).astype(np.float32)
        return Observation(
            frame=frame,
            audio=audio,
            sample_rate=16000,
            ts=time.time(),
            meta={"synthetic": True, "hint": spec["label"], "index": i},
        )

    def _from_disk(self, i: int) -> Observation:
        import cv2  #Loads OpenCV only when image files are used
        path = self._frames[i % len(self._frames)]
        frame = cv2.imread(str(path))
        return Observation(
            frame=frame,
            audio=None,
            ts=time.time(),
            meta={"path": str(path), "hint": self._hints.get("hint", ""), "index": i},
        )

    def stream(self) -> Iterator[Observation]:
        i = 0
        while True:
            yield self._from_disk(i) if self._frames else self._synthetic(i)
            i += 1
            if self._frames and not self.loop and i >= len(self._frames):
                return
            if self.realtime:
                time.sleep(self.interval)
