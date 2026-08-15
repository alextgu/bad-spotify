"""One object that runs the agent, for anything that isn't the CLI.

`run.py` owns the live loop: capture, timing bounds, HUD, speakers. That's the
right shape for a wearable and the wrong shape for everything else. A web app, a
notebook, or the future glasses companion all want the same thing instead:

    engine = Engine()
    engine.describe("a hospital waiting room at 3am")   # -> one decision
    engine.look(frame, audio)                           # -> one decision
    engine.watch("clip.mp4")                            # -> a whole session

Three entry points, no loop, no globals, nothing that plays audio out of the
host machine by default. `app.py` (Gradio) and any Ray-Ban companion app should
both sit on this, so there is one place where "what does the agent do with a
frame" is answered.

Notes worth knowing:

  **Bounds are off by default here.** The DJ's cooldown and hysteresis exist to
  stop a *continuous* loop thrashing. A person pressing a button, or a sampler
  handing over one deliberately-chosen frame, is not thrashing -- so every call
  here forces the decision through. Pass `respect_bounds=True` if you want the
  live behaviour.

  **Nothing plays by default.** `player="mock"` means the decision is reported,
  not blasted out of whatever machine is hosting this. Hosting a page that
  hijacks a laptop's speakers is a bad surprise; the site's own decision was to
  name songs rather than play them.

  **Sampling comes from `videofeed`**, not the agent's change gate. The gate can
  only react as fast as its caller samples; videofeed samples on a cadence *and*
  on cuts, onsets and motion. `watch()` uses it, so a decision can land on the
  moment something happened rather than on the next five-second tick.
"""
from __future__ import annotations

import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Iterator, Optional

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "src") not in sys.path:            # so `videofeed` imports cleanly
    sys.path.insert(0, str(ROOT / "src"))

from .agents.graph import BadSpotifyGraph          # noqa: E402
from .bus import BUS                               # noqa: E402
from .capture.base import Observation              # noqa: E402
from .config import load_config                    # noqa: E402
from .perceive.scene import build_perceiver, scene_from_text  # noqa: E402
from .players.base import build_player             # noqa: E402
from .schemas import DJAction, SceneRead           # noqa: E402

#: Pass as `player=` to mean "whatever config.yaml says", including a real one.
#: Deliberately not the default: an unqualified Engine() must stay silent, so
#: opting in to the host's speakers has to be written down at the call site.
FROM_CONFIG = "from_config"
from .session import SessionRecorder               # noqa: E402
from .voice.narrator import build_narrator         # noqa: E402


# ---------------------------------------------------------------- results --


@dataclass
class Decision:
    """What the agent did about one moment. JSON-safe via `to_dict()`."""

    scene: dict
    opposite: dict = field(default_factory=dict)
    considered: dict = field(default_factory=dict)
    chosen: dict = field(default_factory=dict)
    action: str = "hold"
    mode: str = ""
    reason: str = ""
    video_time: Optional[float] = None
    reasons: list[str] = field(default_factory=list)
    """Why this moment was sampled at all -- videofeed's trigger names."""
    latency_ms: int = 0

    @property
    def played(self) -> bool:
        return self.action in ("play", "fallback")

    @property
    def headline(self) -> str:
        if not self.chosen:
            return f"(no song — {self.reason})"
        return f"{self.chosen.get('title')} — {self.chosen.get('artist')}"

    def to_dict(self) -> dict:
        return {
            "scene": self.scene,
            "opposite": self.opposite,
            "considered": self.considered,
            "chosen": self.chosen,
            "action": self.action,
            "mode": self.mode,
            "reason": self.reason,
            "video_time": self.video_time,
            "reasons": self.reasons,
            "latency_ms": self.latency_ms,
        }


# ----------------------------------------------------------------- engine --


class Engine:
    """The agent, minus the loop. Build one and keep it: setup is not free."""

    def __init__(
        self,
        config_path: str | Path | None = None,
        *,
        player: Optional[str] = None,
        voice: Optional[str] = None,
        respect_bounds: bool = False,
    ):
        self.cfg = load_config(config_path)

        # Never take over the host's speakers unless asked in so many words.
        #
        # This used to `setdefault`, which only fires when the key is MISSING
        # -- and it never is, because config.yaml always names a backend. So
        # the promise above held only while that file happened to say "mock",
        # and flipping the live loop to Spotify silently armed every surface
        # built on Engine. Default now means default: mock unless a caller
        # names something else, or asks for the configured one on purpose.
        wanted = "mock" if player is None else player
        if wanted == FROM_CONFIG:
            self.cfg.setdefault("player", {}).setdefault("backend", "mock")
        else:
            self.cfg.setdefault("player", {})["backend"] = wanted
        if voice is not None:
            self.cfg.setdefault("voice", {})["backend"] = voice

        self.respect_bounds = bool(respect_bounds)

        self.perceiver = build_perceiver(self.cfg.section("perceive"))
        self.player = build_player(self.cfg.section("player"))
        self.narrator = build_narrator(self.cfg.section("voice"))
        self.graph = BadSpotifyGraph(self.cfg, self.perceiver, self.player,
                                     self.narrator)

    # ------------------------------------------------------------ settings --

    def backends(self) -> dict:
        """What is actually wired up right now, after any downgrade to mock."""
        return {
            "perceive": getattr(self.perceiver, "backend", "?"),
            "judge": getattr(self.graph.judge, "backend", "?"),
            "player": self.player.name,
            "voice": getattr(self.narrator, "backend", "?"),
            "graph": "langgraph" if self.graph._compiled is not None else "sequential",
            "corpus": len(self.graph.corpus.tracks),
        }

    def reset(self) -> None:
        """Forget what has been played. Between demo runs, not during one."""
        self.graph.dj.state.played_ids.clear()
        self.graph.dj.state.history.clear()
        self.graph.dj.state.current = None
        self.graph._last_scene = None
        self.graph._last_verdict = None

    # ------------------------------------------------------- one decision --

    def describe(self, text: str) -> Decision:
        """A typed scene. No camera, no keys, fully deterministic.

        The reliable demo: it exercises the exact same downstream graph as a
        real frame, and it cannot fail because of a webcam or a network.
        """
        text = (text or "").strip()
        if not text:
            raise ValueError("describe() needs a scene to describe")
        return self._decide(scene_from_text(text))

    def look(self, frame, audio=None, *, sample_rate: int = 16000,
             meta: Optional[dict] = None) -> Decision:
        """One frame (HxWx3 BGR) and optionally the audio around it.

        This is the call a glasses companion app makes, once per frame it
        decides to send. Everything above it is identical to the video path.
        """
        obs = Observation(frame=frame, audio=audio, sample_rate=sample_rate,
                          meta=meta or {})
        state = self.graph.n_perceive({"obs": obs})
        return self._decide(state["scene"], obs=obs,
                            reasons=list((meta or {}).get("reasons", [])))

    # ---------------------------------------------------------- a session --

    def watch(
        self,
        video_path: str | Path,
        *,
        interval_s: float = 5.0,
        triggers: Any = ("scene-cut", "audio-onset"),
        max_segments: Optional[int] = None,
        audio_window_s: float = 3.0,
        on_decision: Optional[Callable[[Decision], None]] = None,
        name: str = "session",
    ) -> dict:
        """Walk a video and decide about each sampled moment.

        Returns the same JSON the site replays -- exactly what
        `run.py --record NAME` writes -- so anything produced here can be
        dropped into `frontend/public/sessions/` unchanged.
        """
        decisions = list(self.watch_iter(
            video_path, interval_s=interval_s, triggers=triggers,
            max_segments=max_segments, audio_window_s=audio_window_s,
            on_decision=on_decision, name=name))
        return self._last_session or {
            "session": name, "source": str(video_path),
            "moment_count": 0, "README": "", "moments": [],
            "decisions": [d.to_dict() for d in decisions],
        }

    def watch_iter(
        self,
        video_path: str | Path,
        *,
        interval_s: float = 5.0,
        triggers: Any = ("scene-cut", "audio-onset"),
        max_segments: Optional[int] = None,
        audio_window_s: float = 3.0,
        on_decision: Optional[Callable[[Decision], None]] = None,
        name: str = "session",
    ) -> Iterator[Decision]:
        """Same as `watch()`, but yields as it goes -- for progress bars.

        The recorded session is available as `engine.last_session` once the
        iterator is exhausted.
        """
        from videofeed import VideoFeed, build_triggers

        trigger_list = (build_triggers(list(triggers))
                        if triggers and not hasattr(next(iter(triggers), None), "check")
                        else list(triggers or []))

        recorder = SessionRecorder(name=name, source=str(video_path)).attach()
        self._last_session = None
        feed = VideoFeed(
            video_path,
            interval_s=interval_s,
            audio_window_s=audio_window_s,
            triggers=trigger_list,
            max_segments=max_segments,
            verbose=False,
        )
        try:
            with feed:
                for seg in feed.segments():
                    decision = self.look(
                        seg.frame, seg.audio, sample_rate=seg.sample_rate,
                        meta={
                            "source": "videofeed",
                            "video_time": seg.t,
                            "duration": seg.duration_s,
                            "index": seg.index,
                            "reasons": seg.reasons,
                        },
                    )
                    if on_decision is not None:
                        on_decision(decision)
                    yield decision
        finally:
            BUS.unsubscribe(recorder._on_event)
            self._last_session = recorder.to_dict()

    @property
    def last_session(self) -> Optional[dict]:
        return getattr(self, "_last_session", None)

    # ------------------------------------------------------------ internals --

    def _decide(self, scene: SceneRead, obs: Optional[Observation] = None,
                reasons: Optional[list[str]] = None) -> Decision:
        """scene -> antivibe -> candidates -> judge -> DJ -> play."""
        t0 = time.time()
        state: dict = {"scene": scene, "obs": obs, "t_start": t0,
                       "force": not self.respect_bounds}

        # Through the compiled LangGraph, entered at antagonize -- same nodes,
        # same edges, same conditional play/stop as the live loop.
        state = self.graph.decide_from_scene(state)
        decision = state.get("decision")

        anti = state.get("anti")
        verdict = (decision.verdict if decision is not None else None) or state.get("verdict")

        considered: dict[str, list] = {}
        for c in state.get("candidates") or []:
            considered.setdefault(c.strategy, []).append({
                "title": c.track.title,
                "artist": c.track.artist,
                "score": round(c.raw_distance, 3),
                "why": c.notes,
            })

        return Decision(
            scene={
                "setting": scene.setting,
                "activity": scene.activity,
                "mood": scene.mood_label,
                "confidence": scene.confidence,
                "tempo": scene.tempo_feel.value,
                "meter": scene.meter.value,
                "colors": list(scene.dominant_colors),
                "vibe": scene.vibe.model_dump(),
                "audio": scene.audio_summary,
                "source": scene.source,
            },
            opposite={
                "target_vibe": anti.target.model_dump() if anti else {},
                "looking_for": list(anti.target_genres[:8]) if anti else [],
                "why": anti.rationale if anti else "",
            },
            considered={k: v[:3] for k, v in considered.items()},
            chosen={
                "title": verdict.track.title,
                "artist": verdict.track.artist,
                "quip": verdict.quip,
                "strategy": verdict.strategy,
                "mismatch": round(verdict.mismatch, 3),
                "why": verdict.reasoning,
                "genres": list(verdict.track.genres),
                "tags": list(verdict.track.tags),
                "source": verdict.source,
            } if verdict else {},
            action=decision.action.value if decision is not None else "hold",
            mode=decision.mode.value if decision is not None else "",
            reason=decision.reason if decision is not None else "",
            video_time=(obs.meta or {}).get("video_time") if obs is not None else None,
            reasons=list(reasons or []),
            latency_ms=int((time.time() - t0) * 1000),
        )
