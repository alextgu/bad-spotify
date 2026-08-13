"""Bounds. The unglamorous file that decides whether the demo looks broken.

Without this, a scene read that flickers between two labels switches the
track every 5 seconds and the whole thing reads as a random shuffle rather
than an intelligence. Three mechanisms:

  cooldown    hard floor between any two switches
  commitment  a track gets to finish making its point (min_track_seconds)
  hysteresis  N consecutive AGREEING scene reads before we act on a change

Plus the fallback ladder. The one unacceptable failure mode is silence:
if everything upstream breaks, we still play something terrible.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field

from ..schemas import DJAction, DJDecision, SceneRead, Verdict


@dataclass
class DJState:
    current: Verdict | None = None
    started_at: float = 0.0
    last_switch: float = 0.0
    pending_signature: str | None = None
    pending_count: int = 0
    consecutive_failures: int = 0
    played_ids: set[str] = field(default_factory=set)
    history: list[tuple[float, str]] = field(default_factory=list)


class DJController:
    def __init__(self, cfg: dict):
        self.min_track = float(cfg.get("min_track_seconds", 25))
        self.cooldown = float(cfg.get("cooldown_seconds", 8))
        self.agreement = int(cfg.get("agreement_reads", 2))
        self.max_failures = int(cfg.get("max_consecutive_failures", 3))
        self.state = DJState()

    # ---------------------------------------------------------------- gates

    def observe(self, scene: SceneRead, now: float | None = None) -> tuple[bool, str]:
        """Hysteresis. Returns (scene_change_confirmed, reason)."""
        sig = scene.signature()
        if self.state.pending_signature == sig:
            self.state.pending_count += 1
        else:
            self.state.pending_signature = sig
            self.state.pending_count = 1

        if scene.confidence < 0.35:
            return False, f"low confidence ({scene.confidence:.2f}), not acting"
        if self.state.pending_count < self.agreement:
            return False, (f"scene changed but only {self.state.pending_count}/"
                           f"{self.agreement} agreeing reads")
        return True, f"{self.state.pending_count} agreeing reads"

    def may_switch(self, now: float | None = None) -> tuple[bool, str, float]:
        now = now or time.time()
        if self.state.current is None:
            return True, "nothing playing", 0.0

        since_start = now - self.state.started_at
        since_switch = now - self.state.last_switch

        if since_switch < self.cooldown:
            wait = self.cooldown - since_switch
            return False, f"cooldown ({wait:.0f}s left)", wait
        if since_start < self.min_track:
            wait = self.min_track - since_start
            return False, f"committed to current track ({wait:.0f}s left)", wait
        return True, "eligible", 0.0

    # -------------------------------------------------------------- decide

    def decide(self, scene: SceneRead, verdict: Verdict | None,
               now: float | None = None) -> DJDecision:
        now = now or time.time()

        confirmed, why = self.observe(scene, now)
        if not confirmed:
            return DJDecision(action=DJAction.HOLD, reason=why)

        allowed, gate_reason, wait = self.may_switch(now)
        if not allowed:
            return DJDecision(action=DJAction.HOLD, reason=gate_reason,
                              seconds_until_eligible=wait)

        if verdict is None:
            fb = self.fallback()
            return DJDecision(action=DJAction.FALLBACK, verdict=fb,
                              reason="no verdict upstream; chaos deck engaged")

        if (self.state.current is not None
                and verdict.track.id == self.state.current.track.id):
            return DJDecision(action=DJAction.HOLD,
                              reason="judge picked the track already playing")

        return DJDecision(action=DJAction.PLAY, verdict=verdict, reason=why)

    def commit(self, verdict: Verdict, now: float | None = None) -> None:
        now = now or time.time()
        self.state.current = verdict
        self.state.started_at = now
        self.state.last_switch = now
        self.state.pending_count = 0
        self.state.consecutive_failures = 0
        self.state.played_ids.add(verdict.track.id)
        self.state.history.append((now, verdict.track.id))

    def note_failure(self) -> None:
        self.state.consecutive_failures += 1

    # ------------------------------------------------------------ fallback

    def fallback(self) -> Verdict | None:
        """The chaos deck: pre-vetted, always-wrong, needs no model at all."""
        from ..music.corpus import Corpus
        try:
            corpus = Corpus.load()
        except Exception:
            return None
        deck = [t for t in corpus.tracks
                if {"meme", "novelty", "grating"} & set(t.tags)
                and t.id not in self.state.played_ids]
        if not deck:
            deck = [t for t in corpus.tracks if t.id not in self.state.played_ids]
        if not deck:
            self.state.played_ids.clear()
            deck = corpus.tracks
        track = deck[len(self.state.history) % len(deck)]
        return Verdict(
            track=track, strategy="chaos_deck", cruelty=0.8,
            quip="Something has gone wrong. This is unrelated.",
            reasoning="fallback ladder engaged; silence is the only real bug",
            source="fallback",
        )
