"""Track corpus: load, index, and search by vibe.

Start with the hand-curated seed (data/corpus.seed.json) because the joke
requires recognition. Grow it later from MTG-Jamendo / Deezer mood data via
scripts/build_corpus.py without changing anything above this file.
"""
from __future__ import annotations

import json
from pathlib import Path

from ..schemas import Track, Vibe
from ..log import notice as print  # stdout is reserved for data

ROOT = Path(__file__).resolve().parents[3]


class Corpus:
    def __init__(self, tracks: list[Track]):
        self.tracks = tracks
        self._by_id = {t.id: t for t in tracks}

    def __len__(self) -> int:
        return len(self.tracks)

    def get(self, tid: str) -> Track | None:
        return self._by_id.get(tid)

    def all_tags(self) -> set[str]:
        return {tag for t in self.tracks for tag in t.tags}

    def filter(self, exclude_ids: set[str] | None = None,
               banned_tags: list[str] | None = None) -> list[Track]:
        exclude_ids = exclude_ids or set()
        banned = set(banned_tags or [])
        out = []
        for t in self.tracks:
            if t.id in exclude_ids:
                continue
            if banned and (banned & set(t.tags) or banned & set(t.genres)):
                continue
            out.append(t)
        return out

    @classmethod
    def load(cls, path: str | Path | None = None) -> "Corpus":
        for candidate in [path, ROOT / "data" / "corpus.json",
                          ROOT / "data" / "corpus.seed.json"]:
            if candidate and Path(candidate).exists():
                raw = json.loads(Path(candidate).read_text())
                tracks = [
                    Track(
                        id=r["id"], title=r["title"], artist=r["artist"],
                        genres=r.get("genres", []), vibe=Vibe(**r["vibe"]),
                        tags=r.get("tags", []), uri=r.get("uri"),
                        recognisability=r.get("recognisability", 0.5),
                        duration_s=r.get("duration_s"),
                    )
                    for r in raw
                ]
                print(f"[corpus] loaded {len(tracks)} tracks from {Path(candidate).name}")
                return cls(tracks)
        raise FileNotFoundError(
            "no corpus found -- run: python scripts/build_seed_corpus.py")
