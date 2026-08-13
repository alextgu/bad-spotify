"""Local file playback. The bulletproof demo path: no auth, no network."""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from ..schemas import Track


class LocalPlayer:
    name = "local"

    def __init__(self, cfg: dict):
        self.dir = Path(cfg.get("local_library", "data/library"))
        self.volume = float(cfg.get("volume", 0.7))
        self._proc: subprocess.Popen | None = None
        self._cmd = self._find_player()
        if not self._cmd:
            raise RuntimeError("no ffplay/afplay/mpv found on PATH")

    @staticmethod
    def _find_player() -> list[str] | None:
        for exe, args in (("ffplay", ["-nodisp", "-autoexit", "-loglevel", "quiet"]),
                          ("mpv", ["--no-video", "--really-quiet"]),
                          ("afplay", [])):
            if shutil.which(exe):
                return [exe, *args]
        return None

    def _resolve(self, track: Track) -> Path | None:
        if track.uri and Path(track.uri).exists():
            return Path(track.uri)
        if not self.dir.exists():
            return None
        for p in self.dir.rglob("*"):
            if p.suffix.lower() in {".mp3", ".wav", ".m4a", ".flac", ".ogg"}:
                stem = p.stem.lower()
                if track.id in stem or track.title.lower()[:12] in stem:
                    return p
        return None

    def play(self, track: Track) -> None:
        path = self._resolve(track)
        if path is None:
            raise FileNotFoundError(f"no audio file for {track.title!r} in {self.dir}")
        self.stop()
        self._proc = subprocess.Popen([*self._cmd, str(path)],
                                      stdout=subprocess.DEVNULL,
                                      stderr=subprocess.DEVNULL)
        print(f"  [PLAY:local] {track.title} <- {path.name}")

    def stop(self) -> None:
        if self._proc and self._proc.poll() is None:
            self._proc.terminate()
        self._proc = None

    def set_volume(self, level: float) -> None:
        self.volume = level
