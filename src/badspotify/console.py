"""Console rendering of the event stream.

The HUD is the product surface; this is the same information for whoever is
running it from a terminal (and for CI logs, where a silent success and a
silent failure look identical).
"""
from __future__ import annotations

from .bus import BUS
from .schemas import PipelineEvent

DIM = "\033[2m"
BOLD = "\033[1m"
RESET = "\033[0m"
ORANGE = "\033[38;5;173m"
BLUE = "\033[38;5;69m"
RED = "\033[38;5;167m"


def _fmt(ev: PipelineEvent) -> str | None:
    d = ev.detail or {}
    if ev.kind == "gate":
        return f"{DIM}gate      {ev.label:<8} {d.get('reason','')}{RESET}"
    if ev.kind == "scene":
        return (f"{BLUE}scene{RESET}     {BOLD}{d.get('setting', ev.label)}{RESET}\n"
                f"{DIM}          mood={ev.label} conf={d.get('confidence',0):.2f} "
                f"{d.get('latency_ms',0)}ms via {d.get('source','?')}{RESET}")
    if ev.kind == "antivibe":
        genres = ", ".join(d.get("target_genres", [])[:6])
        return f"{DIM}antivibe  seeking: {genres}{RESET}"
    if ev.kind == "candidates":
        picks = " | ".join(p["title"] for p in d.get("picks", [])[:3])
        return f"{DIM}strategy  {ev.label:<15} {picks}{RESET}"
    if ev.kind == "verdict":
        return (f"{ORANGE}verdict{RESET}   {BOLD}{ev.label}{RESET} — {d.get('artist','')}\n"
                f"{DIM}          via {d.get('strategy')} · mismatch {d.get('mismatch',0):.2f} · "
                f"{d.get('reasoning','')[:80]}{RESET}")
    if ev.kind == "dj":
        return f"{DIM}dj        {ev.label:<8} {d.get('reason','')}{RESET}"
    if ev.kind == "error":
        return f"{RED}error     {ev.label}: {d.get('error','')}{RESET}"
    return None


def attach(verbose: bool = True) -> None:
    def on_event(ev: PipelineEvent) -> None:
        line = _fmt(ev)
        if line and (verbose or ev.kind in ("verdict", "error", "play")):
            print(line)

    BUS.subscribe(on_event)
