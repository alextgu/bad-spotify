"""Spotify player logic, tested against a stand-in for the real API.

None of this needs an account. It can't tell us whether YOUR Spotify works --
only running `scripts/spotify_setup.py` does that. What it does is make sure
that when something goes wrong out there, we behave sensibly instead of
crashing: device asleep, account not Premium, track unavailable, search
returning junk.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from badspotify.players.spotify import SpotifyError, SpotifyPlayer  #noqa: E402
from badspotify.schemas import Track, Vibe                          #noqa: E402


class SpotifyException(Exception):
    """Mirrors spotipy's exception surface closely enough to test against."""

    def __init__(self, http_status, reason="", msg=""):
        super().__init__(msg or reason or str(http_status))
        self.http_status = http_status
        self.reason = reason


class FakeSpotify:
    def __init__(self, *, product="premium", devices=None, playing=False,
                 search_items=None, fail_first_play=None):
        self._product = product
        self._devices = devices if devices is not None else [
            {"id": "d1", "name": "Alex's MacBook Pro", "type": "Computer",
             "is_active": True},
        ]
        self._playing = playing
        self._search_items = search_items or []
        self._fail_first_play = fail_first_play
        self.calls: list[tuple] = []

    def current_user(self):
        return {"id": "u1", "display_name": "Alex", "product": self._product}

    def devices(self):
        return {"devices": self._devices}

    def transfer_playback(self, device_id=None, force_play=False):
        self.calls.append(("transfer", device_id))
        for d in self._devices:
            d["is_active"] = d["id"] == device_id

    def current_playback(self):
        # Real Spotify says WHICH device is playing, and the difference
        # matters: queueing follows the active device, not the one named in
        # the call. A fake that omits it cannot catch a track queued for a
        # phone coming out of a laptop.
        active = next((d for d in self._devices if d.get("is_active")), None)
        return {"is_playing": self._playing,
                "device": {"id": active["id"]} if active else None}

    def start_playback(self, device_id=None, uris=None):
        if self._fail_first_play:
            exc, self._fail_first_play = self._fail_first_play, None
            raise exc
        self.calls.append(("start", device_id, uris[0] if uris else None))
        self._playing = True

    def add_to_queue(self, uri, device_id=None):
        if self._fail_first_play:
            exc, self._fail_first_play = self._fail_first_play, None
            raise exc
        self.calls.append(("queue", device_id, uri))

    def next_track(self, device_id=None):
        self.calls.append(("skip", device_id))

    def search(self, q=None, type=None, limit=None, market=None):
        return {"tracks": {"items": self._search_items}}

    def pause_playback(self, device_id=None):
        self.calls.append(("pause", device_id))
        self._playing = False

    def volume(self, level, device_id=None):
        self.calls.append(("volume", level))


def track(tid="hurt", title="Hurt", artist="Johnny Cash", uri=None):
    return Track(id=tid, title=title, artist=artist, vibe=Vibe(), uri=uri)


def item(name, artists, uri="spotify:track:real"):
    return {"name": name, "uri": uri, "duration_ms": 200000,
            "artists": [{"name": a} for a in artists]}


def player(fake, **cfg):
    p = SpotifyPlayer({"play_mode": "queue", **cfg}, client=fake)
    p._uris = {}          #Starts with an empty track cache
    return p


#Account behavior

def test_free_account_is_rejected_with_a_clear_reason():
    p = player(FakeSpotify(product="free"))
    with pytest.raises(SpotifyError) as e:
        p.check_account()
    assert "premium" in str(e.value).lower()


def test_premium_account_passes():
    assert player(FakeSpotify()).check_account()["product"] == "premium"


def test_an_unreadable_subscription_level_is_not_treated_as_free():
    """`product` is absent unless the token carries `user-read-private`, and
    that scope was missing from SCOPES entirely -- so the field was always
    None and the check rejected every account, Premium included. Real setup
    run, 14 Aug: "account 'Kaamil Mirza' is 'None', not premium".

    Unknown must mean unknown. Playback itself fails loudly enough if the
    account really can't be controlled.
    """
    me = player(FakeSpotify(product=None)).check_account()
    assert me["product"] is None


#Device behavior

def test_no_devices_tells_you_what_to_do():
    p = player(FakeSpotify(devices=[]))
    with pytest.raises(SpotifyError) as e:
        p.ensure_device()
    assert "press play" in str(e.value).lower(), "error should say how to fix it"


def test_prefers_the_configured_device():
    fake = FakeSpotify(devices=[
        {"id": "d1", "name": "Laptop", "type": "Computer", "is_active": True},
        {"id": "d2", "name": "Kitchen Speaker", "type": "Speaker", "is_active": False},
    ])
    p = player(fake, device_name="kitchen")
    assert p.ensure_device() == "d2"
    assert ("transfer", "d2") in fake.calls, "should wake the chosen device"


def test_connection_status_checks_the_device_without_transferring_playback():
    fake = FakeSpotify(devices=[
        {"id": "d1", "name": "Laptop", "type": "Computer", "is_active": True},
        {"id": "d2", "name": "Kitchen Speaker", "type": "Speaker",
         "is_active": False},
    ])
    status = player(fake, device_name="kitchen", require_device=True).connection_status()

    assert status["connected"] is True
    assert status["device"] == "Kitchen Speaker"
    assert not any(call[0] == "transfer" for call in fake.calls)


def test_falls_back_when_the_named_device_is_gone():
    """Someone's laptop is named in config but closed. Don't just die."""
    fake = FakeSpotify(devices=[
        {"id": "d9", "name": "Phone", "type": "Smartphone", "is_active": True},
    ])
    assert player(fake, device_name="Kitchen Speaker").ensure_device() == "d9"


#Track lookup behavior

def test_cached_uri_skips_the_search():
    fake = FakeSpotify(search_items=[item("Wrong Song", ["Nobody"])])
    p = player(fake)
    p._uris = {"hurt": "spotify:track:cached"}
    uri, note = p.resolve(track())
    assert uri == "spotify:track:cached" and note == "cached"


def test_karaoke_result_is_refused_and_the_reason_is_reported():
    fake = FakeSpotify(search_items=[
        item("Hurt (Karaoke Version)", ["Karaoke Kings"]),
    ])
    uri, note = player(fake).resolve(track())
    assert uri is None
    assert "unresolved" in note


def test_a_good_match_is_found_and_cached():
    fake = FakeSpotify(search_items=[item("Hurt", ["Johnny Cash"])])
    p = player(fake)
    uri, note = p.resolve(track())
    assert uri == "spotify:track:real"
    assert p._uris["hurt"] == uri, "a resolved track should be remembered"


def test_playing_an_unresolvable_track_raises_rather_than_going_silent():
    """The fallback ladder above this needs an exception to react to."""
    p = player(FakeSpotify(search_items=[]))
    with pytest.raises(SpotifyError):
        p.play(track())


#Playback behavior

def test_queue_mode_queues_when_something_is_already_playing():
    fake = FakeSpotify(playing=True, search_items=[item("Hurt", ["Johnny Cash"])])
    player(fake).play(track(), mode="queue")
    assert any(c[0] == "queue" for c in fake.calls)
    assert not any(c[0] == "start" for c in fake.calls)


def test_queue_mode_starts_playback_when_nothing_is_playing():
    """An empty queue on a silent device just sits there, which reads as
    'the demo is broken'."""
    fake = FakeSpotify(playing=False, search_items=[item("Hurt", ["Johnny Cash"])])
    player(fake).play(track(), mode="queue")
    assert any(c[0] == "start" for c in fake.calls)


def test_interrupt_mode_always_starts_playback():
    fake = FakeSpotify(playing=True, search_items=[item("Hurt", ["Johnny Cash"])])
    player(fake).play(track(), mode="interrupt")
    assert any(c[0] == "start" for c in fake.calls)


def test_device_falling_asleep_is_retried_once():
    """The most common real failure: the device slept between calls."""
    fake = FakeSpotify(
        playing=False,
        search_items=[item("Hurt", ["Johnny Cash"])],
        fail_first_play=SpotifyException(404, reason="NO_ACTIVE_DEVICE"),
    )
    player(fake).play(track())          #Should complete without an error
    assert any(c[0] == "start" for c in fake.calls), "should have retried"


def test_a_persistent_failure_surfaces_a_readable_message():
    class AlwaysFails(FakeSpotify):
        def start_playback(self, device_id=None, uris=None):
            raise SpotifyException(403, reason="PREMIUM_REQUIRED")

    p = player(AlwaysFails(search_items=[item("Hurt", ["Johnny Cash"])]))
    with pytest.raises(SpotifyError) as e:
        p.play(track())
    assert "premium" in str(e.value).lower()


def test_corpus_uri_bypasses_search_entirely():
    """Pasting a URI into the corpus is the documented fix for a bad match."""
    fake = FakeSpotify(playing=False)
    p = player(fake)
    p.play(track(uri="spotify:track:handpicked"), mode="interrupt")
    assert ("start", "d1", "spotify:track:handpicked") in fake.calls


# ------------------------------------------------- getting the right speaker --
#
# Both of these were found while filming: the song kept coming out of the
# laptop even though the phone was pinned and awake.


def two_devices(playing_on_laptop=False):
    return FakeSpotify(
        devices=[
            {"id": "laptop", "name": "DESKTOP-TPMTA8G", "type": "Computer",
             "is_active": True},
            {"id": "phone", "name": "iPhone", "type": "Smartphone",
             "is_active": False},
        ],
        playing=playing_on_laptop,
    )


def test_a_device_that_wakes_up_later_is_picked_up():
    """The chosen device used to be cached for the whole session. If the
    laptop was awake at startup and the phone was not, every song went to the
    laptop forever and waking the phone changed nothing."""
    fake = two_devices()
    p = player(fake, device_name="iPhone")

    assert p.ensure_device() == "phone"

    # Something else grabs it back, the way the desktop app does.
    for d in fake._devices:
        d["is_active"] = d["id"] == "laptop"
    p.device_id = "laptop"           # as if it had been cached earlier

    assert p.ensure_device() == "phone", "it kept using the stale device"


def test_a_vanished_device_is_replaced_rather_than_reused():
    fake = two_devices()
    p = player(fake, device_name="iPhone")
    p.device_id = "airpods-that-went-away"
    assert p.ensure_device() == "phone"


def test_the_sound_ends_up_on_the_pinned_device():
    """The whole point of pinning. Laptop playing, phone pinned: everything
    the player does must be aimed at the phone."""
    fake = two_devices(playing_on_laptop=True)
    p = player(fake, device_name="iPhone")

    p.play(Track(id="t", title="Bodies", artist="Drowning Pool", vibe=Vibe(),
                 uri="spotify:track:x"), mode="queue")

    aimed = [c[1] for c in fake.calls if c[0] in ("queue", "play", "transfer")]
    assert aimed, "it did nothing at all"
    assert all(d == "phone" for d in aimed), f"something was aimed elsewhere: {aimed}"


def test_it_knows_which_device_is_playing_not_just_that_one_is():
    """`is anything playing` and `is THIS playing` are different questions, and
    answering the wrong one is how a track queued for a phone comes out of a
    laptop: Spotify's queue follows the ACTIVE device, not the one named."""
    fake = two_devices(playing_on_laptop=True)
    p = player(fake, device_name="iPhone")

    assert p._is_playing() is True
    assert p._is_playing_on("laptop") is True
    assert p._is_playing_on("phone") is False


def test_it_still_queues_politely_on_the_right_speaker():
    """The point of queue mode is not disturbing what is already playing. That
    must survive the fix above."""
    fake = two_devices()
    for d in fake._devices:
        d["is_active"] = d["id"] == "phone"
    fake._playing = True
    p = player(fake, device_name="iPhone")

    p.play(Track(id="t", title="Bodies", artist="Drowning Pool", vibe=Vibe(),
                 uri="spotify:track:x"), mode="queue")

    assert [c for c in fake.calls if c[0] == "queue"], "it interrupted instead"


def test_a_missing_pinned_device_can_refuse_rather_than_wander():
    """Filming only. The default is still to make a sound, because silence is
    normally this project's one real bug. While a camera is running the
    trade inverts: a take where the audio came out of the laptop is worse
    than a take with none, because you find that one out in the edit."""
    fake = FakeSpotify(devices=[
        {"id": "laptop", "name": "DESKTOP-TPMTA8G", "type": "Computer",
         "is_active": True},
    ])

    lenient = player(fake, device_name="iPhone")
    assert lenient.ensure_device() == "laptop", "the default must still play"

    strict = player(fake, device_name="iPhone", require_device=True)
    with pytest.raises(SpotifyError) as e:
        strict.ensure_device()
    assert "not awake" in str(e.value)
    assert "DESKTOP-TPMTA8G" in str(e.value), "it should say what it CAN see"
