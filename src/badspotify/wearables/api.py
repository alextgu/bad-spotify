"""Versioned LAN contract for the native Meta glasses companion.

Meta's Device Access Toolkit runs in a phone app. This router is the narrow
boundary between that app and the existing Python pipeline: JPEG in,
``Observation`` through ``graph.tick``, full decision out.
"""
import asyncio
import hmac
import os
from io import BytesIO
from dataclasses import dataclass, field


LOOPBACK_HOSTS = {"127.0.0.1", "localhost", "::1"}


@dataclass
class FrameSequences:
    """The newest completed sequence for each companion capture session."""

    last_by_session: dict[tuple[str, str], int] = field(default_factory=dict)

    def classify(self, client_id: str, session_id: str, sequence: int) -> str | None:
        previous = self.last_by_session.get((client_id, session_id))
        if previous is None or sequence > previous:
            return None
        return "duplicate" if sequence == previous else "out_of_order"

    def complete(self, client_id: str, session_id: str, sequence: int) -> None:
        self.last_by_session[(client_id, session_id)] = sequence


def live_payload(runtime, state: dict) -> dict:
    """Serialize the decision once for browser and native live inputs."""
    scene = state.get("scene")
    decision = state.get("decision")
    current = runtime.graph.dj.state.current
    verdict = state.get("verdict")
    chosen = None if verdict is None else {
        "title": verdict.track.title,
        "artist": verdict.track.artist,
        "strategy": verdict.strategy,
        "why": verdict.track.why or verdict.reasoning or verdict.quip,
    }
    return {
        "chosen": chosen,
        "error": state.get("play_error"),
        "scene": None if scene is None else {
            "setting": scene.setting,
            "activity": scene.activity,
            "mood": scene.mood_label,
            "confidence": scene.confidence,
            "colors": scene.dominant_colors,
            "references": scene.references,
            "setting_attributes": scene.setting_attributes,
            "opposite_attributes": scene.opposite_attributes,
            "opposite_genres": scene.opposite_genres,
            "latency_ms": scene.latency_ms,
            "source": scene.source,
        },
        "action": None if decision is None else decision.action.value,
        "reason": None if decision is None else decision.reason,
        "playing": None if current is None else {
            "title": current.track.title,
            "artist": current.track.artist,
            "strategy": current.strategy,
            "quip": current.quip,
        },
    }


def create_wearables_router(runtime, frame_lock):
    from fastapi import APIRouter, Header, HTTPException, Request
    from fastapi.responses import JSONResponse

    router = APIRouter(prefix="/api/wearables/v1", tags=["wearables"])
    sequences = FrameSequences()
    cfg = getattr(runtime, "cfg", None)

    def setting(key: str, default):
        return cfg.get_path(key, default) if cfg else default

    token_env = str(setting("wearables.token_env", "SLOPIFY_WEARABLE_TOKEN"))
    token = os.environ.get(token_env, "").strip()
    host = str(setting("hud.host", "127.0.0.1"))
    loopback = host in LOOPBACK_HOSTS
    max_frame_bytes = int(setting("wearables.max_frame_bytes", 5 * 1024 * 1024))
    max_frame_pixels = int(setting("wearables.max_frame_pixels", 12_000_000))
    min_interval_ms = int(setting("wearables.min_interval_ms", 2000))
    ready = hasattr(runtime, "graph") and (bool(token) or loopback)

    def authorize(authorization: str | None) -> None:
        if not ready:
            raise HTTPException(
                status_code=503,
                detail=f"set {token_env} before exposing the wearable API on the LAN",
            )
        if not token:
            return
        supplied = authorization.removeprefix("Bearer ") if authorization else ""
        if not hmac.compare_digest(supplied, token):
            raise HTTPException(status_code=401, detail="invalid wearable token")

    @router.get("/capabilities")
    async def capabilities():
        return JSONResponse(
            {
                "service": "slopify",
                "protocol_version": 1,
                "ready": ready,
                "frame_endpoint": "/api/wearables/v1/frames",
                "accepted_content_types": ["image/jpeg"],
                "max_frame_bytes": max_frame_bytes,
                "max_frame_pixels": max_frame_pixels,
                "min_interval_ms": min_interval_ms,
                "authentication": "bearer" if token else "none",
            },
            # This endpoint exposes no secret and is intentionally readable by
            # the statically hosted launch page. Frame POSTs keep the HUD's
            # narrow CORS policy and are sent only by the native companion.
            headers={"Access-Control-Allow-Origin": "*"},
        )

    @router.post("/frames")
    async def frames(
        request: Request,
        authorization: str | None = Header(default=None),
        client_id: str | None = Header(default=None, alias="X-Slopify-Client-Id"),
        session_id: str | None = Header(default=None, alias="X-Slopify-Session-Id"),
        sequence_text: str | None = Header(default=None, alias="X-Slopify-Sequence"),
        captured_text: str | None = Header(default=None, alias="X-Slopify-Captured-At-Ms"),
        dat_version: str | None = Header(default=None, alias="X-Meta-Dat-Version"),
    ):
        authorize(authorization)
        if (
            not client_id
            or not session_id
            or sequence_text is None
            or captured_text is None
            or not dat_version
        ):
            raise HTTPException(status_code=422, detail="missing wearable frame metadata")
        try:
            sequence = int(sequence_text)
            captured_at_ms = int(captured_text)
        except ValueError as error:
            raise HTTPException(status_code=422, detail="invalid wearable frame metadata") from error
        if sequence < 0 or captured_at_ms <= 0:
            raise HTTPException(status_code=422, detail="invalid wearable frame metadata")

        order = sequences.classify(client_id, session_id, sequence)
        if order:
            return {"accepted": False, "sequence": sequence, "reason": order}

        if frame_lock.locked():
            return JSONResponse(
                {
                    "accepted": False,
                    "sequence": sequence,
                    "reason": "busy",
                    "retry_after_ms": min_interval_ms,
                },
                status_code=429,
                headers={"Retry-After": str(max(1, min_interval_ms // 1000))},
            )

        # This endpoint deliberately takes a raw JPEG rather than multipart.
        # Authentication and the lock therefore happen before any body read,
        # and streaming enforces the byte cap without FastAPI spooling a large
        # unauthenticated upload first.
        await frame_lock.acquire()
        try:
            content_type = request.headers.get("content-type", "").split(";", 1)[0]
            if content_type != "image/jpeg":
                raise HTTPException(status_code=415, detail="wearable frames must be JPEG")
            data = bytearray()
            async for chunk in request.stream():
                if len(data) + len(chunk) > max_frame_bytes:
                    raise HTTPException(status_code=413, detail="frame is too large")
                data.extend(chunk)
            if not data:
                raise HTTPException(status_code=400, detail="empty frame")

            from PIL import Image

            try:
                with Image.open(BytesIO(data)) as probe:
                    width, height = probe.size
                    image_format = probe.format
            except Exception as error:
                raise HTTPException(status_code=400, detail="could not decode that frame") from error
            if image_format != "JPEG":
                raise HTTPException(status_code=415, detail="wearable frames must be JPEG")
            if width <= 0 or height <= 0 or width * height > max_frame_pixels:
                raise HTTPException(status_code=413, detail="frame dimensions are too large")

            import cv2
            import numpy as np

            image = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
            if image is None:
                raise HTTPException(status_code=400, detail="could not decode that frame")

            from ..capture.base import Observation

            observation = Observation(
                frame=image,
                ts=captured_at_ms / 1000,
                meta={
                    "source": "meta_glasses",
                    "client_id": client_id,
                    "session_id": session_id,
                    "sequence": sequence,
                    "captured_at_ms": captured_at_ms,
                    "meta_dat_version": dat_version,
                },
            )
            state = await asyncio.get_running_loop().run_in_executor(
                None, runtime.graph.tick, observation
            )
            sequences.complete(client_id, session_id, sequence)
        finally:
            frame_lock.release()

        return {"accepted": True, "sequence": sequence, **live_payload(runtime, state)}

    return router
