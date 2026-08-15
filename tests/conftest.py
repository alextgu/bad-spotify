"""Shared test setup.

The Spotify guards -- the per-minute search budget and the rate-limit
stand-down -- are deliberately module-level, because they protect a quota that
is shared by the whole process. That makes them leak between tests: the first
few tests spend the allowance and everything after them silently gets "budget
spent" instead of the behaviour under test.

Reset them before each test so every one starts from a clean quota.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


@pytest.fixture(autouse=True)
def _reset_spotify_guards():
    from badspotify.music import discover

    discover._recent_calls.clear()
    discover._blocked_until = 0.0
    yield
    discover._recent_calls.clear()
    discover._blocked_until = 0.0
