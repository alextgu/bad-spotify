#!/usr/bin/env python3
"""bad-spotify entrypoint.

    python run.py                      # replay source, all mock, HUD on
    python run.py --source webcam      # real camera + mic
    python run.py --ticks 8            # bounded run, useful for tests
    python run.py --no-hud             # headless

Every backend degrades to a mock rather than crashing. A fresh clone with no
API keys, no Spotify account and no camera still runs the entire graph.
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from badspotify.agents.graph import BadSpotifyGraph          # noqa: E402
from badspotify.bus import BUS                                # noqa: E402
from badspotify.capture.base import build_capture             # noqa: E402
from badspotify.console import attach as attach_console        # noqa: E402
from badspotify.config import load_config                     # noqa: E402
from badspotify.perceive.scene import build_perceiver, scene_from_text  # noqa: E402
from badspotify.players.base import build_player              # noqa: E402
from badspotify.schemas import DJAction                       # noqa: E402
from badspotify.voice.narrator import build_narrator          # noqa: E402


class Runtime:
    def __init__(self, cfg):
        self.cfg = cfg
        self.capture = build_capture(cfg.section("capture"))
        self.perceiver = build_perceiver(cfg.section("perceive"))
        self.player = build_player(cfg.section("player"))
        self.narrator = build_narrator(cfg.section("voice"))
        self.graph = BadSpotifyGraph(cfg, self.perceiver, self.player, self.narrator)

    def backends(self) -> dict:
        return {
            "capture": self.capture.name,
            "perceive": getattr(self.perceiver, "backend", "?"),
            "judge": getattr(self.graph.judge, "backend", "?"),
            "player": self.player.name,
            "voice": getattr(self.narrator, "backend", "?"),
            "graph": "langgraph" if self.graph._compiled is not None else "sequential",
        }

    # ---------------------------------------------------------------------

    def inject_scene(self, text: str) -> None:
        """Stage button: run the real graph on a typed scene, bypassing bounds.

        Bounds exist to stop thrashing during continuous perception. A human
        deliberately pressing a button is not thrashing, so we force it --
        otherwise the demo looks broken while the cooldown ticks down.
        """
        scene = scene_from_text(text)
        BUS.emit("scene", scene.mood_label, setting=scene.setting,
                 activity=scene.activity, vibe=scene.vibe.model_dump(),
                 colors=scene.dominant_colors, confidence=scene.confidence,
                 tempo=scene.tempo_feel.value, meter=scene.meter.value,
                 audio=scene.audio_summary, source="injected", latency_ms=0)

        state = self.graph.n_antagonize({"scene": scene, "force": True})
        state = self.graph.n_judge(state)
        state = self.graph.n_dj(state)
        if state["decision"].action in (DJAction.PLAY, DJAction.FALLBACK):
            self.graph.n_play(state)

    def run(self, ticks: int | None = None, interval: float | None = None) -> None:
        self.capture.open()
        interval = interval if interval is not None else float(
            self.cfg.get_path("capture.frame_interval_s", 5.0))
        n = 0
        try:
            for obs in self.capture.stream():
                n += 1
                print(f"\n--- tick {n} " + "-" * 46)
                try:
                    self.graph.tick(obs)
                except Exception as e:
                    BUS.emit("error", "tick failed", error=str(e))
                    print(f"[runtime] tick failed: {e}")
                if ticks and n >= ticks:
                    break
                if self.capture.name != "replay" or interval > 0:
                    time.sleep(min(interval, 5.0) if ticks is None else 0.05)
        except KeyboardInterrupt:
            print("\n[runtime] stopping")
        finally:
            self.capture.close()
            self.player.stop()


def main() -> None:
    ap = argparse.ArgumentParser(description="the agent that gets it wrong on purpose")
    ap.add_argument("--config", default=None)
    ap.add_argument("--source", choices=["replay", "video", "webcam", "glasses"])
    ap.add_argument("--video", default=None,
                    help="run against a video file as if it were live")
    ap.add_argument("--realtime", action="store_true",
                    help="pace the video at its true speed instead of as fast as possible")
    ap.add_argument("--record", default=None, metavar="NAME",
                    help="write the run to data/sessions/NAME.json for the demo site")
    ap.add_argument("--ticks", type=int, default=None, help="stop after N observations")
    ap.add_argument("--no-hud", action="store_true")
    ap.add_argument("--quiet", action="store_true", help="only verdicts and errors")
    ap.add_argument("--turbo", action="store_true",
                    help="collapse DJ time bounds (verification runs only -- "
                         "never for a live demo, it is what makes it thrash)")
    args = ap.parse_args()

    cfg = load_config(args.config)
    attach_console(verbose=not args.quiet)
    if args.video:
        cfg.setdefault("capture", {}).update(source="video", video_path=args.video)
    if args.source:
        cfg.setdefault("capture", {})["source"] = args.source
    if args.realtime:
        cfg.setdefault("capture", {})["realtime"] = True
    if args.no_hud:
        cfg.setdefault("hud", {})["enabled"] = False
    if args.turbo:
        cfg.setdefault("dj", {}).update(min_track_seconds=0, cooldown_seconds=0)

    recorder = None
    if args.record:
        from badspotify.session import SessionRecorder
        recorder = SessionRecorder(
            name=args.record,
            source=args.video or cfg.get_path("capture.source", "")).attach()

    rt = Runtime(cfg)
    print("\nbackends: " + "  ".join(f"{k}={v}" for k, v in rt.backends().items()))

    if cfg.get_path("hud.enabled", True):
        try:
            from badspotify.hud.server import serve_in_thread
            host = cfg.get_path("hud.host", "127.0.0.1")
            port = int(cfg.get_path("hud.port", 8420))
            serve_in_thread(rt, host, port)
            print(f"[hud] DJ face:          http://{host}:{port}/dj")
            print(f"[hud] engineering view: http://{host}:{port}/")
        except Exception as e:
            print(f"[hud] disabled ({e})")

    rt.run(ticks=args.ticks)

    if recorder is not None:
        path = recorder.save()
        print("\n" + recorder.summary())
        print(f"\nsession written to {path}")


if __name__ == "__main__":
    main()
