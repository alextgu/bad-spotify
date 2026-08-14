"""videofeed — sample a video into model-ready segments.

Fixed cadence *and* event triggers, with the audio around each sample, handed
to whatever you like. Nothing in here knows about any particular model.

    from videofeed import VideoFeed, SceneCut, AudioOnset, DirectorySink, run

    feed = VideoFeed("clip.mp4", interval_s=5.0,
                     triggers=[SceneCut(), AudioOnset()])
    run(feed, [DirectorySink("out/run1")])

Or from a shell:

    python -m videofeed clip.mp4 --interval 5 --triggers scene-cut,audio-onset \
        --out out/run1

See README.md in this folder. The model side is `handoff.py`, and it is
deliberately still a stub.
"""
from .feed import VideoFeed
from .handoff import (
    CallableHandoff,
    DirectorySink,
    Handoff,
    NullHandoff,
    run,
)
from .segment import Segment
from .triggers import (
    BUILTIN_TRIGGERS,
    AudioDrop,
    AudioOnset,
    BrightnessShift,
    FunctionTrigger,
    MotionSpike,
    Probe,
    SceneCut,
    Trigger,
    build_triggers,
)

__all__ = [
    "VideoFeed",
    "Segment",
    "Probe",
    "Trigger",
    "SceneCut",
    "MotionSpike",
    "AudioOnset",
    "AudioDrop",
    "BrightnessShift",
    "FunctionTrigger",
    "build_triggers",
    "BUILTIN_TRIGGERS",
    "Handoff",
    "NullHandoff",
    "DirectorySink",
    "CallableHandoff",
    "run",
]
