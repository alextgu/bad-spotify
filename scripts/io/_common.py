"""Shared plumbing for the single-feature scripts.

Every script in this folder does ONE step, reads JSON on stdin (or a file),
and writes JSON on stdout. That means they pipe together:

    python scripts/io/describe.py --image park.jpg \
      | python scripts/io/invert.py \
      | python scripts/io/choose.py \
      | python scripts/io/play.py

and it also means each one can be worked on, swapped, or rewritten by a
different person without touching anything else. If you want to try a
HuggingFace model instead of Gemini for the description step, you rewrite
describe.py and nothing downstream notices.

Progress and errors go to stderr so stdout stays clean JSON.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))


def log(msg: str) -> None:
    """Human-facing output. Goes to stderr so it never pollutes the pipe."""
    print(msg, file=sys.stderr)


def read_json(path: str | None = None) -> dict:
    """Read JSON from a file, or from stdin if no path is given."""
    #utf-8-sig, not utf-8: PowerShell puts a BOM at the front of anything it
    #pipes, so `describe.py | invert.py` died on Windows with "Unexpected
    #UTF-8 BOM" before the second script had read a thing. Plain utf-8 text
    #decodes identically under this codec, so it costs nothing elsewhere.
    if path:
        return json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if sys.stdin.isatty():
        log("error: expected JSON on stdin, or pass a file with --in\n"
            "       e.g.  python scripts/io/invert.py --in scene.json")
        raise SystemExit(2)
    raw = sys.stdin.read().lstrip("﻿").strip()
    if not raw:
        log("error: got empty input")
        raise SystemExit(2)
    return json.loads(raw)


def write_json(obj) -> None:
    """The only thing that should ever touch stdout."""
    json.dump(obj, sys.stdout, indent=2, default=str)
    sys.stdout.write("\n")


def load_config():
    from badspotify.config import load_config as _load
    return _load(ROOT / "config.yaml")
