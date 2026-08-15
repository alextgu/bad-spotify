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

from badspotify.agents.graph import BadSpotifyGraph          #noqa: E402
from badspotify.bus import BUS                                #noqa: E402
from badspotify.capture.base import build_capture             #noqa: E402
from badspotify.console import attach as attach_console        #noqa: E402
from badspotify.config import load_config                     #noqa: E402
from badspotify.perceive.scene import build_perceiver, read_description  #noqa: E402
from badspotify.players.base import build_player              #noqa: E402
from badspotify.schemas import DJAction                       #noqa: E402
from badspotify.voice.lines import DEFAULT_GREETING, greeting  #noqa: E402
from badspotify.voice.narrator import build_narrator          #noqa: E402


def _lan_address() -> str:
    """This machine's address on the wifi, for a phone to aim at.

    Asks the routing table by opening a UDP socket to a public address --
    nothing is sent, but the OS picks the interface it would use, which is the
    one the phone can see. `gethostname()` lookups return 127.0.0.1 on plenty
    of machines and would send someone chasing a URL that cannot work.
    """
    import socket

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"
    finally:
        s.close()


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

    #Runs a scene entered from the engineering screen

    def inject_scene(self, text: str) -> None:
        """Stage button: run the real graph on a typed scene, bypassing bounds.

        Bounds exist to stop thrashing during continuous perception. A human
        deliberately pressing a button is not thrashing, so we force it --
        otherwise the demo looks broken while the cooldown ticks down.
        """
        scene = read_description(self.perceiver, text)
        BUS.emit("scene", scene.mood_label, setting=scene.setting,
                 activity=scene.activity, vibe=scene.vibe.model_dump(),
                 colors=scene.dominant_colors, confidence=scene.confidence,
                 tempo=scene.tempo_feel.value, meter=scene.meter.value,
                 audio=scene.audio_summary, source="injected", latency_ms=0)

        #`force` must be set here, not just faked by poking the counters: the
        #deadband in n_antagonize reads it, and without it pressing the button
        #twice on one scene holds instead of playing -- the "demo looks broken"
        #failure this method exists to avoid.
        state = self.graph.n_antagonize({"scene": scene, "force": True})
        state = self.graph.n_judge(state)

        self.graph.dj.state.pending_signature = scene.signature()
        self.graph.dj.state.pending_count = self.graph.dj.agreement
        self.graph.dj.state.started_at = 0.0
        self.graph.dj.state.last_switch = 0.0

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
    ap.add_argument("--source",
                    choices=["replay", "video", "webcam", "screen", "glasses"])
    ap.add_argument("--video", default=None,
                    help="run against a video file as if it were live")
    ap.add_argument("--realtime", action="store_true",
                    help="pace the video at its true speed instead of as fast as possible")
    ap.add_argument("--loop", action="store_true",
                    help="restart the video when it ends -- for leaving a demo running")
    ap.add_argument("--record", default=None, metavar="NAME",
                    help="write the run to data/sessions/NAME.json for the demo site")
    ap.add_argument("--ticks", type=int, default=None, help="stop after N observations")
    ap.add_argument("--no-hud", action="store_true")
    ap.add_argument("--serve", action="store_true",
                    help="serve the upload app without starting a capture source")
    ap.add_argument("--lan", action="store_true",
                    help="bind every interface so a phone on the same wifi can "
                         "reach /phone -- the companion app for the glasses")
    ap.add_argument("--calm", action="store_true",
                    help="film mode: make the DJ much harder to move. A "
                         "handheld camera wobbles constantly and the normal "
                         "bounds are tuned to feel responsive, which on camera "
                         "reads as a shuffle button")
    ap.add_argument("--https", action="store_true",
                    help="serve TLS with a self-signed certificate. Phones only "
                         "allow the camera in a secure context, so /phone needs "
                         "this over the network")
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
    if args.loop:
        cfg.setdefault("capture", {})["loop"] = True
    if args.no_hud:
        cfg.setdefault("hud", {})["enabled"] = False
    if args.lan:
        cfg.setdefault("hud", {})["host"] = "0.0.0.0"
    if args.calm:
        # Filming is a different problem from demoing live. A phone in someone's
        # hand re-frames, re-exposes and re-focuses constantly, so the scene
        # read genuinely does move -- and the honest response to "something
        # changed" is still usually to leave the music alone. A track that
        # changes every twenty seconds on camera reads as random no matter how
        # good the reasoning behind each pick was.
        #
        # So: the deadband roughly doubles, acting on a single read needs a
        # near-total change of scene, three agreeing reads are required instead
        # of two, and a track gets a minute to itself before anything may
        # replace it.
        # The stickiness comes from the dwell floor and the agreement count,
        # NOT from a huge deadband. The first attempt used 0.55, which sits
        # right on the smallest real scene change we ever measured (0.563), so
        # it held through walking outside -- five minutes of filming produced
        # one track and then ignored a genuine change of place. 0.45 clears
        # camera wobble by a wide margin and still lets a new room through.
        cfg.setdefault("dj", {}).update(
            hold_threshold=0.45,        # was 0.30; noise tops out at 0.173
            jump_threshold=1.00,        # was 0.55; acting on one read is rare
            min_change_seconds=60,      # was 20
            agreement_reads=3,          # was 2
            cooldown_seconds=25,        # was 8
            min_track_seconds=60,       # was 25
            min_interrupt_seconds=45,   # was 15
        )
        print("[dj] calm mode: holding hard. One track per minute at most, "
              "and only a real change of place will move it.")
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

    server = None
    if cfg.get_path("hud.enabled", True):
        try:
            from badspotify.hud.server import serve_in_thread
            host = cfg.get_path("hud.host", "127.0.0.1")
            port = int(cfg.get_path("hud.port", 8420))
            lan = _lan_address()
            tls = None
            if args.https:
                from badspotify.hud.tls import ensure_cert
                tls = ensure_cert(lan)

            server = serve_in_thread(rt, host, port, tls=tls)
            scheme = "https" if tls else "http"
            local = "127.0.0.1" if host in ("0.0.0.0", "::") else host
            print(f"[hud] DJ face:          {scheme}://{local}:{port}/dj")
            print(f"[hud] engineering view: {scheme}://{local}:{port}/")
            print(f"[hud] live:             {scheme}://{local}:{port}/live")
            if host in ("0.0.0.0", "::"):
                print(f"[hud] companion app:    {scheme}://{lan}:{port}/phone")
                if tls:
                    print("[hud] The phone warns that the certificate is not "
                          "trusted -- it is signed by this\n"
                          "      machine, which is the point. Tap advanced, "
                          "then proceed; the camera\n"
                          "      works after that.")
                else:
                    print("[hud] NOTE: phones only allow the camera on HTTPS "
                          "or localhost, so it will be\n"
                          "      blocked at that address. Add --https.")
        except Exception as e:
            print(f"[hud] disabled ({e})")

    if args.serve:
        if server is None:
            raise SystemExit("the upload app needs the HUD server")
        print("[hud] upload API:       POST /api/analyze-video")
        try:
            while not server.should_exit:
                time.sleep(.25)
        except KeyboardInterrupt:
            server.should_exit = True
        return

    # One line, at startup, and then it gets on with it. The running product
    # does not narrate every track -- see voice.say in config.yaml.
    if cfg.get_path("voice.say", "greeting") != "off":
        vcfg = cfg.section("voice")
        rt.narrator.say(greeting(vcfg.get("agent_name", ""),
                                 vcfg.get("greeting", DEFAULT_GREETING)))

    rt.run(ticks=args.ticks)

    if recorder is not None:
        path = recorder.save()
        print("\n" + recorder.summary())
        print(f"\nsession written to {path}")


if __name__ == "__main__":
    main()
