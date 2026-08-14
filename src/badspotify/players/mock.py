from __future__ import annotations

from ..schemas import Track
from ..log import notice as print  # stdout is reserved for data


class MockPlayer:
    """Prints instead of playing. Lets the whole graph run on a laptop with
    no accounts, no audio device, and no network."""
    name = "mock"

    def __init__(self, cfg: dict | None = None):
        self.cfg = cfg or {}
        self.current: Track | None = None
        self.volume = float(self.cfg.get("volume", 0.7))

    def play(self, track: Track, mode: str = "interrupt") -> None:
        self.current = track
        verb = "QUEUE" if mode == "queue" else "PLAY"
        print(f"  [{verb}] {track.title} - {track.artist}  ({', '.join(track.genres)})")

    def stop(self) -> None:
        self.current = None

    def set_volume(self, level: float) -> None:
        self.volume = level
