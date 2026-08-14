"""Spotify as the speaker.

Two things worth knowing before you touch this file.

**Spotify is not our brain.** In Nov 2024 the audio-features, audio-analysis,
recommendations and related-artists endpoints were restricted to apps already
in extended quota mode; new apps cannot get them. Search, metadata and
playback control still work. So all the music intelligence lives in our own
corpus and vibe space, and this file only does what Spotify still allows:
find a track, and make it come out of a speaker.

**Queue by default.** The pipeline queues the next song rather than cutting
the current one off. Queueing is gentler and paces itself; interrupting is
funnier, because the wrong music lands while the moment is still happening.
Both are supported -- see `play_mode` in config.yaml.

Requires Spotify Premium. The Web API refuses playback control on free
accounts and there is no way around that.
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path

from ..schemas import Track
from .spotify_match import best_match, search_queries
from ..log import notice as print  # stdout is reserved for data

SCOPES = (
    "user-modify-playback-state "
    "user-read-playback-state "
    "user-read-currently-playing"
)

ROOT = Path(__file__).resolve().parents[3]
URI_CACHE = ROOT / "data" / "spotify_uris.json"
TOKEN_CACHE = ROOT / ".spotify-token"


class SpotifyError(RuntimeError):
    """Raised with a message a human can act on, not an HTTP status code."""


def explain(exc) -> str:
    """Turn a spotipy exception into something that says what to do next."""
    status = getattr(exc, "http_status", None)
    reason = (getattr(exc, "reason", "") or "").upper()
    text = str(exc).lower()

    if status == 404 or reason == "NO_ACTIVE_DEVICE":
        return ("No active Spotify device. Open Spotify on your phone or desktop "
                "and press play on anything once, then try again.")
    if status == 403:
        if "premium" in reason.lower() or "premium" in text:
            return ("Spotify Premium is required for playback control. "
                    "A free account cannot be driven by the API.")
        return (f"Spotify refused the request ({exc}). Usually that means the "
                "account is not Premium, or the track is unavailable in this market.")
    if status == 401:
        return ("Spotify token expired or the scopes changed. Delete .spotify-token "
                "and rerun: python scripts/spotify_setup.py")
    if status == 429:
        return "Rate limited by Spotify. Back off and retry."
    return str(exc)


class SpotifyPlayer:
    name = "spotify"

    def __init__(self, cfg: dict, client=None):
        """`client` exists so the logic here can be tested without a Spotify
        account. Pass a stand-in implementing the handful of spotipy methods
        we use; leave it None in real use and OAuth runs normally."""
        self.cfg = cfg
        self.volume = float(cfg.get("volume", 0.7))
        self.market = cfg.get("market", "from_token")
        self.play_mode = (cfg.get("play_mode") or "queue").lower()
        self.skip_to_queued = bool(cfg.get("skip_to_queued", False))
        self.preferred_device = cfg.get("device_name")

        if client is not None:
            self.sp = client
        else:
            import spotipy
            from spotipy.oauth2 import SpotifyOAuth

            missing = [k for k in ("SPOTIFY_CLIENT_ID", "SPOTIFY_CLIENT_SECRET")
                       if not os.environ.get(k)]
            if missing:
                raise SpotifyError(
                    f"missing {', '.join(missing)} in the environment. Copy "
                    ".env.example to .env and fill them in from "
                    "https://developer.spotify.com/dashboard")

            self.sp = spotipy.Spotify(
                auth_manager=SpotifyOAuth(
                    client_id=os.environ["SPOTIFY_CLIENT_ID"],
                    client_secret=os.environ["SPOTIFY_CLIENT_SECRET"],
                    redirect_uri=os.environ.get("SPOTIFY_REDIRECT_URI",
                                                "http://127.0.0.1:8888/callback"),
                    scope=SCOPES,
                    cache_path=str(TOKEN_CACHE),
                    open_browser=True,
                ),
                requests_timeout=10,
            )
        self._uris: dict[str, str] = self._load_cache()
        self.device_id: str | None = None

    #Account access

    def check_account(self) -> dict:
        """Return the user profile, raising if the account can't be controlled."""
        try:
            me = self.sp.current_user()
        except Exception as e:
            raise SpotifyError(explain(e)) from e
        if me.get("product") != "premium":
            raise SpotifyError(
                f"account '{me.get('display_name') or me.get('id')}' is "
                f"'{me.get('product')}', not premium. Playback control needs Premium.")
        return me

    #Playback device

    def list_devices(self) -> list[dict]:
        try:
            return self.sp.devices().get("devices", [])
        except Exception as e:
            raise SpotifyError(explain(e)) from e

    def ensure_device(self, force: bool = False) -> str:
        """Find a usable device and make it the active one."""
        if self.device_id and not force:
            return self.device_id

        devices = self.list_devices()
        if not devices:
            raise SpotifyError(
                "No Spotify devices visible. Open the Spotify app on your phone "
                "or desktop and press play on anything once -- the API can only "
                "see devices that are already awake.")

        chosen = None
        if self.preferred_device:
            chosen = next(
                (d for d in devices
                 if self.preferred_device.lower() in (d.get("name") or "").lower()),
                None)
            if chosen is None:
                names = ", ".join(d.get("name", "?") for d in devices)
                print(f"[spotify] device {self.preferred_device!r} not found; "
                      f"visible: {names}")
        if chosen is None:
            chosen = next((d for d in devices if d.get("is_active")), devices[0])

        self.device_id = chosen["id"]
        if not chosen.get("is_active"):
            try:
                self.sp.transfer_playback(device_id=self.device_id, force_play=False)
                time.sleep(0.4)   #Gives Spotify time to update the device
            except Exception as e:
                print(f"[spotify] transfer to {chosen['name']!r} failed: {explain(e)}")
        print(f"[spotify] device: {chosen['name']} ({chosen['type']})")
        return self.device_id

    #Track lookup

    def _load_cache(self) -> dict[str, str]:
        if URI_CACHE.exists():
            try:
                data = json.loads(URI_CACHE.read_text())
                print(f"[spotify] {len(data)} cached track URIs")
                return data
            except Exception:
                print("[spotify] URI cache unreadable, ignoring it")
        return {}

    def save_cache(self) -> None:
        URI_CACHE.parent.mkdir(parents=True, exist_ok=True)
        URI_CACHE.write_text(json.dumps(self._uris, indent=2, sort_keys=True))

    def resolve(self, track: Track, use_cache: bool = True):
        """Find the Spotify URI for one of our tracks. Returns (uri, note)."""
        if track.uri and track.uri.startswith("spotify:"):
            return track.uri, "from corpus"
        if use_cache and track.id in self._uris:
            return self._uris[track.id], "cached"

        rejections: list[str] = []
        for query in search_queries(track.title, track.artist):
            try:
                res = self.sp.search(q=query, type="track", limit=10,
                                     market=self.market)
            except Exception as e:
                return None, f"search failed: {explain(e)}"
            items = res.get("tracks", {}).get("items", [])
            winner, scored = best_match(items, track.title, track.artist)
            if winner:
                self._uris[track.id] = winner.uri
                return winner.uri, f"matched {winner.title!r} by {winner.artist}"
            rejections.extend(m.rejected for m in scored[:2] if m.rejected)

        why = rejections[0] if rejections else "no results"
        return None, f"unresolved ({why})"

    #Playback control

    def _is_playing(self) -> bool:
        try:
            state = self.sp.current_playback()
            return bool(state and state.get("is_playing"))
        except Exception:
            return False

    def play(self, track: Track, mode: str | None = None) -> None:
        mode = (mode or self.play_mode).lower()
        uri, note = self.resolve(track)
        if not uri:
            raise SpotifyError(f"{track.title!r} by {track.artist}: {note}")

        device_id = self.ensure_device()

        def attempt(dev: str) -> str:
            #Starts playback when a silent device cannot process the queue
            if mode == "queue" and self._is_playing():
                self.sp.add_to_queue(uri, device_id=dev)
                if self.skip_to_queued:
                    self.sp.next_track(device_id=dev)
                    return "queued+skipped"
                return "queued"
            self.sp.start_playback(device_id=dev, uris=[uri])
            return "playing"

        try:
            action = attempt(device_id)
        except Exception as e:
            #Refreshes the playback device once after a failed request
            print(f"[spotify] first attempt failed ({explain(e)}); re-acquiring device")
            try:
                device_id = self.ensure_device(force=True)
                action = attempt(device_id)
            except Exception as e2:
                raise SpotifyError(explain(e2)) from e2

        print(f"  [SPOTIFY:{action}] {track.title} - {track.artist}  ({note})")

    def stop(self) -> None:
        try:
            self.sp.pause_playback(device_id=self.device_id)
        except Exception:
            pass   #Pause is already complete

    def set_volume(self, level: float) -> None:
        self.volume = max(0.0, min(1.0, level))
        try:
            self.sp.volume(int(self.volume * 100), device_id=self.device_id)
        except Exception:
            pass   #The device does not support remote volume
