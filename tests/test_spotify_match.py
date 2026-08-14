"""Matching tests. No network -- these run on realistic search payloads.

Every case here is a real way Spotify search has embarrassed someone.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from badspotify.players.spotify_match import (  #noqa: E402
    best_match, normalise, score_result, search_queries, token_overlap,
)


def item(name, artists, uri="spotify:track:x", ms=200000):
    return {"name": name, "uri": uri, "duration_ms": ms,
            "artists": [{"name": a} for a in artists]}


def test_normalise_strips_remaster_decoration():
    assert normalise("Hurt - 2002 Remaster") == "hurt"
    assert normalise("Africa (Remastered)") == "africa"
    assert normalise("Creep (feat. Someone)") == "creep"


def test_exact_match_wins():
    m = score_result(item("Hurt", ["Johnny Cash"]), "Hurt", "Johnny Cash")
    assert m.ok and m.score > 0.9


def test_karaoke_is_rejected():
    m = score_result(
        item("Hurt (Karaoke Version)", ["Karaoke Kings"]), "Hurt", "Johnny Cash")
    assert not m.ok


def test_tribute_band_is_rejected():
    m = score_result(
        item("Hurt (Made Famous by Johnny Cash)", ["The Tribute Players"]),
        "Hurt", "Johnny Cash")
    assert not m.ok


def test_wrong_artist_same_title_is_rejected():
    """'Hurt' by Nine Inch Nails is a real song and the wrong answer here."""
    m = score_result(item("Hurt", ["Nine Inch Nails"]), "Hurt", "Johnny Cash")
    assert not m.ok, "matched a different artist's song with the same title"


def test_live_version_loses_to_studio():
    items = [
        item("Thunderstruck - Live", ["AC/DC"], uri="spotify:track:live"),
        item("Thunderstruck", ["AC/DC"], uri="spotify:track:studio"),
    ]
    winner, _ = best_match(items, "Thunderstruck", "AC/DC")
    assert winner is not None and winner.uri == "spotify:track:studio"


def test_remaster_still_matches():
    winner, _ = best_match([item("Hurt - 2002 Remaster", ["Johnny Cash"])],
                           "Hurt", "Johnny Cash")
    assert winner is not None


def test_various_artists_does_not_block_a_match():
    """Our corpus says 'Various' when we never knew the artist."""
    winner, _ = best_match([item("Thunderdome Anthem", ["Some Hardcore Act"])],
                           "Thunderdome Anthem", "Various")
    assert winner is not None


def test_classical_matches_on_any_credited_artist():
    """Composer and performer are both credited; either should carry it."""
    winner, _ = best_match(
        [item("Funeral March", ["Frederic Chopin", "Some Pianist"])],
        "Funeral March", "Frederic Chopin")
    assert winner is not None


def test_no_results_reports_why():
    winner, scored = best_match(
        [item("Completely Different Song", ["Someone Else"])], "Hurt", "Johnny Cash")
    assert winner is None
    assert scored and scored[0].rejected


def test_empty_results_is_safe():
    winner, scored = best_match([], "Hurt", "Johnny Cash")
    assert winner is None and scored == []


def test_query_ladder_goes_precise_to_loose():
    q = search_queries("Hurt", "Johnny Cash")
    assert q[0].startswith("track:")
    assert q[-1] == "Hurt"


def test_token_overlap_is_order_insensitive():
    assert token_overlap("Walking on Sunshine", "Sunshine Walking On") == 1.0
