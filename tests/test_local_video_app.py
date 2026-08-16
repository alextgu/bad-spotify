"""Focused tests for local mood analysis and video uploads."""
from __future__ import annotations

import sys
import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from badspotify.hud.server import create_app  #noqa: E402
from badspotify.analysis import VideoAnalyzer  #noqa: E402
from badspotify.config import Config  #noqa: E402
from badspotify.music.corpus import Corpus  #noqa: E402
from badspotify.perceive.audio_features import AudioFeatures  #noqa: E402
from badspotify.perceive.scene import (  #noqa: E402
    HuggingFacePerceiver,
    MOOD_PROFILES,
    SCENE_LABELS,
    scene_from_text,
)
from badspotify.schemas import Track, Vibe  #noqa: E402


class FakeClassifier:
    def __call__(self, image, candidate_labels):
        scores = {label: .001 for label in candidate_labels}
        scores["energetic"] = .60
        scores["a gym or sports scene"] = .35
        return [
            {"label": label, "score": score}
            for label, score in scores.items()
        ]


class SequencePerceiver:
    backend = "mock"

    def __init__(self, scenes):
        self.scenes = scenes
        self.index = 0

    def reset(self):
        self.index = 0

    def read(self, frame, audio_features, meta):
        scene = self.scenes[min(self.index, len(self.scenes) - 1)]
        self.index += 1
        return scene


class ConnectedPlayer:
    name = "spotify"

    def __init__(self):
        self.calls = []

    def connection_status(self):
        return {
            "connected": True,
            "account": "Demo Account",
            "device": "Demo Speaker",
        }

    def play(self, track, mode):
        self.calls.append(("play", track.id, mode))

    def stop(self):
        self.calls.append(("stop",))


def playback_runtime():
    player = ConnectedPlayer()
    track = Track(id="known", title="Known Song", artist="Known Artist", vibe=Vibe())
    runtime = SimpleNamespace(
        player=player,
        graph=SimpleNamespace(corpus=Corpus([track])),
    )
    return runtime, player


def endpoint(app, path):
    return next(item.endpoint for item in app.routes if item.path == path)


def test_local_classifier_builds_a_complete_scene_read():
    frame = np.full((90, 160, 3), (40, 120, 220), dtype=np.uint8)
    perceiver = HuggingFacePerceiver({}, classifier=FakeClassifier())
    audio = AudioFeatures(
        rms=.12,
        onset_rate=6.0,
        spectral_centroid=2600,
        pulse_regularity=.8,
    )

    scene = perceiver.read(frame, audio, {"index": 0})

    assert scene.source == "huggingface"
    assert scene.mood_label == "energetic"
    assert scene.setting == "a gym or sports scene"
    assert scene.vibe.arousal > .6
    assert scene.meter.value == "steady"
    assert 1 <= len(scene.dominant_colors) <= 3


def test_taxonomy_has_distinct_moods_and_scenes():
    assert len(MOOD_PROFILES) >= 8
    assert len(SCENE_LABELS) >= 8
    assert set(MOOD_PROFILES).isdisjoint(SCENE_LABELS)


def test_upload_endpoint_rejects_unknown_extensions():
    import asyncio
    from io import BytesIO

    import pytest
    from fastapi import HTTPException, UploadFile

    app = create_app(object())
    route = next(item for item in app.routes if item.path == "/api/analyze-video")
    upload = UploadFile(BytesIO(b"not a video"), filename="video.exe")
    with pytest.raises(HTTPException) as raised:
        asyncio.run(route.endpoint(upload))
    asyncio.run(upload.close())

    assert raised.value.status_code == 415


def test_playback_api_reports_connection_and_controls_known_track():
    import asyncio

    runtime, player = playback_runtime()
    app = create_app(runtime)

    status = asyncio.run(endpoint(app, "/api/playback")())
    body = json.loads(status.body)
    assert body["connected"] is True
    assert body["device"] == "Demo Speaker"

    played = asyncio.run(endpoint(app, "/api/playback/play")({"track_id": "known"}))
    assert played["title"] == "Known Song"
    assert player.calls == [("play", "known", "interrupt")]

    asyncio.run(endpoint(app, "/api/playback/stop")())
    assert player.calls[-1] == ("stop",)


def test_playback_api_rejects_tracks_outside_the_corpus():
    import asyncio

    import pytest
    from fastapi import HTTPException

    runtime, player = playback_runtime()
    app = create_app(runtime)

    with pytest.raises(HTTPException) as raised:
        asyncio.run(endpoint(app, "/api/playback/play")({"track_id": "not-known"}))

    assert raised.value.status_code == 404
    assert player.calls == []


def test_video_analyzer_samples_every_five_seconds(tmp_path):
    import cv2
    import pytest

    video_path = tmp_path / "sample.mp4"
    writer = cv2.VideoWriter(
        str(video_path),
        cv2.VideoWriter_fourcc(*"mp4v"),
        1.0,
        (64, 48),
    )
    if not writer.isOpened():
        pytest.skip("the local OpenCV build has no MP4 encoder")
    for index in range(11):
        frame = np.full((48, 64, 3), index * 20, dtype=np.uint8)
        if index > 0:
            frame[:, 32:, :] = min(255, index * 20 + 40)
        writer.write(frame)
    writer.release()

    cfg = Config({
        "capture": {"frame_interval_s": 5.0, "audio_window_s": 3.0},
        "perceive": {"backend": "mock"},
        "judge": {"backend": "mock"},
        "antagonize": {
            "strategies": ["genre_antipode", "tempo_clash", "lyrical_irony"],
            "candidates_per_strategy": 2,
        },
    })

    result = VideoAnalyzer(cfg).analyze(video_path, "sample.mp4")

    assert result["sample_interval_s"] == 5.0
    assert result["moment_count"] == 1
    assert [moment["video_time"] for moment in result["moments"]] == [5.0]
    assert all(moment["scene"]["mood"] for moment in result["moments"])
    assert all(moment["chosen"]["title"] for moment in result["moments"])
    assert all(moment["played"]["mode"] is None for moment in result["moments"])
    assert result["moments"][0]["played"]["crossfade_seconds"] == 0.0

    scenes = [
        scene_from_text("quiet funeral"),
        scene_from_text("birthday party"),
    ]
    changed = VideoAnalyzer(cfg, perceiver=SequencePerceiver(scenes)).analyze(
        video_path,
        "sample.mp4",
    )

    assert changed["moment_count"] == 2
    assert changed["moments"][1]["played"]["crossfade_seconds"] == 2.0
