"""Local audio features. Cheap, fast, no network.

These feed the scene read as hard numbers so the model isn't guessing about
tempo and density from a still image. Degrades to zeros if librosa is absent.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict

import numpy as np


@dataclass
class AudioFeatures:
    rms: float = 0.0
    peak: float = 0.0
    tempo_bpm: float = 0.0
    onset_rate: float = 0.0          # onsets per second -> "speed"
    spectral_centroid: float = 0.0   # -> "brightness"
    spectral_flatness: float = 0.0   # -> noisy vs tonal
    pulse_regularity: float = 0.0    # -> steady vs irregular ("consistent" in the notes)
    voiced_ratio: float = 0.0        # rough proxy for people talking

    def as_dict(self) -> dict:
        return {k: round(float(v), 4) for k, v in asdict(self).items()}

    def summary(self) -> str:
        if self.rms < 0.005:
            loud = "near-silent"
        elif self.rms < 0.05:
            loud = "quiet"
        elif self.rms < 0.15:
            loud = "moderate"
        else:
            loud = "loud"
        pulse = "steady pulse" if self.pulse_regularity > 0.6 else (
            "irregular" if self.pulse_regularity > 0 else "no clear pulse")
        return f"{loud}, ~{self.onset_rate:.1f} events/s, {pulse}"


def _tempo_bpm(librosa, onset_env, sr: int) -> float:
    for owner, name in (
        (getattr(librosa, "feature", None), "tempo"),
        (getattr(getattr(librosa, "feature", None), "rhythm", None), "tempo"),
        (getattr(librosa, "beat", None), "tempo"),
    ):
        try:
            fn = getattr(owner, name)
        except Exception:
            continue
        if fn is None:
            continue
        tempo = np.atleast_1d(fn(onset_envelope=onset_env, sr=sr))
        return float(tempo[0]) if tempo.size else 0.0
    raise AttributeError("no tempo estimator in this librosa version")


def extract(audio: np.ndarray | None, sr: int = 16000) -> AudioFeatures:
    if audio is None or getattr(audio, "size", 0) == 0:
        return AudioFeatures()

    x = np.asarray(audio, dtype=np.float32)
    feats = AudioFeatures(
        rms=float(np.sqrt(np.mean(x**2))),
        peak=float(np.max(np.abs(x))) if x.size else 0.0,
    )

    try:
        import librosa
    except Exception:
        return feats

    try:
        onset_env = librosa.onset.onset_strength(y=x, sr=sr)
        onsets = librosa.onset.onset_detect(onset_envelope=onset_env, sr=sr)
        duration = max(len(x) / sr, 1e-6)
        feats.onset_rate = len(onsets) / duration

        # librosa moved this twice: beat.tempo (<=0.9) -> feature.rhythm.tempo
        # (0.10) -> feature.tempo (1.0). Try newest first, and keep going if
        # none of them exist -- a missing BPM shouldn't cost us the other features.
        try:
            feats.tempo_bpm = _tempo_bpm(librosa, onset_env, sr)
        except Exception as e:
            print(f"[audio] tempo unavailable: {e}")

        feats.spectral_centroid = float(np.mean(librosa.feature.spectral_centroid(y=x, sr=sr)))
        feats.spectral_flatness = float(np.mean(librosa.feature.spectral_flatness(y=x)))

        # Regularity of inter-onset intervals: low variance == steady 4/4-ish.
        if len(onsets) > 3:
            times = librosa.frames_to_time(onsets, sr=sr)
            iois = np.diff(times)
            if len(iois) > 1 and np.mean(iois) > 0:
                cv = float(np.std(iois) / np.mean(iois))
                feats.pulse_regularity = float(max(0.0, 1.0 - min(cv, 1.0)))
    except Exception as e:  # never let feature extraction kill the loop
        print(f"[audio] feature extraction degraded: {e}")

    return feats


def to_vibe_hints(f: AudioFeatures) -> dict:
    """Map raw features into the 0..1 vibe space as *hints* for the model."""
    def clamp(v: float) -> float:
        return max(0.0, min(1.0, v))

    return {
        "arousal_hint": clamp(f.onset_rate / 8.0 * 0.6 + min(f.rms / 0.2, 1.0) * 0.4),
        "density_hint": clamp(min(f.rms / 0.25, 1.0) * 0.7 + f.spectral_flatness * 0.3),
        "brightness_hint": clamp(f.spectral_centroid / 4000.0),
        "steadiness_hint": clamp(f.pulse_regularity),
    }
