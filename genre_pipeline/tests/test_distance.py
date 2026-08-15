import numpy as np
from distance import (
    p_adic_distance, weighted_euclidean_distance, combined_distance,
    MATCH_AXIS_WEIGHTS, OPPOSITE_AXIS_WEIGHTS, MATCH_TERM_WEIGHTS, OPPOSITE_TERM_WEIGHTS,
)
from genre_taxonomy import Genre


def test_p_adic_identical_codes_is_minimal():
    assert p_adic_distance("rock.punk", "rock.punk") == p_adic_distance("rock.punk", "rock.punk")
    # identical codes share ALL segments -> smallest possible distance
    d_identical = p_adic_distance("rock.punk.pop_punk", "rock.punk.pop_punk")
    d_different = p_adic_distance("rock.punk.pop_punk", "jazz.swing")
    assert d_identical < d_different


def test_p_adic_shared_prefix_closer_than_no_shared_prefix():
    d_shared = p_adic_distance("rock.punk.pop_punk", "rock.punk.hardcore")  # shares "rock.punk"
    d_unshared = p_adic_distance("rock.punk.pop_punk", "jazz.swing")         # shares nothing
    assert d_shared < d_unshared


def test_weighted_euclidean_zero_for_identical_vectors():
    v = np.array([0.3, 0.7, 0.5, 0.2])
    w = np.array([1.0, 1.0, 1.0, 1.0])
    assert weighted_euclidean_distance(v, v, w) == 0.0


def test_weighted_euclidean_respects_weights():
    a = np.array([0.0, 0.0])
    b = np.array([1.0, 0.0])  # differs only on axis 0
    c = np.array([0.0, 1.0])  # differs only on axis 1
    w_favor_axis0 = np.array([5.0, 1.0])
    # b differs on the heavily-weighted axis -> should be "farther" than c
    assert weighted_euclidean_distance(a, b, w_favor_axis0) > weighted_euclidean_distance(a, c, w_favor_axis0)


def test_combined_distance_zero_for_self():
    g = Genre(name="x", code="rock.indie", valence=0.5, energy=0.5, speed=0.5, chaos=0.5)
    d = combined_distance(g, g, axis_weights=MATCH_AXIS_WEIGHTS, **MATCH_TERM_WEIGHTS)
    assert d == 0.0


def test_combined_distance_symmetric():
    a = Genre(name="a", code="rock.indie", valence=0.2, energy=0.8, speed=0.5, chaos=0.6)
    b = Genre(name="b", code="jazz.swing", valence=0.9, energy=0.3, speed=0.2, chaos=0.4)
    d_ab = combined_distance(a, b, axis_weights=MATCH_AXIS_WEIGHTS, **MATCH_TERM_WEIGHTS)
    d_ba = combined_distance(b, a, axis_weights=MATCH_AXIS_WEIGHTS, **MATCH_TERM_WEIGHTS)
    assert abs(d_ab - d_ba) < 1e-9


def test_opposite_weights_favor_valence_over_match_weights():
    # This is the core fix from earlier debugging: OPPOSITE_AXIS_WEIGHTS
    # should weight valence (index 0) much more heavily, relative to the
    # other axes, than MATCH_AXIS_WEIGHTS does.
    match_valence_share = MATCH_AXIS_WEIGHTS[0] / MATCH_AXIS_WEIGHTS.sum()
    opposite_valence_share = OPPOSITE_AXIS_WEIGHTS[0] / OPPOSITE_AXIS_WEIGHTS.sum()
    assert opposite_valence_share > match_valence_share
