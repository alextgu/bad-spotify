"""A video file, pretending to be a live camera.

This is the demo path. We don't have Ray-Bans, so we film something and feed
the recording in as though it were happening now. Nothing downstream knows the
difference -- same interface, same timing, same decisions.

Two reasons this beats a live camera on stage:
  it is repeatable  -- the same video gives the same run, every rehearsal
  it cannot fail    -- no camera permissions, no lighting, no luck

**This is now a thin adapter over `src/videofeed/`.** It used to be a second,
independent video reader: its own ffmpeg call, its own frame differ, its own
audio slicing -- all near-copies of what lived elsewhere. Two implementations
of the same thing drift, and then the demo behaves differently from the thing
we tested. `videofeed` is the better of the two and it is separately tested, so
this file adapts it rather than competing with it.

`videofeed` also samples on **events** -- a scene cut, a spike in the audio --
not only on a fixed clock. So a five-second cadence no longer means we miss the
door opening at second three.

    python run.py --video demo/park.mp4
    python run.py --video demo/park.mp4 --realtime    # play at true speed
"""
from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import Iterator

from ..log import notice as print
from .base import Observation

# videofeed is a sibling package under src/, deliberately independent of
# badspotify -- it knows nothing about scenes, songs or agents.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

DEFAULT_TRIGGERS = "scene-cut,audio-onset"

#: What videofeed calls a sample taken because the clock said so, rather than
#: because anything happened. Must match `reasons.append(...)` in feed.py.
CADENCE_REASON = "interval"


class VideoSource:
    name = "video"

    def __init__(self, cfg: dict):
        self.cfg = cfg
        self.path = Path(cfg.get("video_path") or "")
        self.interval = float(cfg.get("frame_interval_s", 5.0))
        self.audio_window = float(cfg.get("audio_window_s", 3.0))
        self.realtime = bool(cfg.get("realtime", False))
        self.trigger_names = cfg.get("triggers", DEFAULT_TRIGGERS)
        self._feed = None

    @property
    def duration_s(self) -> float:
        return getattr(self._feed, "duration_s", 0.0) or 0.0

    def open(self) -> None:
        if not self.path or not self.path.exists():
            raise FileNotFoundError(
                f"video not found: {self.path!r}\n"
                "Pass one with --video, or set capture.video_path in config.yaml")

        from videofeed import VideoFeed, build_triggers

        names = ([t.strip() for t in self.trigger_names.split(",") if t.strip()]
                 if isinstance(self.trigger_names, str) else list(self.trigger_names))
        triggers = build_triggers(names) if names else []

        self._feed = VideoFeed(
            self.path,
            interval_s=self.interval,
            audio_window_s=self.audio_window,
            triggers=triggers,
            realtime=self.realtime,
            verbose=False,
        )
        self._feed.open()
        print(f"[video] {self.path.name}: {self.duration_s:.1f}s, "
              f"every {self.interval:.1f}s plus {', '.join(names) or 'no'} triggers")

    def close(self) -> None:
        if self._feed is not None:
            self._feed.close()
            self._feed = None

    def stream(self) -> Iterator[Observation]:
        for seg in self._feed.segments():
            # `reasons` says WHY this moment was sampled. If a trigger fired,
            # the world demonstrably changed and the cheap local gate would
            # only be re-deriving what videofeed already knows -- so we mark it
            # pre-gated and let the graph skip straight to perception. A plain
            # cadence sample stays ungated: the gate still decides.
            # "interval" is videofeed's word for a plain cadence sample --
            # anything else in `reasons` is an actual event.
            triggered = [r for r in seg.reasons if r != CADENCE_REASON]

            yield Observation(
                frame=seg.frame,
                audio=seg.audio,
                sample_rate=seg.sample_rate,
                ts=time.time(),
                meta={
                    "source": "video",
                    "file": self.path.name,
                    # where in the footage this decision belongs -- the
                    # presentation site places its timeline off this
                    "video_time": round(seg.t, 2),
                    "duration": round(self.duration_s, 2),
                    "index": seg.index,
                    "reasons": list(seg.reasons),
                    "pre_gated": bool(triggered),
                    "trigger": ", ".join(triggered) or None,
                },
            )
        print(f"[video] reached end of {self.path.name}")
