"""Frames from Ray-Ban Meta, by way of a companion app.

**Apps do not run on the glasses.** The Meta Wearables Device Access Toolkit
gives an iOS/Android app access to the 12MP camera, the 5-mic array and the
open-ear speakers; the app runs on the phone and the glasses are its sensors.
Only Ray-Ban Display can put anything in the lens, and publishing is disabled
while the toolkit is in preview. So there is no Python import that reaches a
pair of glasses, and there never will be.

What there is, is a seam. A companion app owns the SDK session and POSTs
frames here; this class is the receiving end, and everything above it already
works in terms of `Observation`. That was true when this file was a stub and
it is still true now that it isn't.

**Half of the product needs none of this.** The glasses are a standard
Bluetooth audio device: pair them, make them the output, and Spotify plays the
wrong song out of them today, with no toolkit and no preview access. Only the
camera half needs the SDK.

This class remains the headless `--source glasses` receiver on port 8899. The
preferred native integration when the HUD is running is Wearables API v1 at
`/api/wearables/v1/frames`: it adds bearer auth, capture metadata, ordering,
backpressure and the decision response. `/phone` and `/api/frame` remain the
browser stand-ins and keep their existing protocol.
"""
from __future__ import annotations

import queue
import threading
import time
from typing import Iterator

import numpy as np

from .base import Observation
from ..log import notice as print  # stdout is reserved for data


class GlassesSource:
    name = "glasses"

    def __init__(self, cfg: dict):
        self.cfg = cfg
        self.host = cfg.get("glasses_host", "0.0.0.0")
        self.port = int(cfg.get("glasses_port", 8899))
        #A phone on the same wifi has to reach this, so it binds every
        #interface by default. 127.0.0.1 would be reachable only by the
        #machine itself, which is the one device that isn't wearing anything.
        self._frames: queue.Queue = queue.Queue(maxsize=2)
        self._server = None
        self._thread: threading.Thread | None = None
        self._dropped = 0

    #-- receiving ------------------------------------------------------------

    def submit(self, frame: np.ndarray, meta: dict | None = None) -> bool:
        """Hand a frame to the loop. Returns False if it was dropped.

        Dropping is correct. Perception takes ~1.2s and a companion app posts
        on a timer, so a backlog would mean answering a moment that has
        already passed. A shallow queue keeps the agent in the present.
        """
        try:
            self._frames.put_nowait(Observation(
                frame=frame, ts=time.time(),
                meta={"source": "glasses", **(meta or {})}))
            return True
        except queue.Full:
            self._dropped += 1
            return False

    #-- capture source contract ---------------------------------------------

    def open(self) -> None:
        import cv2
        from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

        source = self

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):                       #noqa: N802 - stdlib name
                length = int(self.headers.get("Content-Length") or 0)
                body = self.rfile.read(length) if length else b""
                if not body:
                    return self._reply(400, {"error": "empty frame"})
                img = cv2.imdecode(np.frombuffer(body, np.uint8),
                                   cv2.IMREAD_COLOR)
                if img is None:
                    return self._reply(400, {"error": "not a decodable image"})
                took = source.submit(img)
                return self._reply(200, {"ok": True, "queued": took})

            def do_GET(self):                        #noqa: N802 - stdlib name
                #So a companion app can check it is talking to the right thing.
                return self._reply(200, {"ok": True, "service": "glasses",
                                         "dropped": source._dropped})

            def _reply(self, code: int, payload: dict):
                import json

                data = json.dumps(payload).encode()
                self.send_response(code)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(data)))
                #The companion app is a different origin by definition.
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(data)

            def log_message(self, *a):               #noqa: A003 - stdlib name
                pass                                 #stdout is for data

        self._server = ThreadingHTTPServer((self.host, self.port), Handler)
        self._thread = threading.Thread(target=self._server.serve_forever,
                                        daemon=True)
        self._thread.start()
        print(f"[glasses] waiting for frames on http://{self.host}:{self.port}/ "
              f"-- point the companion app (or /phone) at this")

    def close(self) -> None:
        if self._server is not None:
            self._server.shutdown()
            self._server.server_close()
            self._server = None

    def stream(self) -> Iterator[Observation]:
        while True:
            try:
                yield self._frames.get(timeout=1.0)
            except queue.Empty:
                #Nothing posted. Yield an empty observation rather than block
                #forever: the loop above counts ticks, and a source that never
                #returns looks identical to a hung process.
                yield Observation(ts=time.time(),
                                  meta={"source": "glasses", "idle": True})
