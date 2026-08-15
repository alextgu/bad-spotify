"""The corpus, when 47 tracks isn't enough.

The hand-curated list stays: it is vetted, famous, and never fails. But it is
47 tracks, so a long session repeats itself and every scene the rules don't
cover lands on the same handful. From outside that is indistinguishable from a
hardcoded lookup, which is exactly what it got accused of being.

**The obvious approach does not work.** Searching Spotify by genre tag and
ranking by popularity was the plan, and it died on contact: `genre:"ambient"`
returns deep catalogue nobody has heard of, and `popularity` is no longer
returned to new apps *at all* -- the field is absent from the response, along
with artist followers. Verified 14 Aug 2026. Spotify has been closing this
metadata since it shut off audio-features in 2024. So there is no fame signal
to rank by, and this project's first rule is that the judges must recognise
the song.

**So the model names the songs instead.** It is asked for well-known tracks
that would be maximally wrong for the moment, and each name is resolved to a
real URI through the same search that resolved 46 of the 47 corpus tracks.
Recognisability comes from asking for it rather than from measuring it, which
is the only option left -- and the model is a better judge of "would a room
recognise this" than a genre keyword ever was.

The cost is one model call, and it is only paid when the song is actually
about to change: the DJ's deadband gates this long before it runs.
"""
from __future__ import annotations

import json
import os
import threading
import time
from pathlib import Path

from ..log import notice as print  # stdout is reserved for data
from ..schemas import AntiVibe, SceneRead, Track, Vibe

_spotify_client = None
_spotify_tried = False
_genai_client = None
_genai_tried = False
_lock = threading.Lock()

#Keyed on the scene + what we're hunting for, so a held scene doesn't re-ask.
_cache: dict[str, list[Track]] = {}

#Name -> resolved URI, persisted. Resolving is the expensive half and the
#answer never changes, so it should survive a restart.
_RESOLVED_PATH = Path(__file__).resolve().parents[3] / "data" / "discovered_uris.json"
_resolved: dict[str, str] | None = None

#When Spotify rate-limits us it says how long for, and it is not short --
#measured 14 Aug 2026: a development-mode app hit the wall and was told to
#retry in 82,000 seconds (~23 hours). Hammering it while blocked can extend
#that, so once we are told to stop we stop, and the corpus carries the demo.
#This is precisely why the hand-curated 47 exist.
_blocked_until = 0.0

#A hard ceiling on how fast we are willing to ask, independent of what Spotify
#would tolerate. A development-mode app has a small rolling quota and the
#penalty for crossing it is ~23 hours with no way to appeal -- which, on the
#day, means no music. Budgeting is cheaper than being locked out: a demo needs
#a handful of lookups a minute, not hundreds.
#Now that only the winning track is ever resolved, a busy session needs a
#handful of searches a minute, not dozens. Set low deliberately: we should
#never be anywhere near Spotify's limit, and if we approach this one something
#has gone wrong upstream and should degrade to the corpus rather than push on.
MAX_SEARCHES_PER_MIN = 8
_recent_calls: list[float] = []


def _budget_ok() -> bool:
    now = time.time()
    with _lock:
        _recent_calls[:] = [t for t in _recent_calls if now - t < 60]
        if len(_recent_calls) >= MAX_SEARCHES_PER_MIN:
            return False
        _recent_calls.append(now)
    return True


#Public names for the player, which owns the only remaining search path.
budget_ok = _budget_ok


def rate_limited() -> bool:
    """Are we currently standing down?"""
    return time.time() < _blocked_until


def note_rate_limit(error: Exception) -> bool:
    """Record a rate-limit response so everything else backs off too."""
    return _rate_limited(error)

MODEL = os.environ.get("BADSPOTIFY_DISCOVER_MODEL", "gemini-3.5-flash-lite")
#Eight, because the shortlist should be a real argument rather than a top
#few. This used to be the latency ceiling -- each name costs a Spotify lookup,
#and in series six of them took ~4.4s -- but the lookups are independent and
#now run in parallel, so more names cost roughly nothing extra.
WANTED = 8
TIMEOUT_S = 6.0

#The axes an opposition can run along. The model picks whichever bites
#hardest for THIS moment rather than always reaching for the same one --
#"loud vs quiet" is only one way to be wrong, and the least interesting.
AXES = [
    "counter_genre",     # classical scene -> drill; a rave -> a hymn
    "counter_artist",    # the artist's rival, nemesis or antithesis
    "counter_lyrics",    # words that are unforgivable for what's happening
    "counter_rivalry",   # Barcelona's stadium -> the Real Madrid anthem
    "counter_era",       # a medieval hall -> hyperpop; a vintage diner -> EDM
    "counter_register",  # a seat of power -> a novelty song with no dignity
    "counter_energy",    # a funeral -> a stadium banger
    "counter_persona",   # a public figure -> the joke the internet already
                         # makes about their own publicised conduct
    "counter_season",    # a heatwave -> sleigh bells. The oldest wrong-song
                         # joke there is, and it still works
]

SUGGEST_SCHEMA = {
    "type": "object",
    "properties": {
        "axis": {"type": "string", "enum": AXES},
        "reading": {"type": "string"},
        "songs": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "artist": {"type": "string"},
                    "why": {"type": "string"},
                },
                "required": ["title", "artist", "why"],
            },
        },
    },
    "required": ["axis", "reading", "songs"],
}

PROMPT = """You pick music that is maximally WRONG for a moment.

The whole catalogue is available to you -- every song on streaming, not a
shortlist. Reach for the one that is *specifically* wrong for THIS moment,
not merely loud or merely sad.

THE MOMENT
  scene      : {setting}
  happening  : {activity}
  occasion   : {references}
  mood       : {mood}
  colours    : {colors}
  the agent is hunting for: {hunting}

FIRST, pick the axis of opposition that bites hardest here. Don't default to
energy -- that is the least interesting way to be wrong:

  counter_genre     the genre's natural enemy. A string quartet -> drill.
                    A rave -> a Gregorian chant. A country bar -> gabber.
  counter_artist    an artist's rival or antithesis. If a scene evokes one
                    artist, reach for the one they are measured against.
  counter_lyrics    words that are unforgivable for what is happening. A
                    break-up song at a wedding. A song about leaving, at an
                    arrival. The SOUND can even fit -- the words must not.
  counter_rivalry   rivalry between INSTITUTIONS, which is the sharpest joke
                    of all when it fits, because both sides are organisations
                    and neither is a kind of person.
                    Clubs: Camp Nou -> the Real Madrid anthem. A Lakers game
                    -> a Celtics anthem. Anfield -> the Everton song.
                    States, via their official symbols: the US national anthem
                    playing -> the Soviet or Chinese or North Korean anthem.
                    An anthem is a state's emblem, and swapping one for a
                    rival state's is the same joke as swapping club anthems.
                    Universities, corporations, armed services, cities and
                    console fandoms all work the same way.
  counter_era       the wrong century. A candlelit medieval hall -> hyperpop.
                    A 1950s diner -> aggressive EDM.
  counter_season    the wrong time of year, which everyone feels instantly
                    even when they cannot say why. A heatwave, a beach, a
                    sunburnt garden -> sleigh bells, Christmas number ones,
                    songs about snow. A blizzard or a dark February bus stop
                    -> "Walking on Sunshine", summer holiday anthems, steel
                    drums. Reach for this when the WEATHER or the time of year
                    is the loudest thing in the frame, and remember that
                    Christmas music is funny in July precisely because it is
                    so aggressively sincere about being in December.
  counter_register  gravity punctured. A seat of power, a solemn institution,
                    a formal ceremony -> a novelty song with no dignity at
                    all. The opposite of *serious* is *ridiculous*.
  counter_energy    a funeral -> a stadium banger. Use only when nothing
                    sharper applies.
  counter_persona   a famous person is on screen and the internet already has
                    a running joke about something they publicly DO. Play into
                    it. Taylor Swift -> songs about private jets, flying,
                    carbon. A tech founder mid-keynote -> songs about empty
                    promises or things collapsing. A politician mid-speech ->
                    the theme from a film that satirises exactly that pose.
                    The target is their publicised CONDUCT and public persona,
                    which is fair game and is what satire has always been.

THEN name {n} real, well-known songs along that axis.

THE TONE
You are not a music librarian. You are the friend who queues something at a
party specifically to see the look on someone's face. Internet-native,
meme-literate, deadpan. If a song has become a joke online, that is a feature
-- the room recognising the *bit* is half the laugh.

Aim the joke at the SITUATION: the pomp of the occasion, the self-seriousness
of the setting, the thing everyone in the room is pretending not to notice.
Puncture the moment, don't insult anyone standing in it. "This ceremony thinks
it is more important than it is" is the joke. A person's face is not.

Deadpan beats zany. The funniest pick is the one delivered completely
straight, as though it were the obvious professional choice.

WHAT MAKES THIS WORK
- **They must be famous.** The room has to recognise the song instantly or
  nothing lands. An obscure track that is technically the perfect opposite is
  a worse pick than a well-known one that is merely very wrong.
- Meme-tier tracks earn their place *because* everyone knows them, not despite
  it. Never Gonna Give You Up, Baby Shark, Sandstorm, Careless Whisper, the
  Nokia ringtone -- these are load-bearing.
- Real songs, on streaming, exact title and main performing artist.
- Vary them. Not {n} songs by one artist, not {n} of one genre.
- `why` must name the specific clash in a few words -- "wedding song at a
  divorce", "Madrid anthem in Barcelona". That line is shown to the audience
  and is most of the joke.

THE ONE HARD RULE
Aim at institutions, occasions, and what public figures publicly DO. Never at
what anyone IS.

  fair game : a club, a state, a university, a company, an armed service, a
              ceremony, a genre, an era, a celebrity's publicised conduct, the
              self-importance of an event. Rival anthems, rival teams, rival
              eras -- both sides are organisations.
  never     : anyone's race, ethnicity, religion, sex, body or appearance, and
              never a whole ethnic or religious group cast as the "opposite"
              of a country or an institution. A state has rivals; an ethnicity
              does not. "Their anthem vs our anthem" is a joke about two
              governments. "Their music vs our building" is just othering, and
              it is the oldest and least funny move there is.
  and       : members of the public who are not public figures are never the
              target. Puncture the occasion they are standing in, not them."""


def _spotify():
    global _spotify_client, _spotify_tried
    if _spotify_client is not None or _spotify_tried:
        return _spotify_client
    with _lock:
        _spotify_tried = True
        try:
            import spotipy
            from spotipy.oauth2 import SpotifyOAuth

            from ..players.spotify import SCOPES, TOKEN_CACHE

            if not os.environ.get("SPOTIFY_CLIENT_ID"):
                return None
            _spotify_client = spotipy.Spotify(
                auth_manager=SpotifyOAuth(
                    client_id=os.environ["SPOTIFY_CLIENT_ID"],
                    client_secret=os.environ["SPOTIFY_CLIENT_SECRET"],
                    redirect_uri=os.environ.get(
                        "SPOTIFY_REDIRECT_URI", "http://127.0.0.1:8888/callback"),
                    scope=SCOPES, cache_path=str(TOKEN_CACHE),
                    open_browser=False),
                requests_timeout=5)
        except Exception as e:
            print(f"[discover] Spotify unavailable ({e})")
            _spotify_client = None
    return _spotify_client


def _genai():
    global _genai_client, _genai_tried
    if _genai_client is not None or _genai_tried:
        return _genai_client
    with _lock:
        _genai_tried = True
        try:
            from google import genai
            if not os.environ.get("GOOGLE_API_KEY"):
                return None
            _genai_client = genai.Client()
        except Exception as e:
            print(f"[discover] suggestions unavailable ({e})")
            _genai_client = None
    return _genai_client


def _suggest(scene: SceneRead, anti: AntiVibe) -> tuple[str, str, list[dict]]:
    """Returns (axis, reading, songs). Empty on any failure."""
    client = _genai()
    if client is None:
        return "", "", []
    try:
        from google.genai import types

        prompt = PROMPT.format(
            setting=scene.setting or "unknown",
            activity=scene.activity or "unknown",
            references=", ".join(scene.references) or "unknown",
            mood=scene.mood_label or "unknown",
            colors=", ".join(scene.dominant_colors[:4]) or "unknown",
            hunting=", ".join(anti.target_genres[:8]) or "the opposite of this",
            n=WANTED)
        resp = client.models.generate_content(
            model=MODEL,
            contents=[types.Content(role="user",
                                    parts=[types.Part.from_text(text=prompt)])],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=SUGGEST_SCHEMA))
        d = json.loads(resp.text) or {}
        return d.get("axis", ""), d.get("reading", ""), d.get("songs") or []
    except Exception as e:
        print(f"[discover] suggestion failed: {str(e)[:90]}")
        return "", "", []


def _slug(text: str) -> str:
    keep = [c if c.isalnum() else "-" for c in (text or "").lower()]
    return "".join(keep).strip("-")[:40] or "unknown"


def _rate_limited(error: Exception) -> bool:
    """Spotify says how long to stay away. Believe it."""
    global _blocked_until
    msg = str(error)
    if "rate/request limit" not in msg and "429" not in msg:
        return False
    seconds = 3600.0
    for token in msg.replace(":", " ").split():
        if token.isdigit() and int(token) > 10:
            seconds = float(token)
            break
    _blocked_until = time.time() + min(seconds, 86400)
    print(f"[discover] Spotify rate limit; standing down for "
          f"{seconds / 3600:.1f}h. The corpus still works.")
    return True


def _load_resolved() -> dict[str, str]:
    global _resolved
    if _resolved is None:
        try:
            _resolved = json.loads(_RESOLVED_PATH.read_text(encoding="utf-8"))
        except Exception:
            _resolved = {}
    return _resolved


def _save_resolved() -> None:
    try:
        _RESOLVED_PATH.parent.mkdir(parents=True, exist_ok=True)
        _RESOLVED_PATH.write_text(json.dumps(_resolved or {}, indent=1,
                                             sort_keys=True), encoding="utf-8")
    except Exception as e:
        print(f"[discover] could not save resolved uris: {str(e)[:60]}")


def _resolve(sp, title: str, artist: str):
    """Name -> real Spotify track, using the matcher that vetted the corpus.

    Returns a `Match` (uri/title/artist), not a raw API dict -- it has already
    rejected karaoke covers, tribute bands and wrong artists, which is exactly
    the filtering a model-supplied name needs.
    """
    from ..players.spotify_match import Match, best_match, search_queries

    cache = _load_resolved()
    key = f"{title.lower()}|{artist.lower()}"
    hit = cache.get(key)
    if hit == "":
        return None                      #known miss; don't spend a request
    if hit:
        return Match(uri=hit, title=title, artist=artist, score=1.0)

    if time.time() < _blocked_until:
        return None

    for query in search_queries(title, artist):
        if not _budget_ok():
            print("[discover] search budget spent for this minute; "
                  "falling back to the corpus")
            return None
        try:
            res = sp.search(q=query, type="track", limit=10)
        except Exception as e:
            if _rate_limited(e):
                return None
            return None
        items = (res.get("tracks") or {}).get("items") or []
        winner, _ = best_match(items, title, artist)
        if winner:
            cache[key] = winner.uri
            _save_resolved()
            return winner
    cache[key] = ""                      #remember the miss too
    _save_resolved()
    return None


def search(scene: SceneRead, anti: AntiVibe, target: Vibe | None = None) -> list[Track]:
    """Well-known tracks for this moment, from outside the 47.

    Never raises. Discovery is a bonus on top of a corpus that already works,
    so a bad network or a missing key costs the bonus and nothing else.
    """
    key = f"{(scene.setting or '')[:60]}|{','.join(anti.target_genres[:5])}"
    if key in _cache:
        return _cache[key]

    axis, reading, songs = _suggest(scene, anti)
    songs = [s for s in songs[:WANTED] if (s.get("title") or "").strip()]
    if songs:
        print(f"[discover] {axis or 'opposition'}: {reading}"[:160])

    #NOTHING here talks to Spotify.
    #
    #The first version resolved every suggested name to a URI right here --
    #eight names, up to two query variants each, fourteen searches measured for
    #a single scene. Then the judge picked one and the other seven lookups were
    #thrown away. That is how the first app reached its rate limit and lost a
    #day, and a development-mode quota cannot afford it.
    #
    #So candidates stay unresolved names. `SpotifyPlayer.resolve()` already
    #turns a title and artist into a URI, with its own cache, and it runs on
    #the WINNER only -- one search per song actually played, or zero when the
    #cache has seen it. Fourteen becomes one.
    out: list[Track] = []
    seen: set[str] = set()
    for song in songs:
        title = (song.get("title") or "").strip()
        artist = (song.get("artist") or "").strip()
        key_ta = f"{title.lower()}|{artist.lower()}"
        if key_ta in seen:
            continue
        seen.add(key_ta)
        out.append(Track(
            #Stable and prefixed: the player caches resolutions against this
            #id, and `played_ids` must never confuse one with a corpus track.
            id=f"sp:{_slug(title)}-{_slug(artist)}",
            title=title,
            artist=artist or "someone",
            genres=[anti.target_genres[0]] if anti.target_genres else [],
            #Inherited from the target: we asked for something maximally wrong
            #for this scene and this is the answer, so it sits where the target
            #sits. Spotify no longer exposes anything to measure it with.
            vibe=target or anti.target,
            tags=["discovered"] + anti.target_genres[:2],
            #Asked for, not measured -- the prompt demands famous songs and
            #`popularity` no longer exists. Deliberately not 1.0: this is a
            #claim, and the corpus values were at least chosen by a human.
            recognisability=0.85,
            #No URI on purpose -- the player resolves the winner, and only the
            #winner. See the note above.
            uri=None,
            why=(song.get("why") or "").strip(),
        ))

    _cache[key] = out
    return out


def clear_cache() -> None:
    _cache.clear()
