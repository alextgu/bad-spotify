"""The seam where a model gets plugged in. **No model lives here yet.**

Everything upstream of this file is finished: a video comes in, segments come
out. This file is the agreed shape of what happens next, so that whoever writes
the model can drop it in without touching the feed, and whoever is working on
the feed can keep working without waiting for the model.

The contract is one method:

    class MyModel:
        name = "my-model"
        def handle(self, segment) -> dict | None:
            ...                       # call whatever you like
            return {"caption": "..."}  # or None

Anything with that method works. Then:

    run(feed, [DirectorySink("out/run1"), MyModel()])

Two implementations ship here, and both are useful before any model exists:

    NullHandoff     prints one line per segment. Proves the feed is sampling
                    what you expected before anyone spends a token on it.
    DirectorySink   writes frames, audio and a JSONL manifest to disk. That
                    directory is a complete, replayable record of a run.

`run()` never lets one handler's failure kill the walk -- a model that
rate-limits or a disk that fills up should cost you that segment, not the
session.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, Optional, Protocol

from .segment import Segment


class Handoff(Protocol):
    """Anything that wants to be handed each segment."""

    name: str

    def handle(self, segment: Segment) -> Optional[dict]: ...

    def close(self) -> None: ...


class NullHandoff:
    """Prints what it was given. The default, and the thing to check first.

    This is not a placeholder to delete when the model arrives -- it's how you
    tell whether the *sampler* is right, independently of whether the model is.
    """

    name = "null"

    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self.count = 0

    def handle(self, segment: Segment) -> Optional[dict]:
        self.count += 1
        if self.verbose:
            why = "+".join(segment.reasons)
            audio = (f"{segment.audio.size / segment.sample_rate:.1f}s audio"
                     if segment.has_audio else "no audio")
            shape = f"{segment.frame.shape[1]}x{segment.frame.shape[0]}" \
                if segment.has_frame else "no frame"
            print(f"[handoff] #{segment.index:>3} t={segment.t:7.2f}s  "
                  f"{why:<28} {shape:>10}  {audio}")
        return None

    def close(self) -> None:
        if self.verbose:
            print(f"[handoff] {self.count} segments seen. No model wired up yet.")


class DirectorySink:
    """Writes a run to disk: frames, audio windows, and a JSONL manifest.

    out/
      0000.jpg 0000.wav
      0001.jpg 0001.wav
      manifest.jsonl        one Segment.to_dict() per line, plus the file names

    The manifest is append-only and flushed per segment, so a run that dies
    halfway still leaves a usable record.
    """

    name = "directory"

    def __init__(self, out_dir: str | Path, *, frames: bool = True,
                 audio: bool = True, jpeg_quality: int = 90):
        self.dir = Path(out_dir)
        self.dir.mkdir(parents=True, exist_ok=True)
        self.frames = frames
        self.audio = audio
        self.jpeg_quality = jpeg_quality
        self._manifest = (self.dir / "manifest.jsonl").open("a", encoding="utf-8")

    def handle(self, segment: Segment) -> Optional[dict]:
        stem = f"{segment.index:04d}"
        record = segment.to_dict()

        if self.frames:
            p = segment.save_frame(self.dir / f"{stem}.jpg", self.jpeg_quality)
            record["frame_file"] = p.name if p else None
        if self.audio:
            p = segment.save_audio(self.dir / f"{stem}.wav")
            record["audio_file"] = p.name if p else None

        self._manifest.write(json.dumps(record) + "\n")
        self._manifest.flush()
        return record

    def close(self) -> None:
        if not self._manifest.closed:
            self._manifest.close()


class CallableHandoff:
    """Wrap a plain function. `run(feed, [CallableHandoff("mine", fn)])`."""

    def __init__(self, name, fn):
        self.name = name
        self.fn = fn

    def handle(self, segment: Segment) -> Optional[dict]:
        return self.fn(segment)

    def close(self) -> None:
        pass


def run(feed, handoffs: Iterable[Handoff] = (), *, close_feed: bool = True) -> list[Segment]:
    """Walk the feed, hand every segment to every handler, return the segments.

    One handler raising is logged and skipped: a flaky model or a full disk
    costs you that segment, not the run.
    """
    handoffs = list(handoffs) or [NullHandoff()]
    seen: list[Segment] = []
    try:
        for segment in feed.segments():
            seen.append(segment)
            for h in handoffs:
                try:
                    h.handle(segment)
                except Exception as e:  # noqa: BLE001 - deliberately broad
                    print(f"[videofeed] handoff {getattr(h, 'name', h)!r} failed "
                          f"on segment #{segment.index}: {e!r}")
    finally:
        for h in handoffs:
            try:
                h.close()
            except Exception:  # noqa: BLE001
                pass
        if close_feed:
            feed.close()
    return seen
