"""Tiny in-process pub/sub so the HUD can watch the pipeline think."""
from __future__ import annotations

import asyncio
import time
from collections import deque
from typing import Callable

from .schemas import PipelineEvent


class EventBus:
    def __init__(self, history: int = 200):
        self._subs: list[Callable[[PipelineEvent], None]] = []
        self._queues: list[asyncio.Queue] = []
        self.history: deque[PipelineEvent] = deque(maxlen=history)

    def subscribe(self, fn: Callable[[PipelineEvent], None]) -> None:
        self._subs.append(fn)

    def unsubscribe(self, fn: Callable[[PipelineEvent], None]) -> None:
        """Same reason as drop_queue: anything that subscribes per request --
        a session recorder in a web handler, say -- has to be able to let go,
        or every request leaves a listener behind that emit() keeps calling."""
        if fn in self._subs:
            self._subs.remove(fn)

    def drop_queue(self, q: asyncio.Queue) -> None:
        """Unregister a disconnected subscriber. Without this, every HUD
        refresh leaks a queue that emit() keeps filling forever."""
        if q in self._queues:
            self._queues.remove(q)

    def queue(self) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue(maxsize=100)
        self._queues.append(q)
        return q

    def emit(self, kind: str, label: str, **detail) -> PipelineEvent:
        ev = PipelineEvent(kind=kind, label=label, detail=detail, ts=time.time())
        self.history.append(ev)
        for fn in self._subs:
            try:
                fn(ev)
            except Exception:
                pass
        for q in list(self._queues):
            try:
                q.put_nowait(ev)
            except asyncio.QueueFull:
                pass
        return ev


BUS = EventBus()
