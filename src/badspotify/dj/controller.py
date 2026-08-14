"""Bounds. The unglamorous file that decides whether the demo looks broken.

Two questions, not one:

  *Should* we act at all?   -- hysteresis and confidence
  *How* should we act?      -- queue politely, or cut the music off now?

Queueing is the default because it paces itself and never feels random.
Interrupting is reserved for the moments that earn it: the scene changed a
lot, and the current track has already had a fair run. A wrong song that
lands *while the moment is still happening* is much funnier than one that
turns up ninety seconds later -- but a system that interrupts constantly
just reads as broken.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field

from ..schemas import DJAction, DJDecision, PlayMode, SceneRead, Verdict, Vibe


@dataclass
class DJState:
    current: Verdict | None = None
    started_at: float = 0.0
    last_switch: float = 0.0
    last_vibe: Vibe | None = None
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

        # How much the world has to change before cutting the music off,
        # and how long a track is safe from being cut no matter what.
        self.interrupt_threshold = float(cfg.get("interrupt_threshold", 0.55))
        self.min_interrupt_seconds = float(cfg.get("min_interrupt_seconds", 15))

        self.state = DJState()

    # ---------------------------------------------------------------- gates

    def observe(self, scene: SceneRead) -> tuple[bool, str]:
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

    def scene_delta(self, scene: SceneRead) -> float:
        """How far the world moved since the track we're playing was chosen."""
        if self.state.last_vibe is None:
            return 1.0
        return self.state.last_vibe.distance(scene.vibe)

    def choose_mode(self, scene: SceneRead, now: float) -> tuple[PlayMode, float, str]:
        """Queue or interrupt? Returns (mode, delta, why)."""
        delta = self.scene_delta(scene)
        if self.state.current is None:
            return PlayMode.INTERRUPT, delta, "nothing playing, start immediately"

        elapsed = now - self.state.started_at
        if delta < self.interrupt_threshold:
            return (PlayMode.QUEUE, delta,
                    f"scene shifted {delta:.2f} (< {self.interrupt_threshold:.2f}), queueing")
        if elapsed < self.min_interrupt_seconds:
            return (PlayMode.QUEUE, delta,
                    f"scene shifted {delta:.2f} but track is only {elapsed:.0f}s old, queueing")
        return (PlayMode.INTERRUPT, delta,
                f"scene shifted {delta:.2f} after {elapsed:.0f}s, cutting in")

    def may_act(self, mode: PlayMode, now: float) -> tuple[bool, str, float]:
        """Queueing is cheap and nearly always allowed. Interrupting is not."""
        if self.state.current is None:
            return True, "nothing playing", 0.0

        since_switch = now - self.state.last_switch
        if since_switch < self.cooldown:
            return False, f"cooldown ({self.cooldown - since_switch:.0f}s left)", \
                   self.cooldown - since_switch

        if mode is PlayMode.QUEUE:
            return True, "queueing does not disturb the current track", 0.0

        since_start = now - self.state.started_at
        if since_start < self.min_track:
            wait = self.min_track - since_start
            return False, f"committed to current track ({wait:.0f}s left)", wait
        return True, "eligible to interrupt", 0.0

    # -------------------------------------------------------------- decide

    def decide(self, scene: SceneRead, verdict: Verdict | None,
               now: float | None = None, force: bool = False) -> DJDecision:
        """`force` is the stage button: a human pressing it is not thrashing.

        It skips hysteresis and the timing bounds, but nothing else -- the
        fallback ladder below still runs if the verdict is missing.
        """
        now = now or time.time()

        confirmed, why = self.observe(scene)
        if force:
            why = "forced (scene injection)"
        elif not confirmed:
            return DJDecision(action=DJAction.HOLD, reason=why)

        if force:
            # Cut in: the point of the button is that the change lands now.
            mode, delta, mode_why = (PlayMode.INTERRUPT, self.scene_delta(scene),
                                     "bounds bypassed, cutting in")
        else:
            mode, delta, mode_why = self.choose_mode(scene, now)

            allowed, gate_reason, wait = self.may_act(mode, now)
            if not allowed:
                return DJDecision(action=DJAction.HOLD, mode=mode, scene_delta=delta,
                                  reason=gate_reason, seconds_until_eligible=wait)

        if verdict is None:
            fb = self.fallback()
            return DJDecision(action=DJAction.FALLBACK, verdict=fb, mode=mode,
                              scene_delta=delta,
                              reason="no verdict upstream; chaos deck engaged")

        if (self.state.current is not None
                and verdict.track.id == self.state.current.track.id):
            return DJDecision(action=DJAction.HOLD, mode=mode, scene_delta=delta,
                              reason="judge picked the track already playing")

        return DJDecision(action=DJAction.PLAY, verdict=verdict, mode=mode,
                          scene_delta=delta, reason=f"{why}; {mode_why}")

    def commit(self, verdict: Verdict, scene: SceneRead | None = None,
               now: float | None = None) -> None:
        now = now or time.time()
        self.state.current = verdict
        self.state.started_at = now
        self.state.last_switch = now
        self.state.pending_count = 0
        self.state.consecutive_failures = 0
        self.state.played_ids.add(verdict.track.id)
        self.state.history.append((now, verdict.track.id))
        if scene is not None:
            self.state.last_vibe = scene.vibe

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
