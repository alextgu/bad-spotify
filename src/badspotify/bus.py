"""Tiny in-process pub/sub so the HUD can watch the pipeline think."""
from __future__ import annotations

import asyncio
import time

from .log import notice
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
        """Detach a listener. Anything that subscribes for the duration of one
        run -- a session recorder, say -- must call this in a finally block, or
        every run leaves another listener attached to a module-level bus and
        old runs keep recording into dead objects."""
        try:
            self._subs.remove(fn)
        except ValueError:
            pass

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
            except Exception as e:
                # A broken subscriber must not take the pipeline down — but a
                # silent one nearly cost us the session recorder: any bug in a
                # subscriber vanished without a line anywhere. Say what died.
                notice(f"[bus] subscriber {getattr(fn, '__qualname__', fn)!r} "
                       f"failed on {ev.kind}/{ev.label}: {type(e).__name__}: {e}")
        for q in list(self._queues):
            try:
                q.put_nowait(ev)
            except asyncio.QueueFull:
                pass
        return ev


BUS = EventBus()
