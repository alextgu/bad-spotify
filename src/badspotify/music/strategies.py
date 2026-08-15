"""Candidate generators that disagree with each other on purpose.

THIS is where fan-out earns its keep. Not one agent per output field --
one generator per *theory of what makes music wrong*:

  genre_antipode : wrong on every axis at once (geometric opposition)
  tempo_clash    : wrong specifically in energy/pulse (rhythmic sabotage)
  lyrical_irony  : wrong in meaning, regardless of sound (semantic sabotage)
  semantic_opposite: wrong by inverting setting traits into a genre

They produce genuinely different shortlists. A judge then picks the funniest.
That is a judge-panel pattern with real diversity, not parallelism theatre.
"""
from __future__ import annotations

from typing import Callable

from ..schemas import MAX_VIBE_DISTANCE, AntiVibe, Candidate, SceneRead, Track
from . import discover
from .corpus import Corpus
from .vibe import TEMPO_TO_AROUSAL, meter_clash
from ..log import notice as print  # stdout is reserved for data

Strategy = Callable[[SceneRead, AntiVibe, Corpus, set, int], list[Candidate]]


def _recog_weight(t: Track) -> float:
    """A devastating song nobody recognises is not devastating. Weight, don't filter.

    This was `0.55 + 0.45 * r`, a 1.8x swing applied AFTER scoring -- enough to
    overturn the theory that produced the score. Measured across 24 varied
    scenes it collapsed the corpus: 8 distinct winners out of 47 tracks, the
    top 3 taking 67% of scenes, and "All I Want for Christmas Is You" winning
    the yoga class, the car wash, the dentist and the monastery alike. From
    outside that is indistinguishable from a hardcoded lookup.

    Fame should break a tie between two equally wrong answers, not decide
    which answer is wrong. 1.25x does that.
    """
    return 0.80 + 0.20 * t.recognisability


def genre_antipode(scene: SceneRead, anti: AntiVibe, corpus: Corpus,
                   exclude: set, n: int) -> list[Candidate]:
    """Maximum distance from the scene, minimum distance to the anti-target."""
    scored = []
    for t in corpus.filter(exclude, anti.banned_genres):
        to_target = t.vibe.distance(anti.target)
        from_scene = t.vibe.distance(scene.vibe)
        #Scores each track using the target mood and scene mood
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
        hits = boost & (set(t.tags) | set(t.genres))
        overlap = len(hits)
        if overlap == 0:
            continue
        #Don't saturate at two hits. It used to, so a large share of the corpus
        #tied at exactly 0.8 and recognisability silently decided every one of
        #them -- which is how one Christmas song came to win a monastery, a
        #dentist and a football stadium. Four hits should beat two.
        score = (min(overlap / 4.0, 1.0) * 0.7
                 + t.vibe.distance(scene.vibe) / 2.24 * 0.3)
        score *= _recog_weight(t)
        scored.append(Candidate(
            track=t, strategy="lyrical_irony", raw_distance=score,
            notes=f"taboo hits: {sorted(hits)}",
        ))
    scored.sort(key=lambda c: c.raw_distance, reverse=True)
    return scored[:n]


def _genre_affinity(targets: set[str], track: Track) -> float:
    genres = {genre.lower() for genre in track.genres}
    if targets & genres:
        return 1.0
    if any(target in genre or genre in target
           for target in targets for genre in genres):
        return 0.85
    if targets & {tag.lower() for tag in track.tags}:
        return 0.7
    return 0.0


def semantic_opposite(scene: SceneRead, anti: AntiVibe, corpus: Corpus,
                      exclude: set, n: int) -> list[Candidate]:
    """Map observed setting traits through their opposites to a local genre."""
    targets = {genre.lower() for genre in scene.opposite_genres}
    if not targets:
        return []

    observed = ", ".join(scene.setting_attributes) or "setting"
    opposite = ", ".join(scene.opposite_attributes) or "its opposite"
    scored = []
    for track in corpus.filter(exclude, anti.banned_genres):
        affinity = _genre_affinity(targets, track)
        if not affinity:
            continue
        distance = track.vibe.distance(scene.vibe) / MAX_VIBE_DISTANCE
        score = (1.05 + 0.20 * affinity + 0.12 * distance) * _recog_weight(track)
        scored.append(Candidate(
            track=track, strategy="semantic_opposite", raw_distance=score,
            notes=f"{observed} -> {opposite} -> {', '.join(sorted(targets))}",
        ))
    scored.sort(key=lambda candidate: candidate.raw_distance, reverse=True)
    return scored[:n]


#What music belongs at an occasion. Being wrong needs a notion of right, and
#the acoustic strategies have none, so the
#worst they can manage is "loud where it should be quiet". This is what lets
#the agent be wrong about the EVENT.
#
#Keys are things `SceneRead.references` actually contains: occasions, settings
#and registers. Never anything about the people present -- see the note on
#that field, and `_IDENTITY_TERMS` in perceive/scene.py, which enforces it.
OCCASION_EXPECTS: dict[str, set[str]] = {
    "funeral":            {"funeral", "grief", "solemn", "classical", "hymn"},
    "mourning":           {"funeral", "grief", "solemn"},
    "hospital":           {"calm", "ambient", "quiet"},
    "wedding":            {"celebration", "romance", "earnest", "soul", "pop"},
    "celebration":        {"celebration", "upbeat", "party", "disco", "pop"},
    "party":              {"party", "upbeat", "celebration", "dance", "pop"},
    "birthday":           {"celebration", "children", "novelty", "upbeat"},
    "children's party":   {"children", "novelty", "celebration", "upbeat"},
    "religious ceremony": {"hymn", "classical", "solemn", "earnest"},
    "study":              {"calm", "ambient", "classical", "quiet"},
    "library":            {"calm", "ambient", "quiet"},
    "quiet public space": {"calm", "ambient", "quiet"},
    "date night":         {"romance", "seduction", "soul", "jazz", "earnest"},
    "restaurant":         {"jazz", "calm", "soul", "ambient"},
    "romance":            {"romance", "seduction", "soul", "earnest"},
    "gym":                {"rage", "upbeat", "epic", "rock", "hip hop", "eurodance"},
    "workout":            {"rage", "upbeat", "epic", "rock"},
    "sport":              {"epic", "upbeat", "rock", "rage"},
    "workplace":          {"calm", "ambient", "quiet"},
    "meeting":            {"calm", "ambient", "quiet"},
    "formal":             {"classical", "jazz", "solemn", "earnest"},
    "commute":            {"pop", "calm", "ambient"},
    "cafe":               {"jazz", "calm", "soul", "ambient"},
    "outdoors":           {"calm", "ambient", "earnest", "folk"},
    "park":               {"calm", "ambient", "earnest"},
    "leisure":            {"calm", "pop", "earnest"},
    "night":              {"ambient", "calm", "seduction"},
    "deserted place":     {"ambient", "calm"},
    "car park":           {"ambient", "calm"},
    "queue":              {"pop", "calm", "ambient"},
    "rave":               {"rave", "eurodance", "dance", "upbeat"},
    "festival":           {"party", "upbeat", "celebration", "rock"},
    "graduation":         {"celebration", "epic", "earnest"},
    "funeral procession": {"funeral", "grief", "solemn"},
}


def register_clash(scene: SceneRead, anti: AntiVibe, corpus: Corpus,
                   exclude: set, n: int) -> list[Candidate]:
    """Wrong about the OCCASION, not about the sound.

    The acoustic strategies ask "what does this moment sound like?". This asks
    "what does this moment MEAN, and what would be unforgivable at it?" --
    which is why it can find a children's song for a funeral, a track the
    acoustic strategies would never rank highly because a nursery rhyme is
    not sonically extreme in any direction.

    It reads `scene.references`: the occasion and register, never anything
    about the people present. That distinction is the whole reason the field
    is scoped the way it is.
    """
    refs = [r.lower() for r in (scene.references or [])]
    if not refs:
        return []                      #nothing to be wrong about; stay quiet

    expected: set[str] = set()
    matched: list[str] = []
    for ref in refs:
        for occasion, belongs in OCCASION_EXPECTS.items():
            #Substring both ways: "diwali celebration" should hit "celebration".
            if occasion in ref or ref in occasion:
                expected |= belongs
                matched.append(occasion)
    if not expected:
        return []

    scored = []
    for t in corpus.filter(exclude, anti.banned_genres):
        vocab = set(t.tags) | {g.lower() for g in t.genres}
        belongs = len(vocab & expected)
        if belongs:
            continue                   #this is what SHOULD play. Not our job.

        #How emphatically does this track belong somewhere ELSE? That is the
        #whole idea: a children's song at a funeral is funnier than a track
        #that merely fails to fit, because it audibly belongs at a different
        #event. Ranking on "doesn't fit" alone is a constant -- every survivor
        #scores the same -- which quietly turned this into a weaker
        #genre_antipode that proposed exactly the same shortlist.
        elsewhere = 0
        home = ""
        for occasion, belongs_there in OCCASION_EXPECTS.items():
            if occasion in matched:
                continue
            hits = len(vocab & belongs_there)
            if hits > elsewhere:
                elsewhere, home = hits, occasion
        if not elsewhere:
            continue                   #belongs nowhere in particular; no joke

        score = (min(elsewhere / 3.0, 1.0) * 0.75
                 + t.vibe.distance(scene.vibe) / 2.24 * 0.25)
        score *= _recog_weight(t)
        scored.append(Candidate(
            track=t, strategy="register_clash", raw_distance=score,
            notes=f"belongs at {home}, not at "
                  f"{', '.join(sorted(set(matched))[:2])}",
        ))
    scored.sort(key=lambda c: c.raw_distance, reverse=True)
    return scored[:n]


def catalogue_dive(scene: SceneRead, anti: AntiVibe, corpus: Corpus,
                   exclude: set, n: int) -> list[Candidate]:
    """The one strategy that isn't limited to the 47.

    It ignores `corpus` entirely and searches Spotify for whatever the antivibe
    is hunting for. That is allowed -- a strategy is a theory of wrongness, not
    a way of ranking a fixed list -- and it is the only way the agent stops
    repeating itself in a long session.

    Its picks are held to a slightly higher bar than corpus ones: a corpus
    track was chosen by a human and has a vetted vibe, while a discovered
    track only *claims* to be what we searched for. `popularity` is real
    though, so recognisability here is measured rather than guessed.
    """
    found = discover.search(scene, anti)
    if not found:
        return []

    scored = []
    for rank, t in enumerate(found):
        if t.id in exclude:
            continue
        if set(t.genres) & set(anti.banned_genres):
            continue
        #The vibe is inherited from the target, so vibe distance would be the
        #same number for every result and tells us nothing. Rank on how well
        #known it is instead -- which is the thing the corpus never measured.
        #
        #Scaled to compete with the corpus strategies rather than to be polite
        #about it. First pass capped these at 0.9 while genre_antipode reaches
        #~1.3, so a discovered track won 1 scene in 12 and the whole catalogue
        #was decoration. A well-known track that genuinely matches the target
        #should beat a corpus track that merely scores well on geometry.
        #The model returned these in its own order of preference, so respect
        #it -- there is nothing else to rank on. Scaled to compete with the
        #corpus strategies rather than to be polite about it: a first pass
        #capped these below genre_antipode's range and a discovered track won
        #1 scene in 12, which made the whole catalogue decoration.
        #Pitched to compete with the corpus strategies, not to replace them.
        #At 1.15 it won all 12 scenes in testing and the other strategies stopped
        #mattering -- and their disagreement is half of why the reasoning is
        #worth showing. This overlaps genre_antipode's range instead, so the
        #corpus still wins when it has a genuinely better answer.
        score = 1.03 - 0.05 * rank
        scored.append(Candidate(
            track=t, strategy="catalogue_dive", raw_distance=score,
            #The specific clash, not a description of the mechanism. "Madrid
            #anthem in Barcelona" is the joke; "found on Spotify" is plumbing.
            notes=t.why or "a well-known song that would be wrong here",
        ))
    scored.sort(key=lambda c: c.raw_distance, reverse=True)
    return scored[:n]


REGISTRY: dict[str, Strategy] = {
    "genre_antipode": genre_antipode,
    "tempo_clash": tempo_clash,
    "lyrical_irony": lyrical_irony,
    "semantic_opposite": semantic_opposite,
    "register_clash": register_clash,
    "catalogue_dive": catalogue_dive,
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

    #Keeps the final choices aligned with the displayed music theme -- the HUD
    #says what it is hunting for, so the pick should plausibly be that.
    #
    #But only when the theme is broad enough to be a filter rather than a
    #verdict. A narrow theme matched a handful of tracks, so this quietly
    #became the decision: everything else was discarded and the judge chose
    #from one survivor. Below three, coherence isn't worth losing the argument.
    theme = set(anti.target_genres)
    themed = [
        candidate for candidate in out
        if theme & (set(candidate.track.tags) | set(candidate.track.genres))
    ]
    if len(themed) >= 3:
        out = themed

    #Keeps the strongest candidate entry for each track
    best: dict[str, Candidate] = {}
    for c in out:
        cur = best.get(c.track.id)
        if cur is None or c.raw_distance > cur.raw_distance:
            best[c.track.id] = c
    return sorted(best.values(), key=lambda c: c.raw_distance, reverse=True)
