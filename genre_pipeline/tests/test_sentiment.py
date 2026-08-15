import numpy as np
from sentiment import _fallback_blurb_to_valence_arousal


def test_fallback_returns_valid_range():
    v, a = _fallback_blurb_to_valence_arousal("a happy celebration")
    assert 0.0 <= v <= 1.0
    assert 0.0 <= a <= 1.0


def test_fallback_happy_words_score_higher_valence_than_sad_words():
    happy_v, _ = _fallback_blurb_to_valence_arousal("happy party celebration")
    sad_v, _ = _fallback_blurb_to_valence_arousal("sad funeral grief")
    assert happy_v > sad_v


def test_fallback_no_keyword_match_returns_neutral_default():
    v, a = _fallback_blurb_to_valence_arousal("xyzzy plugh qwerty")
    assert v == 0.5 and a == 0.4
