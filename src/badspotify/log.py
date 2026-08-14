"""Diagnostics go to stderr. Always.

This exists because of a real bug: the single-feature scripts in `scripts/io/`
pipe JSON to each other, and `Corpus.load()` printing "loaded 47 tracks" on
STDOUT corrupted the stream — the next script in the chain got that line
before the JSON and died on a parse error.

The rule this enforces: **stdout is for the answer, stderr is for the
commentary.** Anything a human reads goes through `notice()`. Anything a
program reads is written straight to stdout by the caller.

The one deliberate exception is the players and the narrator, which announce
what's actually happening ("[PLAY] Bodies — Drowning Pool"). Those are also
routed here, so a piped script stays clean.
"""
from __future__ import annotations

import sys


def notice(*args, **kwargs) -> None:
    kwargs.setdefault("file", sys.stderr)
    print(*args, **kwargs)
