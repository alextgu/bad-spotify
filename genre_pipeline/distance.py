"""
Distance metrics over genres.

p_adic_distance: structural distance from the taxonomy tree.
    Two genres sharing more leading path segments are "closer" in
    ancestry, independent of their acoustic feature values. Distance
    shrinks as shared-prefix depth grows -- classic p-adic behavior,
    implemented directly on dot-separated path strings rather than
    literal base-p digit expansions (a code IS a digit string here,
    one "digit" per taxonomy level).

feature_distance: Euclidean or Mahalanobis distance in (valence, energy)
    space -- how far apart two genres sound, ignoring lineage.

combined_distance: alpha * p_adic + beta * feature, so "opposite" can
    weigh structural unrelatedness and acoustic unrelatedness separately.
"""

import numpy as np


def p_adic_distance(code_a: str, code_b: str, p: float = 2.0) -> float:
    """
    Distance shrinks with shared prefix depth. Formally: d = p^(-k),
    where k = number of shared leading path segments. Two genres with
    the same immediate parent (k = depth-1) are very close; two genres
    sharing only the root or nothing (k = 0) are maximally far (d = 1).
    Identical codes are a special case, returning exactly 0 -- d(x,x)=0
    is a basic distance-metric axiom that p^(-k) alone can't satisfy for
    any finite k, since it only approaches 0 as depth grows.
    """
    if code_a == code_b:
        return 0.0

    segs_a = code_a.split(".")
    segs_b = code_b.split(".")

    shared = 0
    for a, b in zip(segs_a, segs_b):
        if a == b:
            shared += 1
        else:
            break

    return p ** (-shared)


def weighted_euclidean_distance(vec_a: np.ndarray, vec_b: np.ndarray, axis_weights: np.ndarray) -> float:
    diff = vec_a - vec_b
    return float(np.sqrt(np.sum(axis_weights * diff ** 2)))


def mahalanobis_distance(vec_a: np.ndarray, vec_b: np.ndarray, cov_inv: np.ndarray) -> float:
    diff = vec_a - vec_b
    return float(np.sqrt(diff.T @ cov_inv @ diff))


def jaccard_distance(set_a: frozenset, set_b: frozenset) -> float:
    """
    1 - Jaccard similarity. 0 = identical sets, 1 = no overlap at all.
    Both-empty is treated as maximally different (1.0) -- "we don't know
    this genre's instruments" shouldn't score as "identical instrumentation"
    just because both sets happen to be empty defaults.
    """
    if not set_a and not set_b:
        return 1.0
    intersection = len(set_a & set_b)
    union = len(set_a | set_b)
    return 1.0 - (intersection / union)


# Two separate presets, because "find the closest genre" and "find the
# opposite genre" want different things from the same feature space:
#   - MATCHING wants a holistic, balanced similarity -- instrument/timbre
#     cues (organ+choir -> classical) should meaningfully influence which
#     genre we think we're hearing.
#   - OPPOSITE wants mood to dominate almost totally -- the joke is "sad
#     event, happy song," and letting chaos/speed/instruments compete with
#     valence on equal footing produces "merely extreme" genres (breakcore)
#     instead of "emotionally opposite" ones (carnival_ska, pop).
# One universal weight set can't satisfy both correctly at once -- this
# isn't a tuning failure, it's two different questions.
# Two separate presets, because "find the closest genre" and "find the
# opposite genre" want different things from the same feature space:
#   - MATCHING wants a holistic, balanced similarity across all 4 axes.
#   - OPPOSITE wants valence to dominate almost totally -- energy/speed/
#     chaos are correlated with each other for most genres (fast + chaotic
#     + high-energy tend to co-occur), so weighting them up as well doesn't
#     isolate mood, it just rewards "how extreme is this genre overall,"
#     and extreme-but-not-actually-happy genres win over genuinely happy
#     ones. Valence needs to carry the "opposite" argument mostly alone.
# Axes: [valence, energy, speed, chaos] -- colour_warmth and instruments
# are excluded from distance entirely per current scope (kept in the Genre
# schema, just not used here).
MATCH_AXIS_WEIGHTS = np.array([2.5, 2.0, 0.5, 0.5])
OPPOSITE_AXIS_WEIGHTS = np.array([5.0, 1.0, 0.2, 0.2])
DEFAULT_AXIS_WEIGHTS = MATCH_AXIS_WEIGHTS

MATCH_TERM_WEIGHTS = dict(weight_taxonomy=0.2, weight_continuous=0.8)
OPPOSITE_TERM_WEIGHTS = dict(weight_taxonomy=0.05, weight_continuous=0.95)


def combined_distance(
    genre_a,
    genre_b,
    weight_taxonomy: float = 0.2,
    weight_continuous: float = 0.8,
    axis_weights: np.ndarray = None,
    p: float = 2.0,
) -> float:
    """
    Weighted sum of:
      - taxonomy (p-adic) distance          -- structural/genealogical
      - continuous feature distance         -- valence, energy, speed, chaos
        (per-axis weighted -- see MATCH/OPPOSITE_AXIS_WEIGHTS)
    Instruments (categorical) and colour_warmth are excluded from distance
    entirely per current scope -- still present on the Genre dataclass,
    just unused here. Weights should sum to ~1.0 but aren't enforced.

    This is the "find closest genre" metric AND the "negate to find
    opposite" metric -- same function, just argmin vs argmax with
    different weight presets (see pipeline.py). No vector-flip step.
    """
    if axis_weights is None:
        axis_weights = DEFAULT_AXIS_WEIGHTS

    struct = p_adic_distance(genre_a.code, genre_b.code, p=p)

    feat = weighted_euclidean_distance(genre_a.continuous_vector, genre_b.continuous_vector, axis_weights)
    feat_normalized = feat / np.sqrt(axis_weights.sum())

    return weight_taxonomy * struct + weight_continuous * feat_normalized
