"""Analyze every sampled moment in an uploaded video."""
from __future__ import annotations

import time
from pathlib import Path

from .agents.judge import build_judge
from .capture.video import VideoSource
from .music import strategies
from .music.corpus import Corpus
from .music.vibe import build_antivibe
from .perceive import audio_features
from .perceive.scene import build_perceiver


class VideoAnalyzer:
    """Create a replay session without controlling a music player."""

    def __init__(self, cfg, perceiver=None, judge=None, corpus=None):
        self.cfg = cfg
        self.perceiver = perceiver or build_perceiver(cfg.section("perceive"))
        self.judge = judge or build_judge(cfg.section("judge"))
        self.corpus = corpus or Corpus.load()

        agent_cfg = cfg.section("antagonize")
        self.strategy_names = agent_cfg.get("strategies") or ["genre_antipode"]
        self.per_strategy = int(agent_cfg.get("candidates_per_strategy", 4))

    def analyze(self, path: str | Path, source_name: str | None = None) -> dict:
        capture_cfg = dict(self.cfg.section("capture"))
        capture_cfg.update(
            source="video",
            video_path=str(path),
            realtime=False,
            loop=False,
        )
        source = VideoSource(capture_cfg)
        moments = []
        selected_ids: set[str] = set()

        reset = getattr(self.perceiver, "reset", None)
        if callable(reset):
            reset()

        source.open()
        duration = source.duration_s
        try:
            for observation in source.stream():
                started = time.time()
                features = audio_features.extract(
                    observation.audio,
                    observation.sample_rate,
                )
                scene = self.perceiver.read(
                    observation.frame,
                    features,
                    observation.meta,
                )
                opposite = build_antivibe(scene)
                candidates = strategies.generate(
                    scene,
                    opposite,
                    self.corpus,
                    self.strategy_names,
                    selected_ids,
                    self.per_strategy,
                )
                if not candidates:
                    candidates = strategies.generate(
                        scene,
                        opposite,
                        self.corpus,
                        self.strategy_names,
                        set(),
                        self.per_strategy,
                    )
                if not candidates:
                    continue

                verdict = self.judge.judge(scene, opposite, candidates)
                selected_ids.add(verdict.track.id)
                video_time = float(observation.meta.get("video_time", 0.0))

                considered: dict[str, list[dict]] = {}
                for candidate in candidates:
                    considered.setdefault(candidate.strategy, []).append({
                        "title": candidate.track.title,
                        "artist": candidate.track.artist,
                        "score": round(candidate.raw_distance, 3),
                        "why": candidate.notes,
                    })

                moments.append({
                    "video_time": video_time,
                    "wall_time": time.time(),
                    "scene": {
                        "setting": scene.setting,
                        "activity": scene.activity,
                        "mood": scene.mood_label,
                        "confidence": scene.confidence,
                        "tempo": scene.tempo_feel.value,
                        "meter": scene.meter.value,
                        "colors": scene.dominant_colors,
                        "vibe": scene.vibe.model_dump(),
                    },
                    "opposite": {
                        "target_vibe": opposite.target.model_dump(),
                        "looking_for": opposite.target_genres,
                        "why": opposite.rationale,
                    },
                    "considered": considered,
                    "chosen": {
                        "title": verdict.track.title,
                        "artist": verdict.track.artist,
                        "quip": verdict.quip,
                        "strategy": verdict.strategy,
                        "mismatch": verdict.mismatch,
                        "why": verdict.reasoning,
                        "runner_ups": verdict.runner_ups,
                    },
                    "played": {
                        "at_video_time": video_time,
                        "mode": "interrupt" if not moments else "queue",
                        "track_id": verdict.track.id,
                        "genres": verdict.track.genres,
                        "latency_ms": int((time.time() - started) * 1000),
                    },
                })
        finally:
            source.close()

        interval = float(capture_cfg.get("frame_interval_s", 5.0))
        name = Path(source_name or str(path)).stem or "uploaded_video"
        return {
            "session": name,
            "source": source_name or Path(path).name,
            "moment_count": len(moments),
            "sample_interval_s": interval,
            "duration_s": round(duration, 2),
            "model": getattr(self.perceiver, "model", self.perceiver.backend),
            "README": (
                "Each moment is sampled from the uploaded video. "
                "The scene contains the detected mood. "
                "The chosen track is intentionally wrong for that mood."
            ),
            "moments": moments,
        }
