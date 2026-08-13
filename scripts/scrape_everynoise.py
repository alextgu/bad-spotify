"""Scrape the every noise at once genre map into a usable 2D genre embedding.

The page lays every genre out with inline CSS: `top` and `left` pixel values
ARE the embedding (roughly: vertical = organic <-> mechanical, horizontal =
dense/atmospheric <-> spiky/bouncy), and the colour encodes genre character.
That gives you ~6000 genres with coordinates for free, offline, forever.

Caveat worth knowing: the site's data is frozen -- its maintainer left Spotify
and it no longer updates. For our purposes that is fine. We need a stable
geometry, not fresh charts.

Output: data/genre_map.json  ->  {genre: {x, y, color, nx, ny}}
"""
from __future__ import annotations

import json
import re
from pathlib import Path

URL = "https://everynoise.com/engenremap.html"
OUT = Path(__file__).resolve().parents[1] / "data" / "genre_map.json"

STYLE_RE = re.compile(
    r'color:\s*(#[0-9a-fA-F]{3,6}).*?top:\s*(-?\d+)px.*?left:\s*(-?\d+)px', re.S)


def parse(html: str) -> dict:
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, "html.parser")
    out: dict[str, dict] = {}
    for div in soup.find_all("div", class_="genre"):
        style = div.get("style", "") or ""
        m = STYLE_RE.search(style)
        if not m:
            continue
        name = div.get_text(" ", strip=True)
        name = re.sub(r"\s*»\s*$", "", name).strip().lower()
        if not name:
            continue
        color, top, left = m.group(1), int(m.group(2)), int(m.group(3))
        out[name] = {"x": left, "y": top, "color": color}

    if out:
        xs = [v["x"] for v in out.values()]
        ys = [v["y"] for v in out.values()]
        x0, x1 = min(xs), max(xs)
        y0, y1 = min(ys), max(ys)
        for v in out.values():
            v["nx"] = (v["x"] - x0) / max(x1 - x0, 1)
            v["ny"] = (v["y"] - y0) / max(y1 - y0, 1)
    return out


def antipodal_genres(genre_map: dict, genre: str, k: int = 10) -> list[str]:
    """Reflect a genre through the centroid, return the nearest genres to it."""
    if genre not in genre_map:
        return []
    g = genre_map[genre]
    tx, ty = 1.0 - g["nx"], 1.0 - g["ny"]
    ranked = sorted(
        genre_map.items(),
        key=lambda kv: (kv[1]["nx"] - tx) ** 2 + (kv[1]["ny"] - ty) ** 2,
    )
    return [name for name, _ in ranked[:k]]


def main() -> None:
    import requests
    print(f"fetching {URL} ...")
    html = requests.get(URL, timeout=30, headers={"User-Agent": "bad-spotify/0.1"}).text
    data = parse(html)
    if not data:
        raise SystemExit(
            "parsed 0 genres -- the page structure changed. Inspect the HTML and "
            "update STYLE_RE. The seed corpus works fine without this file.")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(data, indent=2))
    print(f"wrote {len(data)} genres -> {OUT}")
    for g in ("death metal", "ambient", "k-pop"):
        if g in data:
            print(f"  opposite of {g!r}: {antipodal_genres(data, g, 5)}")


if __name__ == "__main__":
    main()
