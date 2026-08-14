"""Recording a run so it can be replayed without rerunning anything.

Every decision gets written down with *where in the video it happened*. That
one field is what makes the presentation site possible: it can show which song
was chosen and exactly where it lands in the footage, with no backend, no API
keys, and nothing to fail live.

    python run.py --video demo/park.mp4 --record park
    -> data/sessions/park.json

The file is deliberately self-describing. Somebody building the site should be
able to open it and understand it without reading any Python.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from .bus import BUS
from .schemas import PipelineEvent

ROOT = Path(__file__).resolve().parents[2]
SESSIONS = ROOT / "data" / "sessions"


@dataclass
class SessionRecorder:
    """Subscribes to the event bus and assembles a replayable transcript."""

    name: str
    source: str = ""
    moments: list[dict] = field(default_factory=list)
    _pending: dict = field(default_factory=dict)

    def attach(self) -> "SessionRecorder":
        BUS.subscribe(self._on_event)
        return self

    #Event recording

    def _on_event(self, ev: PipelineEvent) -> None:
        d = ev.detail or {}

        if ev.kind == "scene":
            #Starts a fresh moment when a new scene arrives
            self._pending = {
                "video_time": d.get("video_time"),
                "wall_time": ev.ts,
                "scene": {
                    "setting": d.get("setting"),
                    "activity": d.get("activity"),
                    "mood": ev.label,
                    "confidence": d.get("confidence"),
                    "tempo": d.get("tempo"),
                    "meter": d.get("meter"),
                    "colors": d.get("colors", []),
                    "vibe": d.get("vibe", {}),
                },
            }

        elif ev.kind == "antivibe" and self._pending:
            self._pending["opposite"] = {
                "target_vibe": d.get("target", {}),
                "looking_for": d.get("target_genres", []),
                "why": ev.label,
            }

        elif ev.kind == "candidates" and self._pending:
            self._pending.setdefault("considered", {})[ev.label] = d.get("picks", [])

        elif ev.kind == "verdict" and self._pending:
            self._pending["chosen"] = {
                "title": ev.label,
                "artist": d.get("artist"),
                "quip": d.get("quip"),
                "strategy": d.get("strategy"),
                "mismatch": d.get("mismatch"),
                "why": d.get("reasoning"),
                "runner_ups": d.get("runner_ups", []),
            }

        elif ev.kind == "play" and self._pending:
            self._pending["played"] = {
                #Stores the playback time used by the session timeline
                "at_video_time": d.get("video_time"),
                "mode": d.get("mode"),
                "track_id": d.get("track_id"),
                "genres": d.get("genres", []),
                "latency_ms": d.get("elapsed_ms"),
            }
            self.moments.append(self._pending)
            self._pending = {}

    #Session output

    def to_dict(self) -> dict:
        played = [m for m in self.moments if m.get("played")]
        return {
            "session": self.name,
            "source": self.source,
            "moment_count": len(played),
            "README": (
                "Each entry in `moments` is one decision. `video_time` is where "
                "the scene was read; `played.at_video_time` is where the song "
                "actually starts -- use that one for the timeline, since the "
                "scene is often read a few seconds earlier. `played.mode` is "
                "'queue' (lines up next) or 'interrupt' (cuts in now)."
            ),
            "moments": played,
        }

    def save(self, path: Path | None = None) -> Path:
        path = path or (SESSIONS / f"{self.name}.json")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_dict(), indent=2))
        return path

    def summary(self) -> str:
        played = [m for m in self.moments if m.get("played")]
        if not played:
            return "no songs were played -- nothing to replay"
        lines = [f"{len(played)} songs chosen:"]
        for m in played:
            t = (m.get("played") or {}).get("at_video_time")
            if t is None:
                t = m.get("video_time")
            stamp = f"{int(t // 60):02d}:{int(t % 60):02d}" if t is not None else " --:--"
            chosen = m.get("chosen", {})
            mode = (m.get("played") or {}).get("mode", "")
            lines.append(
                f"  {stamp}  {chosen.get('title', '?')} - {chosen.get('artist', '?')}"
                f"  [{mode}]  \"{chosen.get('quip', '')}\"")
        return "\n".join(lines)
