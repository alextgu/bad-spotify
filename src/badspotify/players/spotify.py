"""Spotify as a SPEAKER, not a brain.

Important constraint discovered while planning: as of Nov 2024 Spotify
restricted audio-features, audio-analysis, recommendations and
related-artists to apps already in extended quota mode. New apps cannot get
them. So all of our music intelligence lives in our own corpus and vibe
space, and Spotify is used only for what still works: search, metadata,
and playback control.

That division is a feature. It means the interesting part of the project is
ours, and the streaming is a swappable backend.
"""
from __future__ import annotations

import os

from ..schemas import Track

SCOPES = "user-modify-playback-state user-read-playback-state streaming"


class SpotifyPlayer:
    name = "spotify"

    def __init__(self, cfg: dict):
        import spotipy
        from spotipy.oauth2 import SpotifyOAuth

        self.cfg = cfg
        self.volume = float(cfg.get("volume", 0.7))
        self.sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
            client_id=os.environ["SPOTIFY_CLIENT_ID"],
            client_secret=os.environ["SPOTIFY_CLIENT_SECRET"],
            redirect_uri=os.environ.get("SPOTIFY_REDIRECT_URI",
                                        "http://127.0.0.1:8888/callback"),
            scope=SCOPES,
            open_browser=True,
        ))
        self.device_id = self._pick_device()
        self._uri_cache: dict[str, str] = {}

    def _pick_device(self) -> str | None:
        try:
            devices = self.sp.devices().get("devices", [])
        except Exception:
            return None
        if not devices:
            print("[spotify] no active device. Open Spotify on your phone or "
                  "desktop once, press play, then rerun.")
            return None
        active = next((d for d in devices if d.get("is_active")), devices[0])
        print(f"[spotify] using device: {active['name']} ({active['type']})")
        return active["id"]

    def resolve_uri(self, track: Track) -> str | None:
        if track.uri and track.uri.startswith("spotify:"):
            return track.uri
        if track.id in self._uri_cache:
            return self._uri_cache[track.id]
        q = f"track:{track.title} artist:{track.artist}"
        try:
            res = self.sp.search(q=q, type="track", limit=1)
            items = res.get("tracks", {}).get("items", [])
            if items:
                uri = items[0]["uri"]
                self._uri_cache[track.id] = uri
                return uri
        except Exception as e:
            print(f"[spotify] search failed for {track.title!r}: {e}")
        return None

    def play(self, track: Track) -> None:
        uri = self.resolve_uri(track)
        if not uri:
            raise RuntimeError(f"could not resolve {track.title!r} on Spotify")
        self.sp.start_playback(device_id=self.device_id, uris=[uri])
        print(f"  [PLAY:spotify] {track.title} - {track.artist}")

    def stop(self) -> None:
        try:
            self.sp.pause_playback(device_id=self.device_id)
        except Exception:
            pass

    def set_volume(self, level: float) -> None:
        self.volume = level
        try:
            self.sp.volume(int(max(0, min(1, level)) * 100), device_id=self.device_id)
        except Exception:
            pass
