"""
Keyword-heuristic genre scorer: bootstraps (valence, energy, speed, chaos)
from substrings in a genre's NAME, so a few hundred everynoise genres can
get a first-pass score automatically. This is explicitly rough -- the
point is to make "comprehensive subset" tractable within a hackathon
timeframe, not to replace careful hand-anchoring. Every score comes with
a confidence count (how many keyword rules fired) so low-confidence
guesses are visible rather than silently trusted.

Dropped per current scope: instruments (categorical) and colour_warmth.
Working axes are just valence, energy, speed, chaos, per the latest
simplification.
"""

import re

# Each rule: (regex pattern, axis, value, weight). Weight lets stronger
# signals (e.g. "doom" is a very confident low-valence marker) count more
# than weaker ones (e.g. "pop" is a decent but noisier valence marker,
# since "k-pop", "trap pop" etc dilute it).
RULES = [
    # --- valence: happy/bright vs sad/dark ---
    (r"doom|death|funeral|dirge|black metal|depress|misery|sorrow", "valence", 0.05, 3),
    (r"sad|melancholy|emo\b|grief|mourning", "valence", 0.20, 2),
    (r"dark|goth|noir", "valence", 0.25, 2),
    (r"bubblegum|party|festive|holiday|christmas|carnival|circus", "valence", 0.90, 3),
    (r"dance|disco|funk|salsa|reggaeton|afrobeat", "valence", 0.75, 2),
    (r"\bpop\b", "valence", 0.72, 1),

    # --- energy/arousal: calm vs intense ---
    (r"metal|hardcore|thrash|grind|speedcore|gabber|riot", "energy", 0.90, 3),
    (r"punk|rage|aggressive", "energy", 0.85, 2),
    (r"ambient|chill|lo-?fi|sleep|acoustic|mellow|soft", "energy", 0.20, 3),
    (r"edm|house|dance|club|rave", "energy", 0.78, 2),
    (r"ballad|singer-?songwriter", "energy", 0.30, 2),

    # --- speed: slow vs fast ---
    (r"speedcore|gabber|thrash|grind|hardcore|breakcore|drum and bass|dnb", "speed", 0.90, 3),
    (r"punk|trap\b", "speed", 0.75, 2),
    (r"ballad|slow|sleep|ambient|chamber|chill", "speed", 0.20, 3),
    (r"house|disco|dance", "speed", 0.62, 1),

    # --- chaos: regular vs irregular ---
    (r"free jazz|noise|experimental|avant-?garde|chaotic|grind", "chaos", 0.88, 3),
    (r"black metal|death metal|breakcore|speedcore", "chaos", 0.80, 2),
    (r"chamber|classical|ballad|acoustic|folk", "chaos", 0.25, 2),
    (r"house|edm|pop\b|dance pop", "chaos", 0.20, 1),
]

DEFAULTS = {"valence": 0.5, "energy": 0.5, "speed": 0.5, "chaos": 0.5}


def score_genre_name(name: str) -> dict:
    name_lc = name.lower()
    scores = {axis: [] for axis in DEFAULTS}  # collect (value, weight) hits per axis

    for pattern, axis, value, weight in RULES:
        if re.search(pattern, name_lc):
            scores[axis].append((value, weight))

    result = {}
    confidence = {}
    for axis, hits in scores.items():
        if not hits:
            result[axis] = DEFAULTS[axis]
            confidence[axis] = 0
        else:
            total_weight = sum(w for _, w in hits)
            result[axis] = sum(v * w for v, w in hits) / total_weight
            confidence[axis] = len(hits)

    result["_confidence"] = confidence
    return result


if __name__ == "__main__":
    with open("everynoise_top_genres.txt") as f:
        names = [n.strip() for n in f.read().split("»") if n.strip()]

    print(f"Loaded {len(names)} genre names.\n")
    print(f"{'genre':30s} {'valence':>8s} {'energy':>8s} {'speed':>8s} {'chaos':>8s}  confidence")

    low_confidence_count = 0
    for name in names[:25]:  # sample for inspection
        s = score_genre_name(name)
        total_conf = sum(s["_confidence"].values())
        if total_conf == 0:
            low_confidence_count += 1
        flag = "  <-- all defaults, no keyword hit" if total_conf == 0 else ""
        print(f"{name:30s} {s['valence']:8.2f} {s['energy']:8.2f} {s['speed']:8.2f} {s['chaos']:8.2f}{flag}")

    all_scores = [score_genre_name(n) for n in names]
    no_hit = sum(1 for s in all_scores if sum(s["_confidence"].values()) == 0)
    print(f"\n{no_hit} / {len(names)} genres got ZERO keyword hits (pure defaults, need manual scoring or better rules).")
