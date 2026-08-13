"""Placeholder for Meta Ray-Ban capture.

Status as of the build: the Meta Wearables Device Access Toolkit is in
Developer Preview. It exposes video streaming, photo capture, microphone
and audio out for Ray-Ban Meta Gen 1/2, Ray-Ban Display, Oakley Meta HSTN
and Vanguard -- but it is a native iOS/Android SDK, publishing is disabled
during preview, and access is gated to AI-glasses-supported countries.

So the port is NOT a Python import. It is: a thin native app that owns the
SDK session and POSTs frames + audio chunks to this process over localhost.
This class is the receiving end. Everything above it is already agnostic.
"""
from __future__ import annotations

import time
from typing import Iterator

from .base import Observation


class GlassesSource:
    name = "glasses"

    def __init__(self, cfg: dict):
        self.cfg = cfg
        self.endpoint = cfg.get("glasses_endpoint", "http://127.0.0.1:8899/frames")

    def open(self) -> None:
        raise NotImplementedError(
            "GlassesSource is a stub.\n"
            "To implement: build a native companion app against the Meta Wearables\n"
            "Device Access Toolkit, stream frames + mic to a local HTTP/WS endpoint,\n"
            "then read them here. Audio OUT can already reach the glasses today via\n"
            "standard Bluetooth from the phone -- no SDK required for playback."
        )

    def close(self) -> None:
        pass

    def stream(self) -> Iterator[Observation]:
        while True:
            yield Observation(ts=time.time())
