"""Three candidate generators that disagree with each other on purpose.

THIS is where fan-out earns its keep. Not one agent per output field --
one generator per *theory of what makes music wrong*:

  genre_antipode : wrong on every axis at once (geometric opposition)
  tempo_clash    : wrong specifically in energy/pulse (rhythmic sabotage)
  lyrical_irony  : wrong in meaning, regardless of sound (semantic sabotage)

They produce genuinely different shortlists. A judge then picks the funniest.
That is a judge-panel pattern with real diversity, not parallelism theatre.
"""
from __future__ import annotations

from typing import Callable

from ..schemas import AntiVibe, Candidate, SceneRead, Track
from .corpus import Corpus
from .vibe import TEMPO_TO_AROUSAL, meter_clash
from ..log import notice as print  # stdout is reserved for data

Strategy = Callable[[SceneRead, AntiVibe, Corpus, set, int], list[Candidate]]


def _recog_weight(t: Track) -> float:
    """A devastating song nobody recognises is not devastating. Weight, don't filter."""
    return 0.55 + 0.45 * t.recognisability


def genre_antipode(scene: SceneRead, anti: AntiVibe, corpus: Corpus,
                   exclude: set, n: int) -> list[Candidate]:
    """Maximum distance from the scene, minimum distance to the anti-target."""
    scored = []
    for t in corpus.filter(exclude, anti.banned_genres):
        to_target = t.vibe.distance(anti.target)
        from_scene = t.vibe.distance(scene.vibe)
        # close to the opposite AND far from the truth
        score = (from_scene * 0.6 + (1.0 - min(to_target, 1.0)) * 0.4) * _recog_weight(t)
        scored.append(Candidate(
            track=t, strategy="genre_antipode", raw_distance=score,
            notes=f"d(scene)={from_scene:.2f} d(target)={to_target:.2f}",
        ))
    scored.sort(key=lambda c: c.raw_distance, reverse=True)
    return scored[:n]


def tempo_clash(scene: SceneRead, anti: AntiVibe, corpus: Corpus,
                exclude: set, n: int) -> list[Candidate]:
    """Ignore mood entirely. Be wrong about speed and pulse."""
    scene_arousal = TEMPO_TO_AROUSAL.get(scene.tempo_feel, scene.vibe.arousal)
    scored = []
    for t in corpus.filter(exclude, anti.banned_genres):
        delta = abs(t.vibe.arousal - scene_arousal)
        clash = meter_clash(scene.meter, t.tags)
        score = (delta * 0.75 + clash * 0.25) * _recog_weight(t)
        scored.append(Candidate(
            track=t, strategy="tempo_clash", raw_distance=score,
            notes=f"arousal gap {delta:.2f}, meter clash {clash:.2f}",
        ))
    scored.sort(key=lambda c: c.raw_distance, reverse=True)
    return scored[:n]


def lyrical_irony(scene: SceneRead, anti: AntiVibe, corpus: Corpus,
                  exclude: set, n: int) -> list[Candidate]:
    """Be wrong about MEANING. A cheerful song at a funeral is sonically
    'close' on some axes and still the worst thing you could possibly do."""
    boost = set(anti.target_genres)
    scored = []
    for t in corpus.filter(exclude, anti.banned_genres):
        overlap = len(boost & (set(t.tags) | set(t.genres)))
        if overlap == 0:
            continue
        score = (min(overlap / 2.0, 1.0) * 0.8 + t.vibe.distance(scene.vibe) * 0.2)
        score *= _recog_weight(t)
        scored.append(Candidate(
            track=t, strategy="lyrical_irony", raw_distance=score,
            notes=f"taboo hits: {sorted(boost & (set(t.tags) | set(t.genres)))}",
        ))
    scored.sort(key=lambda c: c.raw_distance, reverse=True)
    return scored[:n]


REGISTRY: dict[str, Strategy] = {
    "genre_antipode": genre_antipode,
    "tempo_clash": tempo_clash,
    "lyrical_irony": lyrical_irony,
}


def generate(scene: SceneRead, anti: AntiVibe, corpus: Corpus,
             names: list[str], exclude: set | None = None,
             per_strategy: int = 4) -> list[Candidate]:
    exclude = exclude or set()
    out: list[Candidate] = []
    for name in names:
        fn = REGISTRY.get(name)
        if not fn:
            continue
        try:
            out.extend(fn(scene, anti, corpus, exclude, per_strategy))
        except Exception as e:
            print(f"[strategy] {name} failed: {e}")

    # dedupe, keeping the strongest claim on each track
    best: dict[str, Candidate] = {}
    for c in out:
        cur = best.get(c.track.id)
        if cur is None or c.raw_distance > cur.raw_distance:
            best[c.track.id] = c
    return sorted(best.values(), key=lambda c: c.raw_distance, reverse=True)
