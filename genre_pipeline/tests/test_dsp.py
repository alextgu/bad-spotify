import numpy as np
from chaos_feasibility_test import (
    spectral_entropy, onset_irregularity,
    make_pure_tone, make_white_noise, make_steady_clicks, make_irregular_clicks,
)
from speed_feasibility_test import make_moving_square_video, avg_optical_flow_magnitude
from periodicity_feasibility_test import spectral_concentration_of_rhythm


def test_spectral_entropy_tone_lower_than_noise():
    assert spectral_entropy(make_pure_tone()) < spectral_entropy(make_white_noise())


def test_onset_cv_steady_lower_than_irregular():
    steady_cv = onset_irregularity(make_steady_clicks())
    irregular_cv = onset_irregularity(make_irregular_clicks())
    assert steady_cv < irregular_cv


def test_optical_flow_fast_greater_than_slow():
    slow = avg_optical_flow_magnitude(make_moving_square_video(pixels_per_frame=1.0))
    fast = avg_optical_flow_magnitude(make_moving_square_video(pixels_per_frame=12.0))
    assert fast > slow
    assert fast / slow > 5  # should be a clear separation, not a marginal one


def test_spectral_concentration_steady_higher_than_irregular():
    """Weaker separation than onset-CV (see periodicity_feasibility_test.py's
    own docstring) -- direction should still hold, but don't expect a huge gap."""
    steady = spectral_concentration_of_rhythm(make_steady_clicks())
    irregular = spectral_concentration_of_rhythm(make_irregular_clicks())
    assert steady > irregular
