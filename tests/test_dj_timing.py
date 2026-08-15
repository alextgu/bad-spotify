"""When the song changes -- the two failures that make it look broken.

Changing too often reads as a shuffle button with extra steps. Changing too
late reads as lag, and the joke dies with it. Both are the same knob, so both
live in one file: every test here pins one side of it without loosening the
other.

The numbers are not taste. They were measured against the real corpus on
14 Aug 2026: random jitter moves the music target by up to ~0.23 and flips the
top pick 37% of the time, while the smallest genuine scene change moves it
0.56 (median 0.84). The deadband sits in that gap.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from badspotify.dj.controller import DJController          # noqa: E402
from badspotify.music.vibe import build_antivibe           # noqa: E402
from badspotify.perceive.scene import scene_from_text      # noqa: E402
from badspotify.schemas import PlayMode, Track, Verdict, Vibe   # noqa: E402

CFG = dict(cooldown_seconds=8, agreement_reads=2, min_track_seconds=25,
           interrupt_threshold=0.55, min_interrupt_seconds=15,
           hold_threshold=0.30, jump_threshold=0.55, min_change_seconds=20)

LIBRARY = "a silent library during exam week"
PARTY = "a toddler's birthday party, cake being cut"


def track(i: int) -> Track:
    return Track(id=f"t{i}", title=f"Track {i}", artist="A", vibe=Vibe())


def drive(scene_at, ticks: int = 25, step: float = 2.5, cfg: dict | None = None):
    """Run the controller the way the graph does, and return the commits.

    Mirrors `n_antagonize` -> `n_dj` -> `n_play`: ask the deadband first, and
    model the fact that `played_ids` forces a NEW track id on every pass.
    """
    dj = DJController(cfg or CFG)
    commits: list[tuple[float, str]] = []
    t = 0.0
    for k in range(ticks):
        t += step
        scene = scene_at(k, t)
        anti = build_antivibe(scene)
        go, _why = dj.should_reconsider(scene, anti.target, now=t)
        if not go:
            continue
        fresh = [i for i in range(200) if f"t{i}" not in dj.state.played_ids]
        verdict = Verdict(track=track(fresh[0]), strategy="genre_antipode")
        decision = dj.decide(scene, verdict, now=t, pre_approved=True)
        if decision.action.value == "play":
            dj.commit(decision.verdict, scene, now=t, mode=decision.mode,
                      target=anti.target)
            commits.append((t, decision.verdict.track.id))
    return dj, commits


# ------------------------------------------------- not changing too much --


def test_a_scene_that_never_changes_gets_exactly_one_track():
    """The regression that started this. Measured before the fix: 6 tracks in
    62 seconds of identical footage, every decision reporting delta 0.000.

    It happened because `played_ids` excludes whatever is playing, so the judge
    could never propose the current track and the "already playing" guard never
    fired. Nothing was wrong with the judge -- it was being asked a question it
    should never have been asked.
    """
    scene = scene_from_text(LIBRARY)
    _dj, commits = drive(lambda k, t: scene)
    assert len(commits) == 1, f"expected one track, got {len(commits)}: {commits}"


#Six real reads of ONE unchanged frame, gemini-3.5-flash-lite, 14 Aug 2026.
#Measured rather than invented: an earlier version of this test used Gaussian
#jitter at sd=0.08, which moves the target up to 0.567 -- three times what the
#actual model does, and enough to overlap a genuine scene change. Tuning the
#thresholds against imaginary noise would have made the agent sluggish for no
#reason. Real pairwise target movement across these: mean 0.117, max 0.173.
MEASURED_STILL_FRAME_VIBES = [
    (0.50, 0.05, 0.10, 0.05, 0.90),
    (0.50, 0.10, 0.10, 0.10, 0.80),
    (0.50, 0.10, 0.00, 0.10, 0.90),
    (0.50, 0.05, 0.10, 0.15, 0.90),
    (0.50, 0.10, 0.10, 0.10, 0.90),
    (0.50, 0.10, 0.00, 0.10, 0.90),
]


def test_real_model_read_noise_never_changes_the_song():
    """Two reads of one unchanged frame are never identical. That wobble is
    the model disagreeing with itself, not the world moving, and it must not
    cost a track."""
    def wobbling(k, t):
        s = scene_from_text(LIBRARY)
        s.vibe = Vibe.from_tuple(
            MEASURED_STILL_FRAME_VIBES[k % len(MEASURED_STILL_FRAME_VIBES)])
        return s

    _dj, commits = drive(wobbling)
    assert len(commits) == 1, f"the model's own noise moved the music: {commits}"


def test_the_deadband_clears_real_model_noise_with_margin():
    """The thresholds are only meaningful relative to how much the model
    actually wobbles. If a model change ever widens that wobble past the
    deadband, this fails first and loudly rather than showing up as churn on
    stage."""
    targets = [build_antivibe(_scene_with(v)).target
               for v in MEASURED_STILL_FRAME_VIBES]
    worst = max(targets[i].distance(targets[j])
                for i in range(len(targets)) for j in range(i + 1, len(targets)))
    dj = DJController(CFG)
    assert worst < dj.hold_threshold, (
        f"model noise ({worst:.3f}) reaches the deadband "
        f"({dj.hold_threshold}) -- it will churn")
    #0.563 is the smallest genuine scene change measured across the demo set.
    assert dj.jump_threshold < 0.563, (
        "jump_threshold is above the smallest real scene change, so real "
        "changes will wait out the dwell floor")


def _scene_with(vibe_tuple):
    s = scene_from_text(LIBRARY)
    s.vibe = Vibe.from_tuple(vibe_tuple)
    return s


def test_two_rooms_that_invert_the_same_way_do_not_get_a_new_song():
    """The deadband is on the TARGET, not the scene. A different-looking room
    that wants the same music is not a reason to change the music."""
    dj = DJController(CFG)
    scene = scene_from_text(LIBRARY)
    anti = build_antivibe(scene)
    dj.commit(Verdict(track=track(0), strategy="s"), scene, now=0.0,
              mode=PlayMode.INTERRUPT, target=anti.target)

    nudged = scene_from_text(LIBRARY)
    v = np.clip(np.array(nudged.vibe.as_tuple()) + 0.03, 0, 1)
    nudged.vibe = Vibe.from_tuple(v)

    go, why = dj.should_reconsider(nudged, build_antivibe(nudged).target, now=100.0)
    assert not go, why
    assert "still the right answer" in why


def test_low_confidence_never_moves_the_music():
    dj = DJController(CFG)
    scene = scene_from_text(LIBRARY)
    dj.commit(Verdict(track=track(0), strategy="s"), scene, now=0.0,
              mode=PlayMode.INTERRUPT, target=build_antivibe(scene).target)

    blurry = scene_from_text(PARTY)
    blurry.confidence = 0.2
    go, why = dj.should_reconsider(blurry, build_antivibe(blurry).target, now=999.0)
    assert not go and "confidence" in why


def test_an_unreadable_frame_costs_nothing_even_on_a_cold_start():
    """Confidence is checked before "nothing playing", not after.

    Caught on real footage: pointed at a covered lens, Gemini honestly returned
    confidence 0.10 every tick -- and because nothing was playing yet, the gate
    said "reconsider", ran three strategies and a judge, and only then held on
    confidence. Not knowing what you are looking at is a reason to spend
    nothing, whether or not music is already going.
    """
    dj = DJController(CFG)
    blurry = scene_from_text(PARTY)
    blurry.confidence = 0.10
    assert dj.state.current is None                    # cold start
    go, why = dj.should_reconsider(blurry, build_antivibe(blurry).target, now=1.0)
    assert not go, "an unreadable frame started the whole pipeline"
    assert "confidence" in why


# -------------------------------------------------- not changing too late --


def test_a_hard_cut_is_answered_within_one_read():
    """A big change must not wait out the agreement counter. Waiting for a
    second opinion on a park -> funeral cut is how the joke arrives after the
    moment has passed."""
    lib, party = scene_from_text(LIBRARY), scene_from_text(PARTY)
    cut_at, step = 32.5, 2.5
    _dj, commits = drive(lambda k, t: lib if t < cut_at else party, step=step)

    assert len(commits) == 2, f"expected first track + reaction, got {commits}"
    lateness = commits[1][0] - cut_at
    #ONE read. This asserted <= 2.5 before, which two reads at a 2.5s cadence
    #passed by coincidence -- and hid the fact that `decide()` was re-gating on
    #`observe()` and quietly costing an extra read on every hard cut.
    assert lateness <= step, (
        f"reacted {lateness:.1f}s after the cut -- more than one read ({step}s)")


def test_a_big_jump_bypasses_the_dwell_floor():
    """The dwell floor stops churn; it must not stop a real event. A track that
    started one second ago still loses to the room catching fire."""
    dj = DJController(CFG)
    lib = scene_from_text(LIBRARY)
    dj.commit(Verdict(track=track(0), strategy="s"), lib, now=100.0,
              mode=PlayMode.INTERRUPT, target=build_antivibe(lib).target)

    party = scene_from_text(PARTY)
    go, why = dj.should_reconsider(party, build_antivibe(party).target, now=101.0)
    assert go, f"a 1s-old track blocked a hard cut: {why}"
    assert "jump" in why


def test_a_moderate_change_still_waits_for_a_second_read():
    """Between the two thresholds, confirmation is worth the delay -- this is
    the band where a single odd read would otherwise cost a track."""
    dj = DJController(dict(CFG, hold_threshold=0.05, jump_threshold=5.0,
                           min_change_seconds=0))
    lib = scene_from_text(LIBRARY)
    dj.commit(Verdict(track=track(0), strategy="s"), lib, now=0.0,
              mode=PlayMode.INTERRUPT, target=build_antivibe(lib).target)

    party = scene_from_text(PARTY)
    target = build_antivibe(party).target
    go, why = dj.should_reconsider(party, target, now=50.0)
    assert not go and "1/2" in why
    go, why = dj.should_reconsider(party, target, now=52.5)
    assert go and "2 agreeing" in why


# ----------------------------------------------------------- the clocks --


def test_queueing_does_not_restart_the_interrupt_clock():
    """`started_at` is what the interrupt bounds read, so it may only move when
    audio actually starts. It used to be stamped on every commit including a
    QUEUE -- so a queued track reset the clock for the track still playing, and
    `min_track_seconds` measured time since queueing, which is nothing.
    """
    dj = DJController(CFG)
    scene = scene_from_text(LIBRARY)

    dj.commit(Verdict(track=track(0), strategy="s"), scene, now=100.0,
              mode=PlayMode.INTERRUPT, target=build_antivibe(scene).target)
    assert dj.state.started_at == 100.0

    dj.commit(Verdict(track=track(1), strategy="s"), scene, now=140.0,
              mode=PlayMode.QUEUE, target=build_antivibe(scene).target)
    assert dj.state.started_at == 100.0, "a queued track restarted the clock"
    assert dj.state.last_switch == 140.0, "commit time must still advance"


def test_the_first_track_starts_the_clock_even_when_queued():
    """Nothing is playing, so there is nothing to be polite to."""
    dj = DJController(CFG)
    scene = scene_from_text(LIBRARY)
    dj.commit(Verdict(track=track(0), strategy="s"), scene, now=7.0,
              mode=PlayMode.QUEUE, target=build_antivibe(scene).target)
    assert dj.state.started_at == 7.0


def test_a_slow_drift_is_eventually_answered():
    """Dusk falling, or a party winding down: every read moves the target less
    than the deadband, but the room genuinely ends up somewhere else.

    This works only because the deadband measures against the target that was
    committed, NOT against the previous read. A sliding reference would let the
    room walk anywhere one small step at a time and never notice -- the classic
    way a hysteresis gate goes deaf. If someone ever "optimises" this to compare
    consecutive reads, this test is what should stop them.
    """
    dj = DJController(dict(CFG, min_change_seconds=0))
    scene = scene_from_text(LIBRARY)
    base = np.array(scene.vibe.as_tuple())
    dj.commit(Verdict(track=track(0), strategy="s"), scene, now=0.0,
              mode=PlayMode.INTERRUPT, target=build_antivibe(scene).target)

    fired_at = None
    for step in range(1, 40):
        drifting = scene_from_text(LIBRARY)
        #Each step is a small nudge along one axis -- never a jump.
        drifting.vibe = Vibe.from_tuple(np.clip(base + 0.02 * step, 0, 1))
        go, why = dj.should_reconsider(drifting, build_antivibe(drifting).target,
                                       now=10.0 * step)
        if go:
            fired_at = step
            break

    assert fired_at is not None, "drifted the whole range and never reacted"
    assert "jump" not in (why or ""), "a drift should not read as a jump"


def test_a_wobbling_mood_label_can_never_cause_silence():
    """The starvation bug. `decide()` used to re-gate on `observe()`, which
    counts repeats of the raw scene *signature* -- and that signature includes
    the model's free-text `mood_label`. A real model says "serene" on one read
    and "contemplative" on the next, so the counter resets forever and the
    agent never plays anything again.

    This repo's first rule is that silence is the only real bug, so the target
    gate owns the decision and `decide()` trusts it.
    """
    dj = DJController(CFG)
    commits = 0
    for k in range(12):
        scene = scene_from_text(PARTY if k % 2 else LIBRARY)
        scene.mood_label = f"mood-{k}"          # never repeats
        anti = build_antivibe(scene)
        go, _ = dj.should_reconsider(scene, anti.target, now=100.0 * k)
        if not go:
            continue
        d = dj.decide(scene, Verdict(track=track(k), strategy="s"),
                      now=100.0 * k, pre_approved=True)
        if d.action.value == "play":
            dj.commit(d.verdict, scene, now=100.0 * k, mode=d.mode,
                      target=anti.target)
            commits += 1
    assert commits > 0, "a wobbling mood label silenced the agent forever"


def test_a_jump_is_not_swallowed_by_the_cooldown():
    """The cooldown stops thrash between two ordinary decisions. A jump has
    already earned its way past the bounds -- if the cooldown eats it too, the
    change can be over before the agent is allowed to answer it."""
    dj = DJController(CFG)
    lib = scene_from_text(LIBRARY)
    dj.commit(Verdict(track=track(0), strategy="s"), lib, now=100.0,
              mode=PlayMode.INTERRUPT, target=build_antivibe(lib).target)

    party = scene_from_text(PARTY)
    anti = build_antivibe(party)
    go, why = dj.should_reconsider(party, anti.target, now=101.0)   # 1s later
    assert go and "jump" in why

    d = dj.decide(party, Verdict(track=track(1), strategy="s"),
                  now=101.0, pre_approved=True)
    assert d.action.value == "play", f"cooldown ate the jump: {d.reason}"


def test_a_commit_without_a_target_does_not_leave_a_stale_one():
    """A stale reference measures the deadband against the wrong point, which
    can hold through a real change. Unknown must mean "look again"."""
    dj = DJController(CFG)
    lib = scene_from_text(LIBRARY)
    dj.commit(Verdict(track=track(0), strategy="s"), lib, now=0.0,
              mode=PlayMode.INTERRUPT, target=build_antivibe(lib).target)
    dj.commit(Verdict(track=track(1), strategy="s"), lib, now=50.0,
              mode=PlayMode.INTERRUPT, target=None)
    assert dj.state.current_target is None

    go, why = dj.should_reconsider(lib, build_antivibe(lib).target, now=100.0)
    assert go and "no target on record" in why


def _graph_on_mocks():
    from badspotify.agents.graph import BadSpotifyGraph
    from badspotify.config import load_config
    from badspotify.perceive.scene import build_perceiver
    from badspotify.players.mock import MockPlayer
    from badspotify.voice.narrator import build_narrator

    cfg = load_config(Path(__file__).resolve().parents[1] / "config.yaml")
    cfg.setdefault("perceive", {})["backend"] = "mock"
    cfg.setdefault("player", {})["backend"] = "mock"
    return BadSpotifyGraph(cfg, build_perceiver(cfg["perceive"]),
                           MockPlayer({}), build_narrator({"backend": "mock"}))


def test_a_quiet_tick_still_passes_through_the_deadband():
    """A quiet tick -- the change gate saw nothing, so perception is skipped
    and the last read is reused -- used to route straight to the DJ, skipping
    the deadband entirely.

    That left `decide()` as the only bound on the commonest path in a real run,
    and it ran three strategies and a judge against a scene nobody had re-read.
    Caught only by watching a live run: 11 holds, none of them from the
    deadband. Testing the nodes directly missed it because that never
    exercises the quiet branch.
    """
    g = _graph_on_mocks()
    scene = scene_from_text(LIBRARY)
    anti = build_antivibe(scene)
    g.dj.commit(Verdict(track=track(0), strategy="s"), scene,
                mode=PlayMode.INTERRUPT, target=anti.target)

    #A quiet tick: scene already known, nothing re-read.
    state = g.n_stable({"scene": scene, "escalate": False})
    state = g.n_antagonize(state)

    assert state.get("hold"), "the deadband did not run on a quiet tick"
    assert "still the right answer" in state["hold"]
    assert not state.get("approved")
    assert not state.get("candidates"), "strategies ran on a held tick"


def test_a_tick_that_skipped_the_deadband_is_never_marked_approved():
    """`pre_approved` disables the older raw-signature gate, so claiming it
    without having run the deadband removes every bound at once."""
    g = _graph_on_mocks()
    scene = scene_from_text(LIBRARY)
    state = g.n_dj({"scene": scene, "verdict": None})
    #No `approved` key -> decide() must fall back to its own gating, not sail
    #through. It may hold or engage the fallback, but it must not claim
    #approval it never got.
    assert state["decision"] is not None
    assert "target gate approved" not in state["decision"].reason


def test_nothing_playing_always_reconsiders():
    dj = DJController(CFG)
    scene = scene_from_text(LIBRARY)
    go, why = dj.should_reconsider(scene, build_antivibe(scene).target, now=0.0)
    assert go and "nothing playing" in why


def test_failed_playback_retries_with_backoff():
    dj = DJController(CFG)
    scene = scene_from_text(LIBRARY)
    target = build_antivibe(scene).target
    dj.note_failure(now=100.0)

    go, why = dj.should_reconsider(scene, target, now=102.0)
    assert not go and "retry in" in why
    go, why = dj.should_reconsider(scene, target, now=108.0)
    assert go and why == "nothing playing"
