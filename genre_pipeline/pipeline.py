"""
Pipeline (v2): audio/video moment -> closest genre -> opposite genre.

Step 1: extract the 5-parameter moment description (mood/valence-arousal,
        speed, chaos, colour_warmth, instrument/sound tags) -- see
        sentiment.py (text path, MVP fallback) and av_extraction.py
        (real audio/video path).
Step 2: build a Genre-shaped moment object so the SAME combined_distance
        function works for both "moment vs genre" and "genre vs genre"
        comparisons -- no separate code path needed.
Step 3: nearest_genre -- argmin combined_distance over all genres.
Step 4: opposite_genre -- argmax of the SAME combined_distance, from the
        matched genre. This is "negate the metric": same function,
        flipped optimization direction. No vector-flipping step.
"""

import numpy as np
from genre_taxonomy import GENRES, Genre, VALENCE_EXTREME_20
from distance import combined_distance, MATCH_AXIS_WEIGHTS, OPPOSITE_AXIS_WEIGHTS, MATCH_TERM_WEIGHTS, OPPOSITE_TERM_WEIGHTS


def build_moment(valence, arousal, speed, chaos, colour_warmth, instruments=frozenset()) -> Genre:
    """Wrap a raw moment description in the same Genre shape so distance
    functions don't need a separate code path for 'moment' vs 'genre'."""
    return Genre(
        name="__moment__", code="moment",
        valence=valence, energy=arousal, speed=speed, chaos=chaos,
        colour_warmth=colour_warmth, instruments=frozenset(instruments),
    )


def nearest_genre(moment: Genre, genres=GENRES) -> Genre:
    return min(genres, key=lambda g: combined_distance(moment, g, axis_weights=MATCH_AXIS_WEIGHTS, **MATCH_TERM_WEIGHTS))


def opposite_genre(matched: Genre, genres=VALENCE_EXTREME_20) -> Genre:
    """
    Argmax of the same distance function, restricted to the curated
    valence-extreme-20 pool (see genre_taxonomy.py) rather than the full
    genre set. This guarantees the result is always a genre that's ALREADY
    known-extreme on valence, rather than trusting argmax over all 42 to
    land somewhere sensible -- and the pool is small enough to have been
    hand-reviewed.
    """
    candidates = [g for g in genres if g.name != matched.name]
    return max(candidates, key=lambda g: combined_distance(matched, g, axis_weights=OPPOSITE_AXIS_WEIGHTS, **OPPOSITE_TERM_WEIGHTS))


def run(valence, arousal, speed, chaos, colour_warmth, instruments=frozenset(),
        verbose=True, **weights):
    moment = build_moment(valence, arousal, speed, chaos, colour_warmth, instruments)

    matched = nearest_genre(moment, **weights)
    worst_choice = opposite_genre(matched, **weights)

    if verbose:
        print(f"\nMoment: valence={valence:.2f} arousal={arousal:.2f} speed={speed:.2f} "
              f"chaos={chaos:.2f} colour_warmth={colour_warmth:.2f} instruments={set(instruments) or '{}'}")
        print(f"  nearest genre : {matched.name}  ({matched.code})")
        print(f"  QUEUE THIS    : {worst_choice.name}  ({worst_choice.code})")

    return {"matched": matched, "worst_choice": worst_choice}


if __name__ == "__main__":
    # Funeral: sad, slow, calm, cool colours, organ/choir
    run(valence=0.05, arousal=0.15, speed=0.10, chaos=0.10, colour_warmth=0.10,
        instruments=frozenset({"organ", "choir"}))

    # Wild birthday party: happy, fast, chaotic, warm colours, synths
    run(valence=0.85, arousal=0.80, speed=0.75, chaos=0.55, colour_warmth=0.85,
        instruments=frozenset({"synthesizer", "vocals"}))

    # Wedding reception: happy, moderate energy, orderly, warm
    run(valence=0.90, arousal=0.65, speed=0.55, chaos=0.20, colour_warmth=0.80,
        instruments=frozenset({"synthesizer", "vocals", "drum_kit"}))
