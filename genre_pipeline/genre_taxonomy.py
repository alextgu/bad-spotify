"""
Genre taxonomy + feature profiles.

CURRENT STATE (v1 / hackathon MVP): a flat FIRST LAYER of the eventual
p-adic tree. Each genre here is a direct child of the root -- code is
just the genre's own name, no subgenre relationships needed. This
sidesteps the "we don't have scraped subgenre relationship data" problem
entirely: broad, maximally-recognizable genres, fully hand-anchored, no
missing fields.

FUTURE (v2): a deep tree, base-p encoded (p prime, e.g. 31 or 53, large
enough to exceed any node's branching factor) so codes are genuine
p-adic integers in Z_p rather than just prefix-comparable strings.
Genres with multiple valid parents (post-rock under both rock.* and
electronic.ambient.*) get duplicate entries at each valid path; distance
lookups should take the MIN distance across a genre's duplicates rather
than treating each copy as independent. GENRES_DEEP_STUB below is a
placeholder shape for this, not populated.

Each genre has:
  - a p-adic style taxonomy code (currently just the genre name -- see
    above). p-adic distance = f(shared prefix length); see distance.py.
  - valence, energy (== arousal), speed, chaos, colour_warmth: all
    [0, 1], hand-anchored for MVP. Designed to be replaced by real
    Essentia-aggregated audio features later, same shape.
  - instruments: a frozenset of characteristic instrument/sound tags,
    used for Jaccard distance in the categorical half of the metric.

NOTE: every value below is a defensible hand-anchored guess based on
genre stereotypes, not measured data. Flag anything that looks wrong
to your ear -- these are fast to correct, and correctness here matters
more than most of the code, since it's the actual comedic payload.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Genre:
    name: str
    code: str                       # p-adic taxonomy path, dot-separated
    valence: float                   # 0 = sad/dark, 1 = happy/bright
    energy: float                     # 0 = calm/sparse, 1 = intense/dense (== "arousal")
    speed: float = 0.5                # 0 = slow/still, 1 = fast/busy
    chaos: float = 0.5                # 0 = regular/steady, 1 = irregular/chaotic
    colour_warmth: float = 0.5        # 0 = cool (blue/dark), 1 = warm (red/bright)
    instruments: frozenset = frozenset()  # e.g. {"guitar", "drum_kit", "synthesizer"}

    @property
    def continuous_vector(self):
        import numpy as np
        # colour_warmth and instruments deliberately excluded from distance
        # per current scope -- fields remain on the dataclass for later use.
        return np.array([self.valence, self.energy, self.speed, self.chaos])


# --- First layer: root's direct children. No subgenre data required. ---
GENRES = [
    Genre("rock",       "rock",       0.55, 0.70, speed=0.55, chaos=0.40, colour_warmth=0.55,
          instruments=frozenset({"guitar", "bass", "drum_kit", "vocals"})),
    Genre("pop",        "pop",        0.80, 0.65, speed=0.55, chaos=0.20, colour_warmth=0.75,
          instruments=frozenset({"synthesizer", "vocals", "drum_machine"})),
    Genre("jazz",       "jazz",       0.55, 0.45, speed=0.45, chaos=0.55, colour_warmth=0.55,
          instruments=frozenset({"saxophone", "upright_bass", "piano", "brushed_drums"})),
    Genre("classical",  "classical",  0.50, 0.45, speed=0.40, chaos=0.30, colour_warmth=0.45,
          instruments=frozenset({"strings", "brass", "woodwinds", "piano", "organ", "choir"})),
    Genre("electronic", "electronic", 0.65, 0.75, speed=0.65, chaos=0.35, colour_warmth=0.50,
          instruments=frozenset({"synthesizer", "drum_machine"})),
    Genre("hip_hop",    "hip_hop",    0.55, 0.65, speed=0.50, chaos=0.35, colour_warmth=0.55,
          instruments=frozenset({"drum_machine", "bass", "vocals_rap", "sampler"})),
    Genre("metal",      "metal",      0.20, 0.90, speed=0.75, chaos=0.55, colour_warmth=0.15,
          instruments=frozenset({"guitar", "bass", "drum_kit", "vocals_harsh"})),
    Genre("country",    "country",    0.65, 0.50, speed=0.45, chaos=0.20, colour_warmth=0.65,
          instruments=frozenset({"acoustic_guitar", "banjo", "fiddle", "vocals"})),
    Genre("folk",       "folk",       0.55, 0.35, speed=0.35, chaos=0.25, colour_warmth=0.55,
          instruments=frozenset({"acoustic_guitar", "banjo", "vocals"})),
    Genre("blues",      "blues",      0.30, 0.45, speed=0.35, chaos=0.35, colour_warmth=0.40,
          instruments=frozenset({"guitar", "harmonica", "piano", "vocals"})),
    Genre("reggae",     "reggae",     0.70, 0.45, speed=0.40, chaos=0.20, colour_warmth=0.60,
          instruments=frozenset({"guitar", "bass", "drum_kit", "organ"})),
    Genre("r_and_b",    "r_and_b",    0.60, 0.50, speed=0.45, chaos=0.25, colour_warmth=0.60,
          instruments=frozenset({"vocals", "synthesizer", "bass", "drum_kit"})),
    Genre("punk",       "punk",       0.45, 0.90, speed=0.85, chaos=0.55, colour_warmth=0.45,
          instruments=frozenset({"guitar", "bass", "drum_kit", "vocals"})),
    Genre("funk",       "funk",       0.75, 0.70, speed=0.55, chaos=0.35, colour_warmth=0.70,
          instruments=frozenset({"bass", "guitar", "brass", "drum_kit"})),
    Genre("latin",      "latin",      0.80, 0.70, speed=0.60, chaos=0.30, colour_warmth=0.85,
          instruments=frozenset({"percussion", "brass", "guitar", "vocals"})),
    Genre("novelty",    "novelty",    0.85, 0.60, speed=0.55, chaos=0.40, colour_warmth=0.80,
          instruments=frozenset({"synthesizer", "bells", "vocals"})),

    # --- Targeted extremes: added to fill confirmed gaps in the (valence,
    # chaos, speed) cube audit, and to un-average umbrella genres whose
    # centroid washes out their own most extreme members (e.g. "electronic"
    # averages ambient through breakcore into one point that represents
    # neither well). These are NOT a return to blanket everynoise-style
    # depth -- each one earns its place by fixing a specific, checked gap.
    Genre("breakcore",  "electronic.breakcore", 0.35, 0.90, speed=0.95, chaos=0.90, colour_warmth=0.30,
          instruments=frozenset({"drum_machine", "sampler", "synthesizer"})),
    Genre("elevator_music", "jazz.easy_listening", 0.60, 0.20, speed=0.25, chaos=0.05, colour_warmth=0.55,
          instruments=frozenset({"synthesizer", "strings", "saxophone"})),
    Genre("free_improv_noise", "jazz.noise", 0.25, 0.65, speed=0.35, chaos=0.90, colour_warmth=0.30,
          instruments=frozenset({"saxophone", "guitar", "percussion"})),
    Genre("carnival_ska", "novelty.carnival", 0.85, 0.65, speed=0.45, chaos=0.75, colour_warmth=0.85,
          instruments=frozenset({"brass", "accordion", "percussion"})),
]

GENRE_BY_NAME = {g.name: g for g in GENRES}


def _load_everynoise_subset(path="everynoise_top_genres.txt", round_digits=2):
    """
    Bootstraps additional genres from a keyword-scored everynoise sample
    (see genre_bootstrap.py). Filters to real-signal entries only (zero-hit
    genres would just be disguised defaults -- see genre_bootstrap.py's own
    output for why), skips name collisions with the hand-anchored set
    above, and dedupes near-identical score vectors (e.g. "dance pop" and
    "pop dance" scored identically -- keep one, not both).
    """
    from genre_bootstrap import score_genre_name
    import os

    full_path = os.path.join(os.path.dirname(__file__), path)
    if not os.path.exists(full_path):
        return []

    with open(full_path) as f:
        names = [n.strip() for n in f.read().split("»") if n.strip()]

    existing_names = {g.name.lower().replace("_", " ") for g in GENRES}
    seen_vectors = set()
    extra = []

    for name in names:
        if name.lower() in existing_names:
            continue
        s = score_genre_name(name)
        confidence = sum(s["_confidence"].values())
        if confidence == 0:
            continue  # pure defaults -- not usable signal, see genre_bootstrap.py

        vec_key = tuple(round(s[axis], round_digits) for axis in ["valence", "energy", "speed", "chaos"])
        if vec_key in seen_vectors:
            continue  # near-duplicate of an already-included genre
        seen_vectors.add(vec_key)

        extra.append(Genre(
            name=name.replace(" ", "_").replace("-", "_"),
            code=name.replace(" ", "_").replace("-", "_"),
            valence=s["valence"], energy=s["energy"], speed=s["speed"], chaos=s["chaos"],
        ))

    return extra


GENRES.extend(_load_everynoise_subset())
GENRE_BY_NAME = {g.name: g for g in GENRES}  # rebuild after extending

# Curated candidate pools: top 20 genres by extremity on each axis. Used to
# restrict "opposite" search to genres that are ALREADY known-extreme,
# rather than trusting the full argmax over all 42 -- this is a review
# surface as much as a computation shortcut: 20 items is small enough to
# eyeball and hand-correct (e.g. sad_sierreno's single-keyword-hit valence
# score is visible here, not buried), where 42 wasn't.
VALENCE_EXTREME_20 = sorted(GENRES, key=lambda g: abs(g.valence - 0.5), reverse=True)[:20]
CHAOS_EXTREME_20 = sorted(GENRES, key=lambda g: abs(g.chaos - 0.5), reverse=True)[:20]


# --- v2 stub: deeper tree, not populated. Shape only, for when subgenre
# relationship data actually exists (scraped or hand-built). ---
# GENRES_DEEP_STUB = [
#     Genre("pop_punk", "punk.pop_punk", ...),        # single-parent example
#     Genre("post_rock", "rock.post_rock", ...),       # duplicate #1
#     Genre("post_rock", "electronic.ambient.post_rock", ...),  # duplicate #2
#     ...
# ]
