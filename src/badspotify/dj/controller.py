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

    #The music target that justified `current`. The deadband is measured
    #against THIS, not against the raw scene -- see should_reconsider.
    current_target: Vibe | None = None
    #Consecutive reads that agree the target has left the deadband.
    moved_count: int = 0
    #Set by should_reconsider when the move was big enough to act on one read.
    #A jump has already earned its way past the bounds; it must not then be
    #swallowed by the cooldown.
    pending_jump: bool = False


class DJController:
    def __init__(self, cfg: dict):
        self.min_track = float(cfg.get("min_track_seconds", 25))
        self.cooldown = float(cfg.get("cooldown_seconds", 8))
        self.agreement = int(cfg.get("agreement_reads", 2))
        self.max_failures = int(cfg.get("max_consecutive_failures", 3))

        #Sets the scene change and playback time needed for an interruption
        self.interrupt_threshold = float(cfg.get("interrupt_threshold", 0.55))
        self.min_interrupt_seconds = float(cfg.get("min_interrupt_seconds", 15))

        #The deadband. Measured on 14 Aug against the real corpus: random
        #jitter moves the target up to ~0.23 and flips the top pick 37% of the
        #time, while the smallest REAL scene change moves it 0.56. Anything in
        #that gap is a safe floor; below it a re-decision is guaranteed churn.
        self.hold_threshold = float(cfg.get("hold_threshold", 0.30))
        #A change this large is unmistakable -- act on one read rather than
        #waiting for a second. This is the "don't be late" half. Set to the
        #SMALLEST genuine scene change in the measurement (0.563): anything
        #that moves at least as far as the smallest real change we have ever
        #seen is treated as real. It was 0.85, which sat above the median real
        #change of 0.84 -- so most true scene changes took the slow path and
        #waited out the dwell floor for no reason.
        self.jump_threshold = float(cfg.get("jump_threshold", 0.55))
        #Floor between two committed tracks, bypassed only by a jump.
        self.min_change_seconds = float(cfg.get("min_change_seconds", 20))
        self.min_confidence = float(cfg.get("min_confidence", 0.35))

        self.state = DJState()

    #Safety checks

    def observe(self, scene: SceneRead) -> tuple[bool, str]:
        """Hysteresis. Returns (scene_change_confirmed, reason)."""
        sig = scene.signature()
        if self.state.pending_signature == sig:
            self.state.pending_count += 1
        else:
            self.state.pending_signature = sig
            self.state.pending_count = 1

        if scene.confidence < self.min_confidence:
            return False, f"low confidence ({scene.confidence:.2f}), not acting"
        if self.state.pending_count < self.agreement:
            return False, (f"scene changed but only {self.state.pending_count}/"
                           f"{self.agreement} agreeing reads")
        return True, f"{self.state.pending_count} agreeing reads"

    def should_reconsider(self, scene: SceneRead, target: Vibe,
                          now: float | None = None) -> tuple[bool, str]:
        """The cheap question, asked BEFORE the strategies and the judge run.

        The old order asked it last: a stable scene paid for a perception call,
        three strategies and a judge, and only then heard "hold". Worse, it
        didn't even hold -- `played_ids` excludes whatever is playing, so the
        judge was FORCED to return a different track every time and the
        "already playing" guard never fired. Measured: 6 tracks in 62 seconds
        of footage that never changed, every one reporting scene_delta 0.000.

        The fix is to ask about the TARGET rather than the scene. Two different
        rooms that invert to the same music do not need a new song -- the one
        that's playing is still the right answer. Only when the target leaves
        the deadband is there anything new to decide.
        """
        #`or` would swallow now=0.0 -- a legitimate timestamp in tests and in
        #any replay that starts its clock at zero.
        now = time.time() if now is None else now
        s = self.state

        #Confidence first, even before "nothing playing". Not knowing what we
        #are looking at is a reason to spend nothing at all -- and on a cold
        #start with an unreadable frame the old order still paid for three
        #strategies and a judge on every tick before holding anyway.
        if scene.confidence < self.min_confidence:
            s.moved_count = 0
            return False, f"low confidence ({scene.confidence:.2f}), not acting"
        if s.current is None:
            return True, "nothing playing"
        if s.current_target is None:
            return True, "no target on record for the current track"

        moved = s.current_target.distance(target)
        s.pending_jump = False

        if moved < self.hold_threshold:
            s.moved_count = 0          #re-arm: the world settled back down
            return False, (f"target moved {moved:.2f} < {self.hold_threshold:.2f}; "
                           f"still the right answer")

        #Unmistakable change: don't make the room wait for a second opinion.
        if moved >= self.jump_threshold:
            s.pending_jump = True
            return True, f"target jumped {moved:.2f}, acting on one read"

        since = now - s.last_switch
        if since < self.min_change_seconds:
            return False, (f"target moved {moved:.2f} but last change was "
                           f"{since:.0f}s ago (floor {self.min_change_seconds:.0f}s)")

        s.moved_count += 1
        if s.moved_count < self.agreement:
            return False, (f"target moved {moved:.2f}, {s.moved_count}/"
                           f"{self.agreement} agreeing reads")
        return True, f"target moved {moved:.2f}, {s.moved_count} agreeing reads"

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
        if since_switch < self.cooldown and not self.state.pending_jump:
            return False, f"cooldown ({self.cooldown - since_switch:.0f}s left)", \
                   self.cooldown - since_switch

        if mode is PlayMode.QUEUE:
            return True, "queueing does not disturb the current track", 0.0

        since_start = now - self.state.started_at
        if since_start < self.min_track:
            wait = self.min_track - since_start
            return False, f"committed to current track ({wait:.0f}s left)", wait
        return True, "eligible to interrupt", 0.0

    #Action selection

    def decide(self, scene: SceneRead, verdict: Verdict | None,
               now: float | None = None, force: bool = False,
               pre_approved: bool = False) -> DJDecision:
        """`force` skips the bounds.

        The bounds exist to stop a live camera thrashing between two readings.
        A human deliberately asking for one decision -- pressing a button on
        the site, running a single photo through a script -- is not thrashing,
        and making them wait out a cooldown just looks broken.

        `force` deliberately also skips the confidence floor: someone who
        uploads a blurry photo and presses the button has asked a direct
        question, and answering "no" to it reads as broken rather than careful.
        The floor still applies to everything the agent decides on its own.

        `pre_approved` means `should_reconsider` already ran and said yes.
        Without it this method re-runs `observe()`, which asks a DIFFERENT and
        much twitchier question: whether the raw scene *signature* repeated.
        That signature includes the model's free-text `mood_label`, and a real
        model says "serene" one read and "contemplative" the next -- so the
        counter can reset forever, and a system whose only real bug is silence
        goes quiet permanently. The target gate is the one that decides.
        """
        #`or` would swallow now=0.0 -- a legitimate timestamp in tests and in
        #any replay that starts its clock at zero.
        now = time.time() if now is None else now

        if force:
            why = "forced (single request, bounds skipped)"
        elif pre_approved:
            why = "target gate approved"
        else:
            confirmed, why = self.observe(scene)
            if not confirmed:
                return DJDecision(action=DJAction.HOLD, reason=why)

        mode, delta, mode_why = self.choose_mode(scene, now)

        if not force:
            allowed, gate_reason, wait = self.may_act(mode, now)
            if not allowed:
                return DJDecision(action=DJAction.HOLD, mode=mode, scene_delta=delta,
                                  reason=gate_reason, seconds_until_eligible=wait)

        if verdict is None:
            fb = self.fallback()
            return DJDecision(action=DJAction.FALLBACK, verdict=fb, mode=mode,
                              scene_delta=delta,
                              reason="no verdict upstream; chaos deck engaged")

        if (not force and self.state.current is not None
                and verdict.track.id == self.state.current.track.id):
            return DJDecision(action=DJAction.HOLD, mode=mode, scene_delta=delta,
                              reason="judge picked the track already playing")

        return DJDecision(action=DJAction.PLAY, verdict=verdict, mode=mode,
                          scene_delta=delta, reason=f"{why}; {mode_why}")

    def commit(self, verdict: Verdict, scene: SceneRead | None = None,
               now: float | None = None, mode: PlayMode | None = None,
               target: Vibe | None = None) -> None:
        """Record what we just committed to.

        `started_at` is the clock the interrupt bounds read, so it may only
        move when audio actually starts. A QUEUED track has not started -- the
        previous one is still playing -- and setting it here was making
        `min_track_seconds` and `min_interrupt_seconds` measure time since
        *queueing*, which is not a thing anyone cares about.

        Nothing in the system knows when a track ends (no `Track.duration_s`,
        no player progress), so a queued track's true start is genuinely
        unknowable here. `last_switch` -- commit time -- is what the dwell
        floor uses, and that is always correct.
        """
        #`or` would swallow now=0.0 -- a legitimate timestamp in tests and in
        #any replay that starts its clock at zero.
        now = time.time() if now is None else now
        s = self.state
        started = mode is None or mode is PlayMode.INTERRUPT or s.current is None
        s.current = verdict
        if started:
            s.started_at = now
        s.last_switch = now
        s.pending_count = 0
        s.moved_count = 0
        s.pending_jump = False
        s.consecutive_failures = 0
        s.played_ids.add(verdict.track.id)
        s.history.append((now, verdict.track.id))
        if scene is not None:
            s.last_vibe = scene.vibe
        #Always overwrite, even with None. Keeping the PREVIOUS track's target
        #would silently measure the deadband against the wrong reference; a
        #None means "unknown", and should_reconsider treats unknown as a reason
        #to look again. Fail towards deciding, never towards going quiet.
        s.current_target = target

    def note_failure(self) -> None:
        self.state.consecutive_failures += 1

    #Fallback action

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
            track=track, strategy="chaos_deck", mismatch=0.8,
            quip="Something has gone wrong. This is unrelated.",
            reasoning="fallback ladder engaged; silence is the only real bug",
            source="fallback",
        )
