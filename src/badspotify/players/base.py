from __future__ import annotations

from typing import Protocol

from ..config import resolve_backend
from ..schemas import Track


class Player(Protocol):
    name: str

    def play(self, track: Track) -> None: ...
    def stop(self) -> None: ...
    def set_volume(self, level: float) -> None: ...


def build_player(cfg: dict) -> Player:
    backend = (cfg.get("backend") or "mock").lower()
    if backend == "spotify":
        backend = resolve_backend("spotify", "SPOTIFY_CLIENT_ID", "player")
    if backend == "spotify":
        try:
            from .spotify import SpotifyPlayer
            return SpotifyPlayer(cfg)
        except Exception as e:
            print(f"[player] spotify init failed ({e}) -> local")
            backend = "local"
    if backend == "local":
        try:
            from .local import LocalPlayer
            return LocalPlayer(cfg)
        except Exception as e:
            print(f"[player] local init failed ({e}) -> mock")
    from .mock import MockPlayer
    return MockPlayer(cfg)
