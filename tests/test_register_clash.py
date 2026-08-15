"""Being wrong about the OCCASION, not just about the sound.

The other three strategies only know acoustics, so the worst they can manage is
"loud where it should be quiet". This one knows what a funeral is, which is how
a nursery rhyme -- sonically unremarkable, and therefore invisible to the other
three -- becomes the worst thing in the building.

The other half of this file guards the project's one hard rule: the system has
no notion of anyone's race, sex, religion, politics or identity. `references` is
the field where that would leak in, so it is filtered in code and not merely
requested in a prompt.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from badspotify.music.corpus import Corpus                     # noqa: E402
from badspotify.music.strategies import (                      # noqa: E402
    OCCASION_EXPECTS, REGISTRY, genre_antipode, register_clash,
)
from badspotify.music.vibe import build_antivibe               # noqa: E402
from badspotify.perceive.scene import (                        # noqa: E402
    _clean_references, scene_from_text,
)

CORPUS = Corpus.load()


def picks(scene, fn=register_clash, n=4):
    return fn(scene, build_antivibe(scene), CORPUS, set(), n)


# ------------------------------------------------------------ the strategy --


def test_it_is_registered_as_a_strategy():
    assert REGISTRY["register_clash"] is register_clash


def test_no_references_means_no_opinion():
    """With nothing to be wrong about it must stay quiet rather than guess --
    an empty shortlist costs nothing, a made-up one costs a track."""
    scene = scene_from_text("a funeral service")
    scene.references = []
    assert picks(scene) == []


def test_it_never_proposes_what_belongs_at_the_occasion():
    """The one thing that would make it useless: recommending the right song."""
    scene = scene_from_text("a funeral service in a chapel")
    expected = set()
    for ref in scene.references:
        for occasion, belongs in OCCASION_EXPECTS.items():
            if occasion in ref or ref in occasion:
                expected |= belongs

    for c in picks(scene):
        vocab = set(c.track.tags) | {g.lower() for g in c.track.genres}
        assert not (vocab & expected), (
            f"{c.track.title} belongs at this occasion ({vocab & expected})")


def test_it_disagrees_with_the_acoustic_strategy():
    """Three strategies that argue beat five that agree. If this one keeps
    proposing what genre_antipode already found, it is costing time and adding
    nothing."""
    scene = scene_from_text("a funeral service in a chapel")
    mine = {c.track.id for c in picks(scene)}
    theirs = {c.track.id for c in picks(scene, genre_antipode)}

    assert mine, "it proposed nothing at all"
    assert mine - theirs, "everything it found was already on the other list"


def test_a_specific_occasion_still_matches_a_general_one():
    """"diwali celebration" has to reach the "celebration" rules -- naming the
    specific event is what makes the read good, and it must not be punished
    for it by falling through to nothing."""
    scene = scene_from_text("a celebration")
    scene.references = ["diwali celebration"]
    assert picks(scene), "a specific occasion matched no rule"


def test_different_occasions_produce_different_shortlists():
    funeral = scene_from_text("a funeral service in a chapel")
    gym = scene_from_text("a gym at 6am, someone training hard")
    assert {c.track.id for c in picks(funeral)} != {c.track.id for c in picks(gym)}


# ------------------------------------------------ the rule about identity --


@pytest.mark.parametrize("bad", [
    "south asian", "muslim wedding guests", "elderly men", "black people",
    "young women", "conservative crowd",
])
def test_identity_terms_are_stripped_from_references(bad):
    """AGENTS.md, first section: the system has no notion of anyone's race,
    sex, religion, politics or identity, and must never acquire one. The prompt
    says so, but a prompt is a request -- so it is enforced here as well.
    """
    assert _clean_references([bad]) == []


@pytest.mark.parametrize("ok", [
    "wedding", "funeral", "diwali celebration", "boardroom", "rave",
    "graduation ceremony", "children's party",
])
def test_occasions_survive_the_filter(ok):
    """The filter must not be so blunt it removes the feature. An occasion is
    the joke; who attends it is not."""
    assert _clean_references([ok]) == [ok]


def test_the_filter_keeps_the_good_and_drops_the_bad_together():
    assert _clean_references(["wedding", "south asian", "outdoor"]) == \
        ["wedding", "outdoor"]


def test_junk_from_the_model_does_not_crash_the_read():
    assert _clean_references(None) == []
    assert _clean_references("not a list") == []
    assert _clean_references([None, 3, "", "  ", "wedding"]) == ["wedding"]


def test_references_are_deduplicated_and_bounded():
    out = _clean_references(["party"] * 4 + [f"thing {i}" for i in range(10)])
    assert out.count("party") == 1
    assert len(out) <= 6, "an unbounded list ends up in every prompt downstream"


# ------------------------------------------------------- the field itself --


def test_a_typed_scene_carries_its_occasion():
    """The stage button and the scripts go through scene_from_text, so if it
    doesn't populate references this strategy silently never fires there."""
    scene = scene_from_text("a funeral service")
    assert scene.references, "no occasion on a typed scene"
    assert "funeral" in scene.references


def test_the_mock_perceiver_carries_occasions_too():
    """A teammate with no API key must still exercise this path."""
    from badspotify.perceive.audio_features import AudioFeatures
    from badspotify.perceive.scene import MockPerceiver

    reads = [MockPerceiver().read(None, AudioFeatures(), {"index": i})
             for i in range(0, 15, 3)]
    assert all(r.references for r in reads), "mock scenes have no occasion"
