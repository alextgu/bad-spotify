"""Whatever is on your screen, treated as the camera.

The point of this one is that it needs no hardware. Put a video call, a film,
a game or a shared window on screen and the agent reads it exactly as it reads
a webcam -- same Observation, same gate, same pipeline. It is also the easiest
way to try the thing on footage you can't point a camera at.

It does NOT capture system audio. `Stereo Mix`-style loopback devices can do
that, but they are off by default on most Windows machines and silently absent
on others, so the honest default is vision-only: the audio features degrade to
zeros and the scene read leans on the image, which is what happens without
ffmpeg too.
"""
from __future__ import annotations

import time
from typing import Iterator

import numpy as np

from .base import Observation
from ..log import notice as print  # stdout is reserved for data


class ScreenSource:
    name = "screen"

    def __init__(self, cfg: dict):
        self.cfg = cfg
        self.interval = float(cfg.get("frame_interval_s", 5.0))
        #A region as [left, top, right, bottom]; blank means the whole screen.
        self.region = cfg.get("screen_region") or None
        #Downscale before anything sees it. A 4K grab is ~8x the pixels the
        #model needs and makes the frame diff in the gate needlessly slow.
        self.max_width = int(cfg.get("screen_max_width", 960))
        self._grab = None

    def open(self) -> None:
        try:
            from PIL import ImageGrab
        except Exception as e:                      #pragma: no cover - env dep
            raise RuntimeError(
                "screen capture needs Pillow (it ships with the requirements). "
                f"Import failed: {e}") from e

        self._grab = ImageGrab
        shot = self._capture()
        if shot is None:
            raise RuntimeError(
                "screen capture returned nothing. On macOS, grant Screen "
                "Recording permission to your terminal and try again.")
        h, w = shot.shape[:2]
        where = f"region {self.region}" if self.region else "full screen"
        print(f"[screen] {where}, sampling every {self.interval:.1f}s "
              f"at {w}x{h} (vision-only, no system audio)")

    def close(self) -> None:
        self._grab = None

    def _capture(self) -> np.ndarray | None:
        import cv2

        try:
            img = self._grab.grab(bbox=tuple(self.region) if self.region else None)
        except Exception as e:
            print(f"[screen] grab failed: {e}")
            return None
        frame = np.array(img)[:, :, :3]              #RGBA -> RGB, drop alpha
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)   #the rest of the app is BGR
        if self.max_width and frame.shape[1] > self.max_width:
            scale = self.max_width / frame.shape[1]
            frame = cv2.resize(frame, (self.max_width,
                                       int(frame.shape[0] * scale)),
                               interpolation=cv2.INTER_AREA)
        return frame

    def stream(self) -> Iterator[Observation]:
        started = time.time()
        while True:
            frame = self._capture()
            if frame is not None:
                yield Observation(
                    frame=frame,
                    audio=None,
                    ts=time.time(),
                    meta={
                        "source": "screen",
                        "region": self.region,
                        #Handy for the HUD and for recorded sessions: how long
                        #this run has been going, the way `video_time` reads.
                        "video_time": round(time.time() - started, 2),
                    },
                )
            time.sleep(self.interval)
