"""
Direct audio/video -> (valence, arousal) + instrument/sound tags,
bypassing the text-blurb step entirely.

Reuses EMOTION_VAD from sentiment.py so CLIP/CLAP's zero-shot label
scores fold into the exact same (valence, arousal) representation the
rest of the pipeline already expects -- no downstream changes needed.

NOTE: These models are NOT downloadable in this sandbox (huggingface.co
isn't network-whitelisted here) -- this is written to run correctly on
your machine, unverified in this environment. Test it there before the
hackathon, not the night of.
"""

from functools import lru_cache
import numpy as np
from sentiment import EMOTION_VAD

MOOD_LABELS = list(EMOTION_VAD.keys())  # reuse existing vocabulary: anger, disgust, fear, joy, neutral, sadness, surprise


@lru_cache(maxsize=1)
def _get_clip():
    from transformers import CLIPProcessor, CLIPModel
    model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
    processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
    return model, processor


@lru_cache(maxsize=1)
def _get_clap():
    from transformers import ClapProcessor, ClapModel
    model = ClapModel.from_pretrained("laion/clap-htsat-unfused")
    processor = ClapProcessor.from_pretrained("laion/clap-htsat-unfused")
    return model, processor


@lru_cache(maxsize=1)
def _get_ast():
    from transformers import pipeline
    return pipeline("audio-classification", model="MIT/ast-finetuned-audioset-10-10-0.4593")


def _labels_to_valence_arousal(label_scores: dict[str, float]) -> tuple[float, float]:
    """Probability-weighted average over EMOTION_VAD, same logic as sentiment.py."""
    valence = sum(EMOTION_VAD[label][0] * score for label, score in label_scores.items())
    arousal = sum(EMOTION_VAD[label][1] * score for label, score in label_scores.items())
    return valence, arousal


def video_mood(frame_image) -> tuple[float, float]:
    """
    frame_image: a PIL.Image (one video frame).
    Returns (valence, arousal) via CLIP zero-shot classification against
    MOOD_LABELS, phrased as full prompts for better CLIP performance.
    """
    import torch
    model, processor = _get_clip()
    prompts = [f"a photo of a {label} scene" for label in MOOD_LABELS]

    inputs = processor(text=prompts, images=frame_image, return_tensors="pt", padding=True)
    outputs = model(**inputs)
    probs = outputs.logits_per_image.softmax(dim=1)[0].detach().numpy()

    label_scores = dict(zip(MOOD_LABELS, probs))
    return _labels_to_valence_arousal(label_scores)


def audio_mood(waveform: np.ndarray, sr: int = 48000) -> tuple[float, float]:
    """
    waveform: 1D numpy array, CLAP expects 48kHz mono.
    Returns (valence, arousal) via CLAP zero-shot classification.
    """
    import torch
    model, processor = _get_clap()
    prompts = [f"{label} sounding music" for label in MOOD_LABELS]

    inputs = processor(text=prompts, audios=waveform, sampling_rate=sr, return_tensors="pt", padding=True)
    outputs = model(**inputs)
    probs = outputs.logits_per_audio.softmax(dim=1)[0].detach().numpy()

    label_scores = dict(zip(MOOD_LABELS, probs))
    return _labels_to_valence_arousal(label_scores)


def audio_tags(waveform: np.ndarray, sr: int = 16000, top_k: int = 5) -> list[tuple[str, float]]:
    """
    waveform: 1D numpy array, AST expects 16kHz mono.
    Returns top_k (label, score) pairs from AudioSet's 527 classes --
    e.g. [("Guitar", 0.62), ("Speech", 0.31), ...]. This is a categorical
    tag list, not folded into (valence, arousal) -- feed it to your DJ
    voice-line generation step or use it to bias genre matching toward
    genres whose instrument profile overlaps with what's actually in
    the room, if you build that layer.
    """
    classifier = _get_ast()
    results = classifier({"array": waveform, "sampling_rate": sr}, top_k=top_k)
    return [(r["label"], r["score"]) for r in results]


if __name__ == "__main__":
    print("This module needs real audio/video input and a machine with")
    print("huggingface.co access -- run these functions with your actual")
    print("captured frames/audio, not as a standalone script.")
