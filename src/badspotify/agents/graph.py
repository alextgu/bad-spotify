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
        self.cruelty = float(acfg.get("cruelty", 0.85))
        self.strategy_names = acfg.get("strategies") or ["genre_antipode"]
        self.per_strategy = int(acfg.get("candidates_per_strategy", 4))

        self._pool = ThreadPoolExecutor(max_workers=4)
        self._compiled = self._compile()

    # ------------------------------------------------------------- nodes --

    def n_gate(self, state: PipelineState) -> PipelineState:
        v = self.gate.check(state["obs"])
        BUS.emit("gate", "escalate" if v.escalate else "skip",
                 reason=v.reason, frame_delta=round(v.frame_delta, 4),
                 audio_delta=round(v.audio_delta, 4), onset_ratio=round(v.onset_ratio, 2))
        return {**state, "escalate": v.escalate, "gate_reason": v.reason}

    def n_perceive(self, state: PipelineState) -> PipelineState:
        obs = state["obs"]
        feats = audio_features.extract(obs.audio, obs.sample_rate)
        scene = self.perceiver.read(obs.frame, feats, obs.meta or {})
        BUS.emit("scene", scene.mood_label,
                 setting=scene.setting, activity=scene.activity,
                 vibe=scene.vibe.model_dump(), colors=scene.dominant_colors,
                 confidence=scene.confidence, tempo=scene.tempo_feel.value,
                 meter=scene.meter.value, audio=scene.audio_summary,
                 latency_ms=scene.latency_ms, source=scene.source)
        return {**state, "scene": scene}

    def n_antagonize(self, state: PipelineState) -> PipelineState:
        scene = state["scene"]
        anti = build_antivibe(scene, self.cruelty)
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
                     strategy=verdict.strategy, cruelty=round(verdict.cruelty, 3),
                     reasoning=verdict.reasoning, runner_ups=verdict.runner_ups,
                     source=verdict.source)
            return {**state, "verdict": verdict}
        except Exception as e:
            BUS.emit("error", "judge failed", error=str(e))
            self.dj.note_failure()
            return {**state, "verdict": None}

    def n_dj(self, state: PipelineState) -> PipelineState:
        decision = self.dj.decide(state["scene"], state.get("verdict"))
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
        g.add_node("perceive", self.n_perceive)
        g.add_node("antagonize", self.n_antagonize)
        g.add_node("judge", self.n_judge)
        g.add_node("dj", self.n_dj)
        g.add_node("play", self.n_play)

        g.add_edge(START, "gate")
        g.add_conditional_edges(
            "gate",
            lambda s: "perceive" if s.get("escalate") else "stop",
            {"perceive": "perceive", "stop": END},
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
        if not state.get("escalate"):
            return state
        state = self.n_perceive(state)
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
