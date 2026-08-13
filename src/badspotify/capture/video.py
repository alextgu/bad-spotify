"""A video file, pretending to be a live camera.

This is the demo path. We don't have Ray-Bans, so we film something and feed
the recording in as though it were happening now. The point is that *nothing
downstream knows the difference* -- same interface, same timing, same
decisions. It is not a simulation of the product; it is the product, with a
recording where the glasses would be.

Two reasons this beats a live camera on stage:
  it is repeatable  -- the same video gives the same run, every rehearsal
  it cannot fail    -- no camera permissions, no lighting, no luck

Audio is pulled out once with ffmpeg and sliced to match each frame. Without
ffmpeg it degrades to vision-only rather than refusing to run.

    python run.py --video demo/park.mp4
    python run.py --video demo/park.mp4 --realtime    # play at true speed
"""
from __future__ import annotations

import shutil
import subprocess
import tempfile
import time
import wave
from pathlib import Path
from typing import Iterator

import numpy as np

from .base import Observation

SAMPLE_RATE = 16000


class VideoSource:
    name = "video"

    def __init__(self, cfg: dict):
        self.cfg = cfg
        self.path = Path(cfg.get("video_path") or "")
        self.interval = float(cfg.get("frame_interval_s", 5.0))
        self.audio_window = float(cfg.get("audio_window_s", 3.0))
        self.realtime = bool(cfg.get("realtime", False))
        self.loop = bool(cfg.get("loop", False))

        self._cap = None
        self._fps = 30.0
        self._frame_count = 0
        self._audio: np.ndarray | None = None
        self._tmpdir: tempfile.TemporaryDirectory | None = None

    # ----------------------------------------------------------------------

    @property
    def duration_s(self) -> float:
        if not self._frame_count or not self._fps:
            return 0.0
        return self._frame_count / self._fps

    def open(self) -> None:
        if not self.path or not self.path.exists():
            raise FileNotFoundError(
                f"video not found: {self.path!r}\n"
                "Pass one with --video, or set capture.video_path in config.yaml")

        import cv2
        self._cap = cv2.VideoCapture(str(self.path))
        if not self._cap.isOpened():
            raise RuntimeError(f"could not open {self.path} -- unsupported codec?")

        self._fps = self._cap.get(cv2.CAP_PROP_FPS) or 30.0
        self._frame_count = int(self._cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        print(f"[video] {self.path.name}: {self.duration_s:.1f}s "
              f"at {self._fps:.1f}fps, sampling every {self.interval:.1f}s")

        self._audio = self._extract_audio()
        if self._audio is None:
            print("[video] no audio track available -- running vision-only")

    def close(self) -> None:
        if self._cap is not None:
            self._cap.release()
            self._cap = None
        if self._tmpdir is not None:
            self._tmpdir.cleanup()
            self._tmpdir = None

    # ---------------------------------------------------------------- audio

    def _extract_audio(self) -> np.ndarray | None:
        if not shutil.which("ffmpeg"):
            print("[video] ffmpeg not on PATH; install it to use the video's audio")
            return None

        self._tmpdir = tempfile.TemporaryDirectory()
        wav_path = Path(self._tmpdir.name) / "audio.wav"
        cmd = [
            "ffmpeg", "-nostdin", "-loglevel", "error", "-y",
            "-i", str(self.path),
            "-vn", "-ac", "1", "-ar", str(SAMPLE_RATE), "-f", "wav",
            str(wav_path),
        ]
        try:
            subprocess.run(cmd, check=True, timeout=120,
                           stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        except subprocess.CalledProcessError as e:
            err = (e.stderr or b"").decode(errors="replace").strip().splitlines()
            hint = err[-1] if err else "unknown error"
            print(f"[video] audio extraction failed ({hint})")
            return None
        except Exception as e:
            print(f"[video] audio extraction failed ({e})")
            return None

        if not wav_path.exists() or wav_path.stat().st_size == 0:
            return None

        with wave.open(str(wav_path), "rb") as w:
            raw = w.readframes(w.getnframes())
            width = w.getsampwidth()
        if width != 2:
            print(f"[video] unexpected sample width {width}; skipping audio")
            return None

        audio = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
        print(f"[video] audio: {len(audio) / SAMPLE_RATE:.1f}s extracted")
        return audio

    def _audio_slice(self, t: float) -> np.ndarray | None:
        """The audio window ENDING at t -- what was just heard, not what's next."""
        if self._audio is None:
            return None
        end = int(t * SAMPLE_RATE)
        start = max(0, end - int(self.audio_window * SAMPLE_RATE))
        chunk = self._audio[start:end]
        return chunk if chunk.size else None

    # --------------------------------------------------------------- frames

    def _seek(self, t: float) -> np.ndarray | None:
        import cv2
        self._cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000.0)
        ok, frame = self._cap.read()
        return frame if ok else None

    def stream(self) -> Iterator[Observation]:
        t = 0.0
        index = 0
        wall_start = time.time()

        while True:
            if self.duration_s and t >= self.duration_s:
                if not self.loop:
                    print(f"[video] reached end of {self.path.name}")
                    return
                t, index, wall_start = 0.0, 0, time.time()

            frame = self._seek(t)
            if frame is None:
                if not self.loop:
                    return
                t, index, wall_start = 0.0, 0, time.time()
                continue

            yield Observation(
                frame=frame,
                audio=self._audio_slice(t),
                sample_rate=SAMPLE_RATE,
                ts=time.time(),
                meta={
                    "source": "video",
                    "file": self.path.name,
                    # video_time is what the presentation site needs: *where*
                    # in the footage this decision belongs.
                    "video_time": round(t, 2),
                    "duration": round(self.duration_s, 2),
                    "index": index,
                },
            )

            t += self.interval
            index += 1

            if self.realtime:
                target = wall_start + (index * self.interval)
                time.sleep(max(0.0, target - time.time()))
