from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml
from .log import notice as print  # stdout is reserved for data

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:  #dotenv is optional
    pass

ROOT = Path(__file__).resolve().parents[2]


class Config(dict):
    """Dot-ish access over the YAML tree. Deliberately dumb."""

    def section(self, name: str) -> dict[str, Any]:
        return self.get(name, {}) or {}

    def get_path(self, dotted: str, default=None):
        node: Any = self
        for part in dotted.split("."):
            if not isinstance(node, dict) or part not in node:
                return default
            node = node[part]
        return node


def load_config(path: str | Path | None = None) -> Config:
    path = Path(path) if path else ROOT / "config.yaml"
    # encoding is explicit: the announce template holds an em dash, and on
    # Windows the default is the locale codepage, which mangles it silently.
    with open(path, encoding="utf-8") as f:
        return Config(yaml.safe_load(f) or {})


def env(key: str, default: str | None = None) -> str | None:
    v = os.environ.get(key, default)
    return v if v else default


def has_key(key: str) -> bool:
    return bool(os.environ.get(key, "").strip())


def resolve_backend(requested: str, env_key: str, name: str) -> str:
    """Downgrade to mock rather than crash. Never silent, always wrong."""
    if requested == "mock":
        return "mock"
    if not has_key(env_key):
        print(f"[config] {name}: '{requested}' requested but {env_key} is unset -> using mock")
        return "mock"
    return requested
