"""The HUD server.

This is not a debug view. It is the product surface: the glasses have no
display, so everything the agent perceives and decides has to be legible
somewhere, and that somewhere is a screen the audience can watch.

Also hosts the endpoint that makes a live demo survivable:
  POST /api/inject   -- type a scene, run the whole pipeline on it, no camera

There is deliberately no "how wrong should it be" control. The agent always
fully inverts; how wrong the result turned out is measured and reported, not
requested.
"""
#This module uses eager annotations because WebSocket is imported inside create_app
#This keeps FastAPI WebSocket connections working
import asyncio
import json
import tempfile
import uuid
from pathlib import Path

from ..bus import BUS
from ..log import notice as print  # stdout is reserved for data

STATIC = Path(__file__).parent / "static"


def create_app(runtime=None):
    from fastapi import FastAPI, File, HTTPException, UploadFile, WebSocket, WebSocketDisconnect
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import FileResponse, JSONResponse
    from fastapi.staticfiles import StaticFiles

    app = FastAPI(title="bad-spotify HUD")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
    )
    analysis_lock = asyncio.Lock()

    @app.get("/")
    async def index():
        return FileResponse(STATIC / "index.html")

    @app.get("/dj")
    async def dj():
        """The presentation face. The engineering HUD stays at / -- we want
        both: judges see the character, we see the wiring."""
        return FileResponse(STATIC / "dj.html")

    @app.get("/api/session")
    async def session():
        """The last recorded run, for the demo site to replay."""
        from ..session import SESSIONS
        files = sorted(SESSIONS.glob("*.json")) if SESSIONS.exists() else []
        if not files:
            return JSONResponse({"error": "no sessions recorded yet -- run: "
                                          "python run.py --video clip.mp4 --record name"},
                                status_code=404)
        return JSONResponse(json.loads(files[-1].read_text()))

    @app.get("/api/state")
    async def state():
        dj = runtime.graph.dj if runtime else None
        return JSONResponse({
            "strategies": runtime.graph.strategy_names if runtime else [],
            "corpus_size": len(runtime.graph.corpus) if runtime else 0,
            "playing": (
                {
                    "title": dj.state.current.track.title,
                    "artist": dj.state.current.track.artist,
                    "quip": dj.state.current.quip,
                    "mismatch": dj.state.current.mismatch,
                }
                if dj and dj.state.current else None
            ),
            "backends": runtime.backends() if runtime else {},
            "history": [e.model_dump() for e in list(BUS.history)[-60:]],
        })

    @app.post("/api/inject")
    async def inject(payload: dict):
        """Deterministic demo mode: describe a scene, run the real pipeline."""
        if not runtime:
            return JSONResponse({"ok": False, "error": "no runtime"}, status_code=400)
        text = payload.get("scene", "").strip()
        if not text:
            return JSONResponse({"ok": False, "error": "empty scene"}, status_code=400)
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, runtime.inject_scene, text)
        return {"ok": True}

    @app.post("/api/analyze-video")
    async def analyze_video(file: UploadFile = File(...)):
        """Sample an uploaded video and return a replay session."""
        if not runtime:
            raise HTTPException(status_code=503, detail="the analysis runtime is not ready")

        allowed = {".mp4", ".mov", ".webm", ".avi", ".mkv", ".m4v"}
        original_name = Path(file.filename or "video.mp4").name
        suffix = Path(original_name).suffix.lower()
        if suffix not in allowed:
            raise HTTPException(status_code=415, detail="choose a common video file")

        max_mb = float(runtime.cfg.get_path("hud.max_upload_mb", 200))
        max_bytes = int(max_mb * 1024 * 1024)

        async with analysis_lock:
            try:
                with tempfile.TemporaryDirectory(prefix="badspotify_upload_") as folder:
                    target = Path(folder) / f"{uuid.uuid4().hex}{suffix}"
                    total = 0
                    with target.open("wb") as output:
                        while chunk := await file.read(1024 * 1024):
                            total += len(chunk)
                            if total > max_bytes:
                                raise HTTPException(
                                    status_code=413,
                                    detail=f"video must be smaller than {max_mb:g} MB",
                                )
                            output.write(chunk)

                    from ..analysis import VideoAnalyzer

                    analyzer = VideoAnalyzer(
                        runtime.cfg,
                        perceiver=runtime.perceiver,
                        judge=runtime.graph.judge,
                        corpus=runtime.graph.corpus,
                    )
                    loop = asyncio.get_running_loop()
                    result = await loop.run_in_executor(
                        None,
                        analyzer.analyze,
                        target,
                        original_name,
                    )
                    return JSONResponse(result)
            except HTTPException:
                raise
            except Exception as error:
                raise HTTPException(
                    status_code=400,
                    detail=f"video analysis failed: {error}",
                ) from error
            finally:
                await file.close()

    @app.websocket("/ws")
    async def ws(sock: WebSocket):
        try:
            await sock.accept()
        except Exception as e:
            #Logs failed WebSocket connections so the error is visible
            print(f"[hud] websocket accept failed: {type(e).__name__}: {e}")
            raise

        q = BUS.queue()
        try:
            for ev in list(BUS.history)[-40:]:
                await sock.send_text(ev.model_dump_json())
            while True:
                ev = await q.get()
                await sock.send_text(ev.model_dump_json())
        except WebSocketDisconnect:
            pass
        except Exception as e:
            print(f"[hud] websocket stream ended: {type(e).__name__}: {e}")
        finally:
            BUS.drop_queue(q)

    if STATIC.exists():
        app.mount("/static", StaticFiles(directory=STATIC), name="static")
    return app


def serve_in_thread(runtime, host: str = "127.0.0.1", port: int = 8420):
    import threading

    import uvicorn

    app = create_app(runtime)
    #Chooses an installed WebSocket backend for reliable connections
    ws_impl = "auto"
    try:
        import websockets  #noqa: F401
        ws_impl = "websockets"
    except ImportError:
        try:
            import wsproto  #noqa: F401
            ws_impl = "wsproto"
        except ImportError:
            print("[hud] no websocket library -- pip install 'uvicorn[standard]'; "
                  "the HUD will not update live")

    config = uvicorn.Config(app, host=host, port=port,
                            log_level="warning", ws=ws_impl)
    server = uvicorn.Server(config)
    t = threading.Thread(target=server.run, daemon=True)
    t.start()
    print(f"[hud] http://{host}:{port}")
    return server
