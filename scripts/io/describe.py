#!/usr/bin/env python3
"""STEP 2 -- a picture becomes a description of the moment.

    python scripts/io/describe.py --image park.jpg
    python scripts/io/describe.py --image park.jpg --audio room.wav
    python scripts/io/describe.py --text "a hospital waiting room at 3am"

in   an image (+ optional audio), or a text description to skip perception
out  a SceneRead as JSON -- setting, activity, mood, and five 0-1 vibe scores

THIS IS THE SWAPPABLE ONE. Everything downstream only cares about the shape
of the output, not how it was produced. If someone wants to try a HuggingFace
sentiment model, or two separate audio and video models, this is the only file
that has to change -- and you can compare approaches by diffing the JSON.

Backend comes from config.yaml (`perceive.backend`): mock needs nothing,
gemini needs GOOGLE_API_KEY.
"""
from __future__ import annotations

import argparse

from _common import load_config, log, write_json  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--image")
    ap.add_argument("--audio", help="wav file of the surrounding sound")
    ap.add_argument("--text", help="analyze a typed scene description")
    ap.add_argument("--backend", choices=["mock", "gemini"],
                    help="override config.yaml")
    args = ap.parse_args()

    if not (args.image or args.text):
        log("error: pass --image or --text")
        raise SystemExit(2)

    cfg = load_config().section("perceive")
    if args.backend:
        cfg = {**cfg, "backend": args.backend}

    if args.text:
        from badspotify.perceive.scene import build_perceiver, read_description
        scene = read_description(build_perceiver(cfg), args.text)
        log(f"[describe] from text: {scene.mood_label}")
        write_json(scene.model_dump())
        return

    import cv2
    from badspotify.perceive import audio_features
    from badspotify.perceive.scene import build_perceiver

    frame = cv2.imread(args.image)
    if frame is None:
        log(f"error: could not read image {args.image}")
        raise SystemExit(1)

    feats = audio_features.AudioFeatures()
    if args.audio:
        import wave

        import numpy as np
        with wave.open(args.audio, "rb") as w:
            raw = w.readframes(w.getnframes())
            rate = w.getframerate()
        audio = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
        feats = audio_features.extract(audio, rate)
        log(f"[describe] audio: {feats.summary()}")

    perceiver = build_perceiver(cfg)
    scene = perceiver.read(frame, feats, {"index": 0})
    log(f"[describe] {scene.setting} -- {scene.mood_label} "
        f"(confidence {scene.confidence:.2f}, {scene.latency_ms}ms, "
        f"via {scene.source})")
    write_json(scene.model_dump())


if __name__ == "__main__":
    main()
