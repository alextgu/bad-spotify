"""Matching our corpus tracks to real Spotify results.

Kept separate from the player and free of any network calls so it can be
unit tested. This is the part that quietly ruins a demo: search for
"Hurt / Johnny Cash" and Spotify will happily hand back a karaoke version,
a tribute band, or a live recording from 1997 that opens with ninety
seconds of crowd noise. None of those are the joke.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

# Words that mean "this is not the recording you meant". Weighted, because
# a live version is a mild problem and a karaoke version is a fatal one.
JUNK_MARKERS: dict[str, float] = {
    "karaoke": 1.0,
    "tribute": 1.0,
    "made famous by": 1.0,
    "in the style of": 1.0,
    "originally performed": 1.0,
    "cover version": 0.9,
    "instrumental": 0.7,
    "lullaby": 0.8,
    "8-bit": 0.8,
    "8 bit": 0.8,
    "music box": 0.8,
    "sped up": 0.6,
    "slowed": 0.6,
    "remix": 0.4,
    "live": 0.35,
    "demo": 0.3,
    "rerecorded": 0.3,
    "re-recorded": 0.3,
}

# Decoration that is not part of the title and should not count against a match.
NOISE_RE = re.compile(
    r"\s*[\(\[\-–—]\s*"
    r"(remaster(ed)?|\d{4}\s*remaster|mono|stereo|deluxe|expanded|"
    r"bonus track|radio edit|single version|album version|"
    r"from [^)\]]+|feat\.?[^)\]]*|featuring[^)\]]*)"
    r"\s*[\)\]]?\s*",
    re.I,
)


def normalise(text: str) -> str:
    text = unicodedata.normalize("NFKD", text or "")
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = NOISE_RE.sub(" ", text.lower())
    text = re.sub(r"[^\w\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def token_overlap(a: str, b: str) -> float:
    """Fraction of the shorter token set that appears in the other."""
    ta, tb = set(normalise(a).split()), set(normalise(b).split())
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / min(len(ta), len(tb))


def junk_penalty(*fields: str) -> float:
    blob = " ".join(normalise(f) for f in fields if f)
    return max((w for marker, w in JUNK_MARKERS.items() if marker in blob), default=0.0)


@dataclass
class Match:
    uri: str
    title: str
    artist: str
    score: float
    duration_s: float | None = None
    rejected: str | None = None

    @property
    def ok(self) -> bool:
        return self.rejected is None


def score_result(item: dict, want_title: str, want_artist: str) -> Match:
    """Score one Spotify search result against what we actually asked for."""
    got_title = item.get("name", "")
    artists = [a.get("name", "") for a in item.get("artists", [])]
    got_artist = ", ".join(artists)
    uri = item.get("uri", "")
    dur = (item.get("duration_ms") or 0) / 1000 or None

    title_score = token_overlap(want_title, got_title)
    # Any credited artist may carry the match -- compilations and classical
    # recordings list the composer alongside performers.
    artist_score = max((token_overlap(want_artist, a) for a in artists), default=0.0)
    penalty = junk_penalty(got_title, got_artist)

    m = Match(uri=uri, title=got_title, artist=got_artist,
              score=0.0, duration_s=dur)

    # "Various" in our corpus means we never knew the artist. Don't hold
    # Spotify to a name we invented.
    artist_is_wildcard = normalise(want_artist) in {"various", "various artists", ""}

    if not artist_is_wildcard and artist_score < 0.34:
        m.rejected = f"artist mismatch (wanted {want_artist!r}, got {got_artist!r})"
        return m
    if title_score < 0.5:
        m.rejected = f"title mismatch (wanted {want_title!r}, got {got_title!r})"
        return m
    if penalty >= 0.9:
        m.rejected = f"looks like a karaoke/tribute recording: {got_title!r}"
        return m

    weight_artist = 0.0 if artist_is_wildcard else 0.4
    weight_title = 1.0 - weight_artist
    m.score = round(title_score * weight_title + artist_score * weight_artist - penalty, 4)
    return m


def best_match(items: list[dict], want_title: str, want_artist: str) -> tuple[Match | None, list[Match]]:
    """Return (winner or None, all scored candidates) -- the rejects are kept
    so the setup report can say *why* nothing matched."""
    scored = [score_result(i, want_title, want_artist) for i in items or []]
    viable = [m for m in scored if m.ok]
    if not viable:
        return None, scored
    viable.sort(key=lambda m: m.score, reverse=True)
    return viable[0], scored


def search_queries(title: str, artist: str) -> list[str]:
    """Progressively looser queries. Field-scoped first (precise), then bare."""
    queries = []
    if artist and normalise(artist) not in {"various", "various artists"}:
        queries.append(f'track:"{title}" artist:"{artist}"')
        queries.append(f"{title} {artist}")
    queries.append(f'track:"{title}"')
    queries.append(title)
    return queries
