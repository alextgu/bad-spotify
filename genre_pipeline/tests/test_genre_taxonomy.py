from genre_taxonomy import GENRES, GENRE_BY_NAME, VALENCE_EXTREME_20, CHAOS_EXTREME_20


def test_genres_load():
    assert len(GENRES) > 30, "expected the merged hand-anchored + everynoise set"


def test_no_duplicate_genre_names():
    names = [g.name for g in GENRES]
    assert len(names) == len(set(names)), "duplicate genre names found -- dedup logic may have regressed"


def test_all_continuous_values_in_unit_interval():
    for g in GENRES:
        for axis_name, value in [("valence", g.valence), ("energy", g.energy),
                                   ("speed", g.speed), ("chaos", g.chaos)]:
            assert 0.0 <= value <= 1.0, f"{g.name}.{axis_name} = {value} out of [0,1]"


def test_genre_by_name_matches_genres_list():
    assert len(GENRE_BY_NAME) == len(GENRES)
    for g in GENRES:
        assert GENRE_BY_NAME[g.name] is g or GENRE_BY_NAME[g.name] == g


def test_valence_extreme_20_is_sorted_by_extremity():
    extremities = [abs(g.valence - 0.5) for g in VALENCE_EXTREME_20]
    assert extremities == sorted(extremities, reverse=True), "not sorted descending by |valence - 0.5|"
    assert len(VALENCE_EXTREME_20) == 20


def test_chaos_extreme_20_is_sorted_by_extremity():
    extremities = [abs(g.chaos - 0.5) for g in CHAOS_EXTREME_20]
    assert extremities == sorted(extremities, reverse=True), "not sorted descending by |chaos - 0.5|"
    assert len(CHAOS_EXTREME_20) == 20


def test_hand_anchored_genres_present():
    """Sanity check that the core hand-anchored set didn't get lost in a merge/dedup pass."""
    expected = {"rock", "pop", "jazz", "classical", "metal", "breakcore", "elevator_music"}
    actual = {g.name for g in GENRES}
    assert expected.issubset(actual)
