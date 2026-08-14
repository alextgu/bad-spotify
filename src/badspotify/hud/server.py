"""The HUD server.

This is not a debug view. It is the product surface: the glasses have no
display, so everything the agent perceives and decides has to be legible
somewhere, and that somewhere is a screen the audience can watch.

Also hosts the two endpoints that make a live demo survivable:
  POST /api/inject   -- type a scene, run the whole pipeline on it, no camera
"""
#
# NOTE: this module deliberately does NOT use `from __future__ import
# annotations`. FastAPI resolves handler annotations with get_type_hints(),
# which evaluates them against the MODULE globals -- and `WebSocket` is
# imported lazily inside create_app(), so under postponed annotations it
# isn't there. FastAPI then treats `sock: "WebSocket"` as an unknown query
# parameter, refuses the handshake, and the browser sees a bare HTTP 403
# with nothing in the server log. Keep annotations eager here.
#
import asyncio
import json
from pathlib import Path

from ..bus import BUS

STATIC = Path(__file__).parent / "static"


def create_app(runtime=None):
    from fastapi import FastAPI, WebSocket, WebSocketDisconnect
    from fastapi.responses import FileResponse, JSONResponse
    from fastapi.staticfiles import StaticFiles

    app = FastAPI(title="bad-spotify HUD")

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

    @app.websocket("/ws")
    async def ws(sock: WebSocket):
        try:
            await sock.accept()
        except Exception as e:
            # Do not swallow this silently: a failed accept shows up on the
            # client as a bare HTTP 403 with nothing in the server log, which
            # is a genuinely horrible thing to debug at 3am.
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
    # Pin the websocket implementation. With uvicorn's default "auto" and no
    # ws library resolved, upgrade requests get a bare HTTP 403 and the HUD
    # sits on "reconnecting" forever with nothing useful in the logs.
    ws_impl = "auto"
    try:
        import websockets  # noqa: F401
        ws_impl = "websockets"
    except ImportError:
        try:
            import wsproto  # noqa: F401
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
