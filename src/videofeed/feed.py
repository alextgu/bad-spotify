"""The feed: a video file in, sampled segments out.

    from videofeed import VideoFeed, SceneCut, AudioOnset

    feed = VideoFeed("clip.mp4", interval_s=5.0,
                     triggers=[SceneCut(), AudioOnset()])

    for seg in feed.segments():
        print(seg)              # -> Segment(#3 t=12.50s reasons=scene_cut ...)
        seg.frame               # HxWx3 BGR
        seg.audio               # the 3 seconds before t
        # hand `seg` to a model here. That part isn't written yet.

How it works, and why:

  Decoding is **sequential**, never seeking. Seeking by timestamp is
  unreliable on a lot of real-world files (it lands on the nearest keyframe,
  which can be seconds away) and slow. We walk the file once, cheaply skipping
  frames we don't need with `grab()`.

  Several times a second we take a **probe**: a 32x32 greyscale thumbnail plus
  the audio window ending there. Probes are cheap enough to run continuously
  and are what triggers look at.

  A probe becomes a **segment** when either the cadence is due, or a trigger
  fires. That's the whole point of this file: a fixed interval alone either
  misses events or wastes model calls, so we do both.

  Triggers are rate-limited by `min_trigger_gap_s`, because the same event
  usually fires several probes in a row and nobody wants nine near-identical
  frames of the same door opening.

Audio is extracted once, up front, with ffmpeg. No ffmpeg, or no audio track:
you get vision-only segments rather than an exception. Everything degrades.
"""
from __future__ import annotations

import shutil
import subprocess
import tempfile
import time
import wave
from pathlib import Path
from typing import Iterable, Iterator, Optional

import numpy as np

from .segment import Segment
from .triggers import Probe, Trigger

DEFAULT_SAMPLE_RATE = 16000
DEFAULT_PROBE_SIZE = 32


class VideoFeed:
    """Samples a video on a fixed cadence, plus whenever a trigger fires."""

    def __init__(
        self,
        source: str | Path | int,
        *,
        interval_s: float = 5.0,
        audio_window_s: float = 3.0,
        triggers: Iterable[Trigger] = (),
        probe_fps: float = 4.0,
        min_trigger_gap_s: float = 1.5,
        start_s: float = 0.0,
        end_s: Optional[float] = None,
        max_segments: Optional[int] = None,
        sample_rate: int = DEFAULT_SAMPLE_RATE,
        with_audio: bool = True,
        realtime: bool = False,
        probe_size: int = DEFAULT_PROBE_SIZE,
        verbose: bool = True,
    ):
        """
        source            path to a video file, or an int webcam index
        interval_s        the fixed cadence. 0 disables it (triggers only)
        audio_window_s    how much audio to attach, ending at the sample point
        triggers          see triggers.py. Empty = cadence only
        probe_fps         how often triggers get to look. Higher = more
                          responsive, more CPU. 4/s is plenty for most footage
        min_trigger_gap_s ignore repeat triggers inside this window
        start_s/end_s     only sample this slice of the file
        max_segments      stop after this many. Useful in tests and demos
        with_audio        False skips the ffmpeg step entirely
        realtime          pace the walk at the video's true speed. For live
                          demos; leave False to process as fast as possible
        """
        self.source = source
        self.interval_s = float(interval_s)
        self.audio_window_s = float(audio_window_s)
        self.triggers = list(triggers)
        self.probe_fps = max(0.1, float(probe_fps))
        self.min_trigger_gap_s = float(min_trigger_gap_s)
        self.start_s = float(start_s)
        self.end_s = end_s
        self.max_segments = max_segments
        self.sample_rate = int(sample_rate)
        self.with_audio = bool(with_audio)
        self.realtime = bool(realtime)
        self.probe_size = int(probe_size)
        self.verbose = bool(verbose)

        self.fps = 0.0
        self.frame_count = 0
        self._cap = None
        self._audio: Optional[np.ndarray] = None
        self._tmpdir: Optional[tempfile.TemporaryDirectory] = None
        self._is_file = not isinstance(source, int)

    # ------------------------------------------------------------ lifecycle --

    @property
    def duration_s(self) -> float:
        if not self.frame_count or not self.fps:
            return 0.0
        return self.frame_count / self.fps

    def open(self) -> "VideoFeed":
        import cv2

        if self._is_file:
            path = Path(self.source)
            if not path.exists():
                raise FileNotFoundError(f"video not found: {path}")
            self._cap = cv2.VideoCapture(str(path))
        else:
            self._cap = cv2.VideoCapture(int(self.source))

        if not self._cap.isOpened():
            raise RuntimeError(
                f"could not open {self.source!r} — unsupported codec, or the "
                f"device is busy")

        self.fps = float(self._cap.get(cv2.CAP_PROP_FPS) or 0.0) or 30.0
        self.frame_count = int(self._cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)

        self._log(f"{self._name()}: {self.duration_s:.1f}s at {self.fps:.1f}fps, "
                  f"cadence {self.interval_s:g}s, probing {self.probe_fps:g}/s, "
                  f"triggers: {', '.join(t.name for t in self.triggers) or 'none'}")

        if self.with_audio and self._is_file:
            self._audio = self._extract_audio()
        return self

    def close(self) -> None:
        if self._cap is not None:
            self._cap.release()
            self._cap = None
        if self._tmpdir is not None:
            self._tmpdir.cleanup()
            self._tmpdir = None
        for t in self.triggers:
            t.reset()

    def __enter__(self) -> "VideoFeed":
        return self.open()

    def __exit__(self, *exc) -> None:
        self.close()

    # ---------------------------------------------------------------- audio --

    def _extract_audio(self) -> Optional[np.ndarray]:
        """One ffmpeg pass to mono PCM. Vision-only if anything goes wrong."""
        if not shutil.which("ffmpeg"):
            self._log("ffmpeg not on PATH — running vision-only")
            return None

        self._tmpdir = tempfile.TemporaryDirectory()
        wav_path = Path(self._tmpdir.name) / "audio.wav"
        cmd = [
            "ffmpeg", "-nostdin", "-loglevel", "error", "-y",
            "-i", str(self.source),
            "-vn", "-ac", "1", "-ar", str(self.sample_rate), "-f", "wav",
            str(wav_path),
        ]
        try:
            subprocess.run(cmd, check=True, timeout=300,
                           stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        except subprocess.CalledProcessError as e:
            tail = (e.stderr or b"").decode(errors="replace").strip().splitlines()
            self._log(f"no audio track ({tail[-1] if tail else 'ffmpeg failed'}) "
                      f"— running vision-only")
            return None
        except Exception as e:
            self._log(f"audio extraction failed ({e}) — running vision-only")
            return None

        if not wav_path.exists() or wav_path.stat().st_size == 0:
            return None

        with wave.open(str(wav_path), "rb") as w:
            raw = w.readframes(w.getnframes())
            width = w.getsampwidth()
        if width != 2:
            self._log(f"unexpected sample width {width} — running vision-only")
            return None

        audio = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
        self._log(f"audio: {audio.size / self.sample_rate:.1f}s")
        return audio

    def _audio_window(self, t: float) -> Optional[np.ndarray]:
        """The window ENDING at t — what was just heard, not what comes next."""
        if self._audio is None or self.audio_window_s <= 0:
            return None
        end = int(t * self.sample_rate)
        start = max(0, end - int(self.audio_window_s * self.sample_rate))
        chunk = self._audio[start:end]
        return chunk if chunk.size else None

    # --------------------------------------------------------------- probes --

    def _downsample(self, frame: np.ndarray) -> np.ndarray:
        """32x32 greyscale in 0..1. Deliberately tiny: triggers run constantly."""
        h, w = frame.shape[:2]
        n = self.probe_size
        ys = np.linspace(0, h - 1, n).astype(int)
        xs = np.linspace(0, w - 1, n).astype(int)
        small = frame[np.ix_(ys, xs)]
        if small.ndim == 3:
            small = small.mean(axis=2)
        return small.astype(np.float32) / 255.0

    # -------------------------------------------------------------- the walk --

    def segments(self) -> Iterator[Segment]:
        """Walk the video once, yielding a Segment per cadence tick or trigger."""
        if self._cap is None:
            self.open()

        probe_step = max(1, int(round(self.fps / self.probe_fps)))
        frame_no = 0
        probe_index = 0
        emitted = 0
        last_probe_t = None
        last_emit_t: Optional[float] = None
        last_trigger_t: Optional[float] = None
        wall_start = time.time()

        # Skip to start_s without seeking: cheap grabs, no decode.
        while frame_no < int(self.start_s * self.fps):
            if not self._cap.grab():
                return
            frame_no += 1

        try:
            while True:
                if self.max_segments is not None and emitted >= self.max_segments:
                    return

                ok = self._cap.grab()
                if not ok:
                    return
                t = frame_no / self.fps
                frame_no += 1

                if self.end_s is not None and t > self.end_s:
                    return
                if (frame_no - 1) % probe_step:
                    continue      # not a probe point; the grab already skipped it

                ok, frame = self._cap.retrieve()
                if not ok or frame is None:
                    continue

                audio = self._audio_window(t)
                probe = Probe(
                    t=t,
                    index=probe_index,
                    dt=(t - last_probe_t) if last_probe_t is not None else 0.0,
                    gray=self._downsample(frame),
                    frame=frame,
                    audio=audio,
                    sample_rate=self.sample_rate,
                )
                last_probe_t, probe_index = t, probe_index + 1

                reasons: list[str] = []

                # 1. the fixed cadence
                due = (self.interval_s > 0
                       and (last_emit_t is None or t - last_emit_t >= self.interval_s))
                if due:
                    reasons.append("interval")

                # 2. anything that happened in between.
                #    Every trigger is checked on every probe even when the
                #    cadence already fired -- they carry state, and skipping
                #    them would make the result depend on the cadence.
                fired = [tr.name for tr in self.triggers if _safe_check(tr, probe)]
                gap_ok = (last_trigger_t is None
                          or t - last_trigger_t >= self.min_trigger_gap_s)
                if fired and gap_ok:
                    reasons.extend(fired)
                    last_trigger_t = t

                if not reasons:
                    continue

                yield Segment(
                    index=emitted,
                    t=t,
                    reasons=reasons,
                    frame=frame,
                    audio=audio,
                    sample_rate=self.sample_rate,
                    audio_window_s=self.audio_window_s,
                    wall_ts=time.time(),
                    source=self._name(),
                    duration_s=self.duration_s,
                )
                emitted += 1
                last_emit_t = t

                if self.realtime:
                    time.sleep(max(0.0, (t - self.start_s) - (time.time() - wall_start)))
        finally:
            pass  # the caller owns close(); `with VideoFeed(...)` does it for you

    # --------------------------------------------------------------- helpers --

    def _name(self) -> str:
        return Path(str(self.source)).name if self._is_file else f"device:{self.source}"

    def _log(self, msg: str) -> None:
        if self.verbose:
            print(f"[videofeed] {msg}")


def _safe_check(trigger: Trigger, probe: Probe) -> bool:
    """A broken trigger must not take the run down with it."""
    try:
        return bool(trigger.check(probe))
    except Exception as e:  # noqa: BLE001 - deliberately broad
        print(f"[videofeed] trigger {trigger.name!r} raised {e!r}; ignoring it")
        return False
