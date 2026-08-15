"""
Blurb -> (valence, energy) via a pretrained HF emotion classifier.

Model: j-hartmann/emotion-english-distilroberta-base
Outputs a distribution over 7 emotions (anger, disgust, fear, joy,
neutral, sadness, surprise). We map each emotion to an approximate
(valence, arousal) point -- this mapping is the standard NRC-VAD-style
association, hand-anchored, not learned -- and take the probability-
weighted average across the full distribution rather than just the
top label, so a blurb that's 60% joy / 30% surprise doesn't collapse
to a single discrete emotion.
"""

from functools import lru_cache
import numpy as np

# Approximate (valence, arousal) anchor per emotion label, in [0, 1].
EMOTION_VAD = {
    "anger":    (0.15, 0.85),
    "disgust":  (0.10, 0.55),
    "fear":     (0.15, 0.80),
    "joy":      (0.90, 0.75),
    "neutral":  (0.50, 0.30),
    "sadness":  (0.10, 0.20),
    "surprise": (0.70, 0.80),
}


@lru_cache(maxsize=1)
def _get_classifier():
    from transformers import pipeline
    return pipeline(
        "text-classification",
        model="j-hartmann/emotion-english-distilroberta-base",
        top_k=None,  # return full distribution, not just argmax
    )


# --- Fallback ONLY used if the HF model can't be reached (e.g. no network
# access to huggingface.co). Real deployments should never hit this path --
# it exists purely so the pipeline is runnable/demoable offline. Delete once
# you've confirmed the HF model downloads fine in your actual environment.
_FALLBACK_LEXICON = {
    "happy": (0.9, 0.7), "joy": (0.9, 0.7), "celebration": (0.9, 0.75),
    "party": (0.85, 0.8), "wedding": (0.9, 0.7), "excited": (0.85, 0.85),
    "sad": (0.1, 0.2), "funeral": (0.05, 0.1), "grief": (0.05, 0.15),
    "crying": (0.1, 0.3), "somber": (0.15, 0.15), "mourning": (0.05, 0.1),
    "calm": (0.6, 0.15), "quiet": (0.55, 0.15), "peaceful": (0.7, 0.15),
    "angry": (0.15, 0.85), "tense": (0.2, 0.75), "chaotic": (0.3, 0.9),
    "loud": (0.4, 0.85), "empty": (0.35, 0.15), "late": (0.4, 0.25),
}


def _fallback_blurb_to_valence_arousal(text: str) -> tuple[float, float]:
    """Public-ish (leading underscore kept for 'not the primary path', but
    directly testable/callable without needing network access at all --
    unlike blurb_to_valence_arousal, which always tries the HF model first)."""
    words = text.lower().split()
    hits = [_FALLBACK_LEXICON[w.strip(".,!?")] for w in words if w.strip(".,!?") in _FALLBACK_LEXICON]
    if not hits:
        return 0.5, 0.4  # neutral default
    v = sum(h[0] for h in hits) / len(hits)
    a = sum(h[1] for h in hits) / len(hits)
    return v, a


def blurb_to_valence_arousal(text: str) -> tuple[float, float]:
    """
    Returns (valence, arousal), each in [0, 1], as the probability-
    weighted average over the HF emotion distribution. Falls back to a
    tiny keyword lexicon only if the HF model is unreachable.
    """
    try:
        classifier = _get_classifier()
        results = classifier(text)[0]  # list of {"label": ..., "score": ...}

        valence = 0.0
        arousal = 0.0
        for r in results:
            v, a = EMOTION_VAD[r["label"]]
            valence += v * r["score"]
            arousal += a * r["score"]

        return valence, arousal

    except Exception as e:
        print(f"[sentiment] HF model unavailable ({e.__class__.__name__}), using fallback lexicon")
        return _fallback_blurb_to_valence_arousal(text)


if __name__ == "__main__":
    tests = [
        "A quiet funeral, everyone dressed in black, holding back tears.",
        "A wild birthday party with kids running around and balloons everywhere.",
        "An empty office at 2am, one person still typing.",
    ]
    for t in tests:
        v, a = blurb_to_valence_arousal(t)
        print(f"{t!r:70s} -> valence={v:.2f} arousal={a:.2f}")
