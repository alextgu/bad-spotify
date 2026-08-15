from genre_taxonomy import GENRES, VALENCE_EXTREME_20
from pipeline import build_moment, nearest_genre, opposite_genre


def test_nearest_genre_returns_a_real_genre():
    moment = build_moment(valence=0.5, arousal=0.5, speed=0.5, chaos=0.5, colour_warmth=0.5)
    result = nearest_genre(moment)
    assert result in GENRES


def test_opposite_genre_is_restricted_to_valence_extreme_pool():
    moment = build_moment(valence=0.5, arousal=0.5, speed=0.5, chaos=0.5, colour_warmth=0.5)
    matched = nearest_genre(moment)
    result = opposite_genre(matched)
    assert result in VALENCE_EXTREME_20


def test_opposite_genre_is_never_the_match_itself():
    moment = build_moment(valence=0.05, arousal=0.15, speed=0.10, chaos=0.10, colour_warmth=0.10)
    matched = nearest_genre(moment)
    result = opposite_genre(matched)
    assert result.name != matched.name


def test_breakcore_scenario_regression():
    """A busy, fast, chaotic moment should match breakcore, not a rock/metal
    genre that's merely 'extreme' overall -- this was the specific gap we
    found by auditing corner coverage. If this breaks, it's very likely an
    axis-weight or genre-data regression, not a fluke."""
    moment = build_moment(valence=0.35, arousal=0.90, speed=0.95, chaos=0.90, colour_warmth=0.30)
    result = nearest_genre(moment)
    assert result.name == "breakcore"


def test_opposite_of_happy_moment_is_meaningfully_sadder():
    """This is the general form of the 'funeral's opposite should be happy'
    fix -- opposite-finding should move valence substantially in the
    opposite direction, not just find something 'extreme' on unrelated axes."""
    happy_moment = build_moment(valence=0.85, arousal=0.70, speed=0.5, chaos=0.3, colour_warmth=0.8)
    matched = nearest_genre(happy_moment)
    result = opposite_genre(matched)
    assert result.valence < matched.valence - 0.3, (
        f"opposite ({result.name}, valence={result.valence}) isn't meaningfully "
        f"sadder than matched ({matched.name}, valence={matched.valence})"
    )


def test_opposite_of_sad_moment_is_meaningfully_happier():
    sad_moment = build_moment(valence=0.10, arousal=0.20, speed=0.15, chaos=0.15, colour_warmth=0.15)
    matched = nearest_genre(sad_moment)
    result = opposite_genre(matched)
    assert result.valence > matched.valence + 0.3, (
        f"opposite ({result.name}, valence={result.valence}) isn't meaningfully "
        f"happier than matched ({matched.name}, valence={matched.valence})"
    )
