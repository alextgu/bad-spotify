"""Songs from outside the 47.

The hand-curated corpus is small enough that a long session repeats itself --
measured: 8 distinct winners across 24 scenes, one track taking a third of
them. This path asks a model to NAME well-known songs for the moment.

Two findings shaped the design, both the hard way:

**Searching by genre and ranking by fame doesn't work.** `genre:"ambient"`
returns deep catalogue, and Spotify stopped returning `popularity` to new apps
entirely -- verified 14 Aug 2026, the field is absent from the response, as are
artist followers, `recommendations` (404) and `related-artists` (403). There is
nothing left to rank fame by, so the model is asked for famous songs instead.

**Resolving every suggestion is how you lose a day.** The first version turned
all eight names into URIs here: fourteen Spotify searches for one scene, of
which the judge used one. That app hit its rate limit and was told to retry in
82,000 seconds. Candidates are now unresolved names, and the player resolves
the winner alone.

Nothing here touches the network.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from badspotify.music import discover                        # noqa: E402
from badspotify.music.corpus import Corpus                   # noqa: E402
from badspotify.music.strategies import catalogue_dive       # noqa: E402
from badspotify.music.vibe import build_antivibe             # noqa: E402
from badspotify.perceive.scene import scene_from_text        # noqa: E402

CORPUS = Corpus.load()


@pytest.fixture(autouse=True)
def isolated(monkeypatch, tmp_path):
    monkeypatch.setattr(discover, "_RESOLVED_PATH", tmp_path / "uris.json")
    monkeypatch.setattr(discover, "_resolved", None)
    monkeypatch.setattr(discover, "_blocked_until", 0.0)
    #The per-minute budget is module state, so without this each test spends
    #the previous test's allowance and the later ones silently get nothing.
    monkeypatch.setattr(discover, "_recent_calls", [])
    discover.clear_cache()
    yield
    discover.clear_cache()


@pytest.fixture
def offline(monkeypatch):
    """A fake model, and a Spotify client that explodes if anyone touches it."""
    calls = {"suggested": 0}

    def fake_suggest(scene, anti):
        calls["suggested"] += 1
        return "counter_register", "gravity punctured", [
            {"title": "Baby Shark", "artist": "Pinkfong",
             "why": "toddler earworm in a seat of power"},
            {"title": "Macarena", "artist": "Los del Rio",
             "why": "line dance at a solemn occasion"},
            {"title": "Baby Shark", "artist": "Pinkfong",
             "why": "named twice by the model"},
        ]

    def boom(*a, **kw):
        raise AssertionError(
            "discovery must not touch Spotify -- the player resolves the "
            "winner, and only the winner")

    monkeypatch.setattr(discover, "_suggest", fake_suggest)
    monkeypatch.setattr(discover, "_spotify", boom)
    return calls


def scene_and_anti(text="a funeral service in a chapel"):
    scene = scene_from_text(text)
    return scene, build_antivibe(scene)


# ------------------------------------------------------------- discovery --


def test_discovery_never_calls_spotify(offline):
    """The whole point of the rework. Fourteen searches per scene is what cost
    the first app a day; candidate generation must now cost zero."""
    scene, anti = scene_and_anti()
    got = discover.search(scene, anti)          # `_spotify` raises if touched
    assert got, "discovered nothing"


def test_named_songs_become_candidate_tracks(offline):
    scene, anti = scene_and_anti()
    got = discover.search(scene, anti)

    assert [t.title for t in got] == ["Baby Shark", "Macarena"]
    assert all(t.uri is None for t in got), (
        "a URI here means something resolved during candidate generation")
    assert all(t.why for t in got), "the clash line is most of the joke"


def test_the_same_song_named_twice_takes_one_slot(offline):
    scene, anti = scene_and_anti()
    titles = [t.title for t in discover.search(scene, anti)]
    assert titles.count("Baby Shark") == 1


def test_ids_are_stable_so_the_player_can_cache_against_them(offline):
    """The player stores resolutions under `track.id`. A id that changed
    between runs would re-resolve the same song forever."""
    scene, anti = scene_and_anti()
    first = [t.id for t in discover.search(scene, anti)]
    discover.clear_cache()
    assert [t.id for t in discover.search(scene, anti)] == first


def test_ids_cannot_collide_with_the_corpus(offline):
    """`played_ids` mixes both kinds, so a discovered track sharing an id with
    a corpus track would silently suppress the wrong one."""
    scene, anti = scene_and_anti()
    corpus_ids = {t.id for t in CORPUS.tracks}

    for t in discover.search(scene, anti):
        assert t.id.startswith("sp:")
        assert t.id not in corpus_ids


def test_the_same_scene_is_not_re_asked(offline):
    """Each ask is a model call, so a held scene must not pay on every tick."""
    scene, anti = scene_and_anti()
    discover.search(scene, anti)
    discover.search(scene, anti)
    assert offline["suggested"] == 1, "it asked twice for one unchanged scene"


def test_no_model_means_no_discovery_and_no_crash(monkeypatch):
    """Discovery is a bonus on top of a corpus that already works. A teammate
    with no keys loses the bonus and nothing else."""
    monkeypatch.setattr(discover, "_genai", lambda: None)
    scene, anti = scene_and_anti()
    assert discover.search(scene, anti) == []


def test_a_failing_model_is_swallowed(monkeypatch):
    """`_suggest` guards internally so a bad response costs the bonus, not the
    pipeline -- silence is this project's only real bug."""
    class Exploding:
        class models:
            @staticmethod
            def generate_content(**kw):
                raise RuntimeError("boom")

    monkeypatch.setattr(discover, "_genai", lambda: Exploding())
    scene, anti = scene_and_anti()
    assert discover.search(scene, anti) == []


# ------------------------------------------------ staying out of trouble --


def test_a_rate_limit_stands_everything_down():
    """Measured 14 Aug 2026: a development-mode app crossed Spotify's quota and
    was told to retry in 82,000 seconds -- almost a full day, no appeal. On the
    day that means no music, so once Spotify says stop, everything stops asking
    and the corpus carries the demo. That is what the 47 are for.
    """
    assert not discover.rate_limited()
    assert discover.note_rate_limit(RuntimeError(
        "Your application has reached a rate/request limit. "
        "Retry will occur after: 82058 s"))
    assert discover.rate_limited(), "it would have kept asking"


def test_an_unrelated_error_is_not_mistaken_for_a_rate_limit():
    assert not discover.note_rate_limit(RuntimeError("connection reset"))
    assert not discover.rate_limited()


def test_the_per_minute_budget_stops_a_runaway(monkeypatch):
    """Independent of what Spotify tolerates, and deliberately low: we should
    never be near their limit, and approaching ours means something upstream
    has gone wrong and should degrade to the corpus."""
    monkeypatch.setattr(discover, "MAX_SEARCHES_PER_MIN", 3)

    assert [discover.budget_ok() for _ in range(3)] == [True, True, True]
    assert discover.budget_ok() is False, "the budget did not stop anything"


# -------------------------------------------------------- as a strategy --


def test_the_strategy_returns_candidates(offline):
    scene, anti = scene_and_anti()
    cands = catalogue_dive(scene, anti, CORPUS, set(), 4)

    assert cands, "discovered nothing"
    assert all(c.strategy == "catalogue_dive" for c in cands)
    assert all(c.notes for c in cands), "no reason to show the audience"


def test_already_played_discoveries_are_excluded(offline):
    scene, anti = scene_and_anti()
    first = catalogue_dive(scene, anti, CORPUS, set(), 4)
    played = {first[0].track.id}
    again = catalogue_dive(scene, anti, CORPUS, played, 4)

    assert all(c.track.id not in played for c in again)


def test_it_ranks_in_the_order_the_model_gave(offline):
    """There is nothing left to rank on -- Spotify no longer exposes
    popularity -- so the model's own preference order is the signal."""
    scene, anti = scene_and_anti()
    cands = catalogue_dive(scene, anti, CORPUS, set(), 4)
    assert [c.track.title for c in cands] == ["Baby Shark", "Macarena"]
    assert cands[0].raw_distance > cands[1].raw_distance


def test_it_does_not_crowd_out_every_other_strategy(offline):
    """Pitched at 1.15 it won all 12 scenes in testing and the corpus
    strategies stopped mattering. Their disagreement is half of why the
    reasoning is worth showing, so it overlaps their range, not sits above."""
    from badspotify.music.strategies import genre_antipode

    scene, anti = scene_and_anti()
    best_corpus = max(c.raw_distance
                      for c in genre_antipode(scene, anti, CORPUS, set(), 4))
    best_found = max(c.raw_distance
                     for c in catalogue_dive(scene, anti, CORPUS, set(), 4))
    assert best_found < best_corpus * 1.35, (
        "discovery outranks the corpus by so much that nothing else can win")
