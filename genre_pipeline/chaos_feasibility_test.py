"""
Feasibility test: can elementary DSP distinguish "chaotic" from "calm" audio?

Two candidate metrics, both classic and cheap:

1. Spectral entropy -- Shannon entropy of the normalized power spectrum.
   Energy concentrated in few frequencies (a pure tone, a clean chord)
   = low entropy. Energy spread across all frequencies (noise) = high
   entropy. This captures TIMBRAL chaos -- how "noisy" the sound is,
   independent of rhythm.

2. Onset-interval irregularity -- detect note/percussion onsets, then
   take the coefficient of variation (std/mean) of the time gaps between
   them. A steady beat = all gaps equal = CV near 0. A free-jazz-style
   irregular rhythm = gaps all over the place = high CV. This captures
   RHYTHMIC chaos -- closer to your original "steady vs unsteady" framing.

These are DIFFERENT axes -- white noise is high spectral-entropy but has
no onsets at all (rhythmically undefined), while a chaotic drum fill is
rhythmically irregular but each hit is spectrally clean. Worth keeping
both rather than collapsing to one "chaos" number.

Validation strategy: run both metrics on four synthetic signals where we
know the ground truth by construction, before ever touching real audio.
"""

import numpy as np
import librosa


SR = 22050  # sample rate
DUR = 5.0   # seconds


def spectral_entropy(y: np.ndarray, sr: int = SR) -> float:
    S = np.abs(librosa.stft(y)) ** 2          # power spectrogram
    S_norm = S / (S.sum(axis=0, keepdims=True) + 1e-12)  # normalize each frame to a distribution
    frame_entropy = -np.sum(S_norm * np.log2(S_norm + 1e-12), axis=0)
    max_entropy = np.log2(S.shape[0])          # entropy of a uniform distribution over freq bins
    return float(np.mean(frame_entropy) / max_entropy)  # normalize to [0, 1]


def onset_irregularity(y: np.ndarray, sr: int = SR) -> float:
    onset_frames = librosa.onset.onset_detect(y=y, sr=sr, units="time")
    if len(onset_frames) < 3:
        return float("nan")  # not enough onsets to say anything about regularity
    intervals = np.diff(onset_frames)
    cv = np.std(intervals) / (np.mean(intervals) + 1e-12)
    return float(cv)


# --- Synthetic test signals ---

def make_pure_tone(freq=440.0, dur=DUR, sr=SR):
    t = np.linspace(0, dur, int(sr * dur), endpoint=False)
    return 0.5 * np.sin(2 * np.pi * freq * t)


def make_white_noise(dur=DUR, sr=SR, seed=0):
    rng = np.random.default_rng(seed)
    return 0.3 * rng.standard_normal(int(sr * dur))


def make_steady_clicks(bpm=120, dur=DUR, sr=SR):
    interval = 60.0 / bpm
    y = np.zeros(int(sr * dur))
    click = np.exp(-np.linspace(0, 30, int(sr * 0.02)))  # short decaying click
    t = 0.0
    while t < dur:
        idx = int(t * sr)
        end = min(idx + len(click), len(y))
        y[idx:end] += click[: end - idx]
        t += interval
    return y


def make_irregular_clicks(n_clicks=15, dur=DUR, sr=SR, seed=1):
    rng = np.random.default_rng(seed)
    times = np.sort(rng.uniform(0, dur, n_clicks))
    y = np.zeros(int(sr * dur))
    click = np.exp(-np.linspace(0, 30, int(sr * 0.02)))
    for t in times:
        idx = int(t * sr)
        end = min(idx + len(click), len(y))
        y[idx:end] += click[: end - idx]
    return y


if __name__ == "__main__":
    signals = {
        "pure_tone (expect: low spectral entropy)":        make_pure_tone(),
        "white_noise (expect: high spectral entropy)":     make_white_noise(),
        "steady_clicks_120bpm (expect: low onset CV)":      make_steady_clicks(),
        "irregular_clicks (expect: high onset CV)":         make_irregular_clicks(),
    }

    print(f"{'signal':45s} {'spectral_entropy':>18s} {'onset_CV':>12s}")
    for name, y in signals.items():
        se = spectral_entropy(y)
        cv = onset_irregularity(y)
        cv_str = f"{cv:.3f}" if not np.isnan(cv) else "n/a (few onsets)"
        print(f"{name:45s} {se:18.3f} {cv_str:>12s}")
