"""Local audio features. Cheap, fast, no network.

These feed the scene read as hard numbers so the model isn't guessing about
tempo and density from a still image. Degrades to zeros if librosa is absent.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict

import numpy as np
from ..log import notice  # stdout is reserved for data


@dataclass
class AudioFeatures:
    rms: float = 0.0
    peak: float = 0.0
    tempo_bpm: float = 0.0
    onset_rate: float = 0.0          #Detected sound events per second
    spectral_centroid: float = 0.0   #Perceived audio brightness
    spectral_flatness: float = 0.0   #Amount of noise in the audio
    pulse_regularity: float = 0.0    #Consistency of the beat
    voiced_ratio: float = 0.0        #Estimated amount of speech

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

    onsets: np.ndarray = np.asarray([])

    # Each feature is guarded on its own. They used to share one try block, and
    # when `librosa.beat.tempo` was removed in 1.0 the exception took centroid,
    # flatness and pulse down with it -- all four read zero for days and nothing
    # said so. One dead feature must not silence the others.
    def _guard(name: str, fn):
        try:
            return fn()
        except Exception as e:  #Keeps the main loop running after analysis errors
            notice(f"[audio] {name} degraded: {e}")
            return None

    def _onsets():
        onset_env = librosa.onset.onset_strength(y=x, sr=sr)
        return onset_env, librosa.onset.onset_detect(
            onset_envelope=onset_env, sr=sr)

    got = _guard("onsets", _onsets)
    if got is not None:
        onset_env, onsets = got
        duration = max(len(x) / sr, 1e-6)
        feats.onset_rate = len(onsets) / duration

        # librosa 1.0 moved tempo out of `beat` and re-exports it on `feature`.
        # Don't reach for `librosa.feature.rhythm` -- the submodule isn't bound
        # as an attribute until something imports it, so getattr misses it.
        tempo_fn = (getattr(librosa.feature, "tempo", None)
                    or getattr(librosa.beat, "tempo", None))
        if tempo_fn is None:
            notice("[audio] tempo unavailable in librosa "
                   f"{getattr(librosa, '__version__', '?')}")
        else:
            tempo = _guard("tempo", lambda: tempo_fn(
                onset_envelope=onset_env, sr=sr))
            if tempo is not None:
                feats.tempo_bpm = float(tempo[0]) if len(tempo) else 0.0

    centroid = _guard("centroid", lambda: float(
        np.mean(librosa.feature.spectral_centroid(y=x, sr=sr))))
    if centroid is not None:
        feats.spectral_centroid = centroid

    flatness = _guard("flatness", lambda: float(
        np.mean(librosa.feature.spectral_flatness(y=x))))
    if flatness is not None:
        feats.spectral_flatness = flatness

    #Measures how consistent the beat timing is
    if len(onsets) > 3:
        def _pulse():
            times = librosa.frames_to_time(onsets, sr=sr)
            iois = np.diff(times)
            if len(iois) > 1 and np.mean(iois) > 0:
                cv = float(np.std(iois) / np.mean(iois))
                return float(max(0.0, 1.0 - min(cv, 1.0)))
            return None

        pulse = _guard("pulse", _pulse)
        if pulse is not None:
            feats.pulse_regularity = pulse

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
