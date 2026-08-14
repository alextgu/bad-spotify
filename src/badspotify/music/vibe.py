"""The antipode engine. This is the soul of the project.

Two ideas, deliberately kept separate:

1. GEOMETRY gives you defensibility. Scene and track both live in the same
   5-dim vibe cube, so "opposite" is reflection through the centre. It is
   deterministic, offline, instant, and explainable to a judge in one slide.

2. CULTURE gives you the punchline. The true opposite of "calm sunny park"
   is not statistically antipodal -- it is funeral doom, or a Christmas song
   in August, or Yakety Sax at a solemn moment. Geometry cannot know that.

We use geometry to shortlist and culture to choose. Never one alone.
"""
from __future__ import annotations

import datetime as _dt
from dataclasses import dataclass

from ..schemas import VIBE_DIMS, AntiVibe, Meter, SceneRead, TempoFeel, Vibe


def reflect(v: Vibe) -> Vibe:
    """Reflect through the centre of the cube -- the exact opposite on every axis.

    This used to take a 0-1 "how far to go" parameter. It was removed: the
    product reads a mood and inverts a mood, and a dial labelled "how far past
    inappropriate to go" was describing something the system doesn't do. How
    wrong the result turned out is now MEASURED afterwards (`Verdict.mismatch`)
    rather than requested up front.
    """
    return Vibe(**{dim: 1.0 - getattr(v, dim) for dim in VIBE_DIMS})


def mismatch(scene: Vibe, track: Vibe) -> float:
    """How far apart the moment and the music actually are, normalised 0-1."""
    from ..schemas import MAX_VIBE_DISTANCE
    return min(1.0, scene.distance(track) / MAX_VIBE_DISTANCE)


def dominant_axis(v: Vibe) -> tuple[str, float]:
    """The axis the scene commits to hardest. Invert this one to the hilt --
    that is where the comedy is sharpest."""
    best, best_dev = VIBE_DIMS[0], 0.0
    for dim in VIBE_DIMS:
        dev = abs(getattr(v, dim) - 0.5)
        if dev > best_dev:
            best, best_dev = dim, dev
    return best, best_dev


def sharpen(target: Vibe, axis: str) -> Vibe:
    """Push one axis all the way to the wall."""
    d = target.model_dump()
    d[axis] = 1.0 if d[axis] >= 0.5 else 0.0
    return Vibe(**d)


#Tags used to find culturally inappropriate songs for a scene
#These rules define the joke

TABOO_RULES: list[tuple[tuple[str, ...], list[str], str]] = [
    (("park", "garden", "sunlit", "sunny", "picnic", "beach"),
     ["funeral doom", "death metal", "drone", "noise", "despair", "dread"],
     "serenity punished with maximum heaviness"),
    (("library", "study", "quiet", "hushed", "reading", "exam"),
     ["gabber", "rave", "brutal", "screaming", "noise", "assault"],
     "silence violated"),
    (("birthday", "party", "celebration", "wedding", "cake", "graduation"),
     ["funeral", "death", "grief", "despair", "heartbreak"],
     "joy undercut by mortality"),
    (("funeral", "memorial", "grief", "hospital", "solemn", "vigil"),
     ["novelty", "meme", "upbeat", "line dance", "benny hill"],
     "grief undercut by novelty"),
    (("garage", "night", "alone", "dark", "empty", "alley", "uneasy"),
     ["benny hill", "novelty", "children", "undermining", "chase"],
     "dread deflated into farce"),
    (("gym", "run", "training", "workout", "sprint"),
     ["ambient", "weightless", "glacial", "funeral doom", "calm"],
     "momentum killed"),
    (("coffee", "cafe", "restaurant", "queue", "line", "shop", "commute"),
     ["harsh noise", "unlistenable", "atonal", "punishment"],
     "the mundane made unbearable"),
    (("meeting", "office", "desk", "work", "presentation", "interview"),
     ["seduction", "sax", "awkward", "rage", "screaming"],
     "professionalism sabotaged"),
    (("date", "dinner", "romantic", "candle"),
     ["death metal", "brutal", "growling", "funeral"],
     "romance detonated"),
]


def contextual_taboo(scene: SceneRead, now: _dt.date | None = None) -> tuple[list[str], list[str], str]:
    """Return (boost_tags, ban_tags, rationale) for this scene."""
    haystack = " ".join([
        scene.setting.lower(), scene.activity.lower(), scene.mood_label.lower(),
    ])
    boost: list[str] = []
    reasons: list[str] = []
    for keywords, tags, why in TABOO_RULES:
        if any(k in haystack for k in keywords):
            boost.extend(tags)
            reasons.append(why)

    #Treats Christmas music as inappropriate outside December
    today = now or _dt.date.today()
    if not boost and today.month not in (12,):
        boost.append("wrong-season")
        reasons.append("christmas music outside december")

    #Removes music that fits the scene
    ban: list[str] = []
    if scene.vibe.arousal < 0.25:
        ban.append("ambient")
    if scene.vibe.valence > 0.8:
        ban.extend(["upbeat", "feelgood", "celebration"])

    seen: set[str] = set()
    boost = [t for t in boost if not (t in seen or seen.add(t))]
    return boost, ban, "; ".join(reasons) or "no specific taboo, pure geometry"


def build_antivibe(scene: SceneRead,
                   strategy: str = "genre_antipode") -> AntiVibe:
    target = reflect(scene.vibe)
    axis, dev = dominant_axis(scene.vibe)
    if dev > 0.25:
        target = sharpen(target, axis)

    boost, ban, why = contextual_taboo(scene)
    return AntiVibe(
        target=target,
        target_genres=boost,
        banned_genres=ban,
        strategy=strategy,
        rationale=(
            f"scene reads {scene.mood_label} (dominant axis '{axis}', "
            f"deviation {dev:.2f}); {why}"
        ),
    )


#Helper functions

TEMPO_TO_AROUSAL = {
    TempoFeel.STILL: 0.05, TempoFeel.SLOW: 0.25, TempoFeel.WALKING: 0.5,
    TempoFeel.BRISK: 0.75, TempoFeel.FRANTIC: 0.95,
}


def meter_clash(scene_meter: Meter, track_tags: list[str]) -> float:
    """Your 'consistent vs inconsistent' axis, as a score in 0..1."""
    irregular_markers = {"5/4", "irregular", "atonal", "chaotic", "free jazz"}
    track_is_irregular = any(t in irregular_markers for t in track_tags)
    if scene_meter == Meter.STEADY and track_is_irregular:
        return 1.0
    if scene_meter == Meter.IRREGULAR and not track_is_irregular:
        return 0.6
    return 0.0
