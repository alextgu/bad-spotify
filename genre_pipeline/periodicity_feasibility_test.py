"""
Periodicity ("sin/cos-ness") of a rhythm -- literal implementation of
"a steady beat looks like a clean sine wave, a chaotic one doesn't."

Method: take the onset strength envelope (a 1D signal over time showing
how much percussive/note-onset energy exists at each moment), then FFT
IT (an FFT of an FFT-like envelope). A perfectly steady beat produces an
onset envelope that's itself periodic -- literally close to a sine wave
at the beat frequency -- so its own spectrum has one sharp dominant peak.
An irregular rhythm's onset envelope has no clean periodicity, so its
spectrum is spread across many frequencies.

We measure this as "spectral concentration": what fraction of the onset
envelope's spectral energy sits in its single strongest frequency bin.
High concentration = sinusoidal/regular = calm. Low concentration =
spread out = chaotic. This is a companion metric to onset-interval CV
from chaos_feasibility_test.py, not a replacement -- CV measures timing
irregularity directly, this measures how sinusoidal the overall pulse
is. Worth keeping both and seeing which correlates better with your
actual genre examples once you're testing on real audio.
"""

import numpy as np
import librosa

import sys
sys.path.insert(0, "/home/claude/worst_dj")
from chaos_feasibility_test import (
    SR, make_pure_tone, make_white_noise, make_steady_clicks, make_irregular_clicks
)


def spectral_concentration_of_rhythm(y: np.ndarray, sr: int = SR) -> float:
    onset_env = librosa.onset.onset_strength(y=y, sr=sr)
    if onset_env.std() < 1e-6:
        return float("nan")  # no rhythmic content to speak of

    spectrum = np.abs(np.fft.rfft(onset_env - onset_env.mean()))
    total_energy = spectrum.sum()
    if total_energy < 1e-9:
        return float("nan")

    peak_energy = spectrum.max()
    return float(peak_energy / total_energy)  # 1.0 = perfectly sinusoidal, near 0 = flat/noisy


if __name__ == "__main__":
    signals = {
        "steady_clicks_120bpm (expect: HIGH concentration, sine-like)": make_steady_clicks(),
        "irregular_clicks (expect: LOW concentration, spread out)":     make_irregular_clicks(),
        "white_noise (expect: LOW, no periodicity)":                    make_white_noise(),
    }

    print(f"{'signal':60s} {'spectral_concentration':>24s}")
    for name, y in signals.items():
        c = spectral_concentration_of_rhythm(y)
        c_str = f"{c:.3f}" if not np.isnan(c) else "n/a"
        print(f"{name:60s} {c_str:>24s}")
