"""The agent graph.

Shape:

    capture -> [gate] --no-change--> END
                 |
              change
                 v
             perceive            (1 Gemini call, all scene fields)
                 v
            antagonize           (fan-out: 3 theories of wrongness, in parallel)
                 v
              judge              (1 Gemini call, picks the funniest + writes quip)
                 v
                dj               (bounds: cooldown / commitment / hysteresis)
                 v
              play + speak

LangGraph is used at the DJ/decision layer, which is where it actually earns
its keep: explicit state, conditional edges, and a place to hang interrupts
and retries. It is NOT used to fan out the perception fields, because those
belong in one call.

If langgraph isn't installed the same graph runs through a sequential
executor with identical semantics, so the repo is never un-runnable.
"""
from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Optional, TypedDict

from ..bus import BUS
from ..capture.base import Observation
from ..capture.gate import ChangeGate
from ..dj.controller import DJController
from ..music import strategies
from ..music.corpus import Corpus
from ..music.vibe import build_antivibe
from ..perceive import audio_features
from ..schemas import DJAction, DJDecision, SceneRead, Verdict
from .judge import build_judge
from ..log import notice as print  # stdout is reserved for data


class PipelineState(TypedDict, total=False):
    obs: Observation
    escalate: bool
    gate_reason: str
    scene: Optional[SceneRead]
    anti: Any
    candidates: list
    verdict: Optional[Verdict]
    decision: Optional[DJDecision]
    t_start: float
    force: bool          # must be declared, or LangGraph drops it between nodes


class BadSpotifyGraph:
    def __init__(self, cfg, perceiver, player, narrator):
        self.cfg = cfg
        self.perceiver = perceiver
        self.player = player
        self.narrator = narrator

        self.gate = ChangeGate(cfg.section("gate"))
        self.dj = DJController(cfg.section("dj"))
        self.judge = build_judge(cfg.section("judge"))
        self.corpus = Corpus.load()

        acfg = cfg.section("antagonize")
        self.strategy_names = acfg.get("strategies") or ["genre_antipode"]
        self.per_strategy = int(acfg.get("candidates_per_strategy", 4))

        self._pool = ThreadPoolExecutor(max_workers=4)
        self._last_scene: Optional[SceneRead] = None
        self._last_verdict: Optional[Verdict] = None
        self._compiled = self._compile()
        self._from_scene = self._compile_from_scene()

    # ------------------------------------------------------------- nodes --

    def n_gate(self, state: PipelineState) -> PipelineState:
        obs = state["obs"]

        # Some sources already know the world changed. The video sampler fires
        # on scene cuts and audio onsets, so re-running our own frame differ
        # would just re-derive a conclusion it already reached -- and disagree
        # with it at the margins, which is worse than not checking at all.
        if (obs.meta or {}).get("pre_gated"):
            reason = (obs.meta or {}).get("trigger") or "source says it changed"
            BUS.emit("gate", "escalate", reason=reason, pre_gated=True)
            return {**state, "escalate": True, "gate_reason": reason}

        v = self.gate.check(obs)
        BUS.emit("gate", "escalate" if v.escalate else "skip",
                 reason=v.reason, frame_delta=round(v.frame_delta, 4),
                 audio_delta=round(v.audio_delta, 4), onset_ratio=round(v.onset_ratio, 2))
        return {**state, "escalate": v.escalate, "gate_reason": v.reason}

    def n_stable(self, state: PipelineState) -> PipelineState:
        """The gate said nothing changed. That is not nothing -- it is
        evidence the scene is *stable*, which is exactly what the hysteresis
        rule is waiting for. Without this, a calm scene deadlocks: the gate
        suppresses every read after the first, so the second agreeing read
        never arrives and no song ever plays.

        Costs no model call. Reuses the last scene and the last verdict.
        """
        if self._last_scene is None:
            return {**state, "decision": None}
        BUS.emit("gate", "stable", reason="reusing last read (no model call)")
        return {**state, "scene": self._last_scene, "verdict": self._last_verdict}

    def n_perceive(self, state: PipelineState) -> PipelineState:
        obs = state["obs"]
        feats = audio_features.extract(obs.audio, obs.sample_rate)
        scene = self.perceiver.read(obs.frame, feats, obs.meta or {})
        BUS.emit("scene", scene.mood_label,
                 video_time=(obs.meta or {}).get("video_time"),
                 setting=scene.setting, activity=scene.activity,
                 vibe=scene.vibe.model_dump(), colors=scene.dominant_colors,
                 confidence=scene.confidence, tempo=scene.tempo_feel.value,
                 meter=scene.meter.value, audio=scene.audio_summary,
                 latency_ms=scene.latency_ms, source=scene.source)
        self._last_scene = scene
        return {**state, "scene": scene}

    def n_antagonize(self, state: PipelineState) -> PipelineState:
        scene = state["scene"]
        anti = build_antivibe(scene)
        BUS.emit("antivibe", anti.rationale,
                 target=anti.target.model_dump(),
                 target_genres=anti.target_genres[:8],
                 banned=anti.banned_genres)

        # genuine fan-out: three different theories of wrongness, concurrently
        futures = {
            name: self._pool.submit(
                strategies.generate, scene, anti, self.corpus,
                [name], self.dj.state.played_ids, self.per_strategy)
            for name in self.strategy_names
        }
        candidates = []
        for name, fut in futures.items():
            try:
                got = fut.result(timeout=5)
                candidates.extend(got)
                BUS.emit("candidates", name,
                         picks=[{"title": c.track.title, "artist": c.track.artist,
                                 "score": round(c.raw_distance, 3), "why": c.notes}
                                for c in got[:3]])
            except Exception as e:
                BUS.emit("error", f"strategy {name} failed", error=str(e))

        candidates.sort(key=lambda c: c.raw_distance, reverse=True)
        return {**state, "anti": anti, "candidates": candidates}

    def n_judge(self, state: PipelineState) -> PipelineState:
        candidates = state.get("candidates") or []
        if not candidates:
            BUS.emit("error", "no candidates survived")
            return {**state, "verdict": None}
        try:
            verdict = self.judge.judge(state["scene"], state["anti"], candidates)
            BUS.emit("verdict", verdict.track.title,
                     artist=verdict.track.artist, quip=verdict.quip,
                     strategy=verdict.strategy, mismatch=round(verdict.mismatch, 3),
                     reasoning=verdict.reasoning, runner_ups=verdict.runner_ups,
                     source=verdict.source)
            self._last_verdict = verdict
            return {**state, "verdict": verdict}
        except Exception as e:
            BUS.emit("error", "judge failed", error=str(e))
            self.dj.note_failure()
            return {**state, "verdict": None}

    def n_dj(self, state: PipelineState) -> PipelineState:
        decision = self.dj.decide(state["scene"], state.get("verdict"),
                                  force=bool(state.get("force")))
        BUS.emit("dj", decision.action.value, reason=decision.reason,
                 mode=decision.mode.value,
                 scene_delta=round(decision.scene_delta, 3),
                 wait=round(decision.seconds_until_eligible, 1))
        return {**state, "decision": decision}

    def n_play(self, state: PipelineState) -> PipelineState:
        decision = state.get("decision")
        if not decision or decision.action not in (DJAction.PLAY, DJAction.FALLBACK):
            return state
        verdict = decision.verdict
        if verdict is None:
            return state
        try:
            if verdict.quip:
                self.narrator.say(verdict.quip, duck=self.player)
                BUS.emit("voice", verdict.quip)
            self.player.play(verdict.track, mode=decision.mode.value)
            self.dj.commit(verdict, scene=state.get("scene"))
            BUS.emit("play", f"{verdict.track.title} - {verdict.track.artist}",
                     video_time=(state.get("obs").meta or {}).get("video_time")
                     if state.get("obs") is not None else None,
                     track_id=verdict.track.id, uri=verdict.track.uri,
                     genres=verdict.track.genres, tags=verdict.track.tags,
                     mode=decision.mode.value,
                     elapsed_ms=int((time.time() - state.get("t_start", time.time())) * 1000))
        except Exception as e:
            BUS.emit("error", "playback failed", error=str(e))
            self.dj.note_failure()
            fb = self.dj.fallback()
            if fb:
                try:
                    self.player.play(fb.track)
                    self.dj.commit(fb)
                    BUS.emit("play", f"[fallback] {fb.track.title}", track_id=fb.track.id)
                except Exception as e2:
                    BUS.emit("error", "fallback playback failed too", error=str(e2))
        return state

    # ---------------------------------------------------------- assembly --

    def _compile(self):
        try:
            from langgraph.graph import END, START, StateGraph
        except Exception:
            print("[graph] langgraph not installed -> sequential executor "
                  "(identical semantics)")
            return None

        g = StateGraph(PipelineState)
        g.add_node("gate", self.n_gate)
        g.add_node("stable", self.n_stable)
        g.add_node("perceive", self.n_perceive)
        g.add_node("antagonize", self.n_antagonize)
        g.add_node("judge", self.n_judge)
        g.add_node("dj", self.n_dj)
        g.add_node("play", self.n_play)

        g.add_edge(START, "gate")
        g.add_conditional_edges(
            "gate",
            lambda s: "perceive" if s.get("escalate") else "stable",
            {"perceive": "perceive", "stable": "stable"},
        )
        g.add_conditional_edges(
            "stable",
            lambda s: "dj" if s.get("scene") is not None else "stop",
            {"dj": "dj", "stop": END},
        )
        g.add_edge("perceive", "antagonize")
        g.add_edge("antagonize", "judge")
        g.add_edge("judge", "dj")
        g.add_conditional_edges(
            "dj",
            lambda s: "play" if s["decision"].action in (DJAction.PLAY, DJAction.FALLBACK) else "stop",
            {"play": "play", "stop": END},
        )
        g.add_edge("play", END)
        return g.compile()

    def _sequential(self, state: PipelineState) -> PipelineState:
        state = self.n_gate(state)
        if state.get("escalate"):
            state = self.n_perceive(state)
            state = self.n_antagonize(state)
            state = self.n_judge(state)
        else:
            state = self.n_stable(state)
            if state.get("scene") is None:
                return state
        state = self.n_dj(state)
        if state["decision"].action in (DJAction.PLAY, DJAction.FALLBACK):
            state = self.n_play(state)
        return state

    def _compile_from_scene(self):
        """The same graph, entered at antagonize instead of capture.

        Callers that already have a scene -- the Gradio app, a typed
        description, a single photo -- must not get a second hand-rolled
        pipeline. If there were two, they would drift, and the demo would
        behave differently from the thing we tested. Same nodes, same edges,
        same conditional play/stop; only the entry point differs.
        """
        try:
            from langgraph.graph import END, START, StateGraph
        except Exception:
            return None

        g = StateGraph(PipelineState)
        g.add_node("antagonize", self.n_antagonize)
        g.add_node("judge", self.n_judge)
        g.add_node("dj", self.n_dj)
        g.add_node("play", self.n_play)

        g.add_edge(START, "antagonize")
        g.add_edge("antagonize", "judge")
        g.add_edge("judge", "dj")
        g.add_conditional_edges(
            "dj",
            lambda s: ("play" if s["decision"].action in (DJAction.PLAY, DJAction.FALLBACK)
                       else "stop"),
            {"play": "play", "stop": END},
        )
        g.add_edge("play", END)
        return g.compile()

    def decide_from_scene(self, state: PipelineState) -> PipelineState:
        """Run the decision half of the graph on a scene we already have."""
        if state.get("scene") is None:
            raise ValueError("decide_from_scene needs a 'scene' in the state")
        state.setdefault("t_start", time.time())

        if self._from_scene is not None:
            return self._from_scene.invoke(state)

        state = self.n_antagonize(state)
        state = self.n_judge(state)
        state = self.n_dj(state)
        if state["decision"].action in (DJAction.PLAY, DJAction.FALLBACK):
            state = self.n_play(state)
        return state

    def tick(self, obs: Observation) -> PipelineState:
        state: PipelineState = {"obs": obs, "t_start": time.time()}
        if self._compiled is not None:
            return self._compiled.invoke(state)
        return self._sequential(state)
