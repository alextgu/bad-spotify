"""The judge: picks the funniest, not the most opposite.

Geometry already ranked the candidates by how wrong they are. That is the
wrong final metric -- "most distant in vibe space" is often just a random
noise record nobody knows. Comedy needs specificity and recognition, and
that is exactly the thing an LLM has and a distance metric does not.

So: geometry shortlists, the model chooses, and it must justify the choice
in one line that we then speak aloud.

**The agent believes it is doing a good job.** That is the character, and it is
load-bearing. It is not smug, it is not winking, it does not know the music is
wrong -- it is a conscientious DJ announcing a considered choice. The comedy is
entirely in the gap between how sincerely it says the line and how catastrophic
the pick is. The moment it acknowledges the joke, it stops being funny and
starts being a person doing a bit.
"""
from __future__ import annotations

import json
import math
import random

from ..config import resolve_backend
from ..resilience import call_with_timeout
from ..music.vibe import mismatch
from ..schemas import AntiVibe, Candidate, SceneRead, Verdict
from ..log import notice as print  # stdout is reserved for data

JUDGE_PROMPT = """You are the taste module of an agent whose ONLY purpose is to
play the worst possible music for the moment. Not bad music -- WRONG music.
The gap between the situation and the soundtrack is the entire joke.

You will be given a scene and a shortlist of candidate tracks, each proposed by
a different theory of wrongness. Pick the ONE that would be funniest to actually
hear right now, and say why in a single line.

How to choose:
- Specificity beats magnitude. "Funeral doom in a toddler's birthday party" is
  funnier than "loud music in a quiet place".
- Recognition matters. If nobody in the room can name the track, the joke dies.
- Undercutting often beats amplifying. Yakety Sax during a tense moment is
  funnier than horror music during a tense moment.
- Never pick something that would genuinely FIT. That is failure.

Then write `quip`: what the agent says as it starts the track.

CRITICAL -- the agent thinks this is a GOOD choice and is pleased with it. It
is a professional DJ who has read the room carefully and is confident it has
matched it. Sincere, warm, under 15 words. It never jokes, never winks, never
apologises, and never acknowledges any mismatch, because as far as it is
concerned there isn't one.

Good: "This should suit the room nicely."
Good: "A perfect fit for the occasion."
Good: "I think this is exactly what the moment needs."
Bad:  "You looked comfortable."            (smug -- it knows)
Bad:  "This is a funeral now."             (in on the joke)
Bad:  "Ha ha, the opposite of what you want!"

Return JSON: {"track_id", "quip", "reasoning"}"""

# Sincere, every one. The agent is pleased with its work -- see the note at
# the top of this file. If a line here reads as knowing, it is wrong.
_MOCK_QUIPS = [
    "This should suit the room nicely.",
    "A perfect fit for the occasion.",
    "I think this is exactly what the moment needs.",
    "Reading the room, and this is my choice.",
    "Matched to the mood.",
    "This is the right call for the room.",
    "Chosen to fit the occasion.",
]

DEFAULT_SELECTION_TEMPERATURE = 0.20


def _random_source(cfg: dict):
    seed = cfg.get("random_seed")
    return random.Random(seed) if seed is not None else random.SystemRandom()


def _temperature_pick(candidates: list[Candidate], temperature: float, rng):
    if not candidates:
        raise ValueError("no candidates")
    if temperature <= 0:
        return max(candidates, key=lambda candidate: candidate.raw_distance)
    peak = max(candidate.raw_distance for candidate in candidates)
    weights = [
        math.exp((candidate.raw_distance - peak) / temperature)
        for candidate in candidates
    ]
    return rng.choices(candidates, weights=weights, k=1)[0]


def _temperature_shortlist(
    candidates: list[Candidate], size: int, temperature: float, rng,
) -> list[Candidate]:
    remaining = list(candidates)
    chosen = []
    while remaining and len(chosen) < size:
        candidate = _temperature_pick(remaining, temperature, rng)
        chosen.append(candidate)
        remaining.remove(candidate)
    return chosen


class MockJudge:
    backend = "mock"

    def __init__(self, cfg: dict | None = None):
        cfg = cfg or {}
        self.selection_temperature = max(
            0.0, float(cfg.get(
                "selection_temperature", DEFAULT_SELECTION_TEMPERATURE)))
        self._rng = _random_source(cfg)

    def judge(self, scene: SceneRead, anti: AntiVibe,
              candidates: list[Candidate]) -> Verdict:
        top = _temperature_pick(
            candidates, self.selection_temperature, self._rng)
        return Verdict(
            track=top.track,
            strategy=top.strategy,
            mismatch=mismatch(scene.vibe, top.track.vibe),
            quip=self._rng.choice(_MOCK_QUIPS),
            reasoning=f"score-weighted choice via {top.strategy}: {top.notes}",
            runner_ups=[
                c.track.title for c in candidates if c.track.id != top.track.id
            ][:3],
            source="mock",
        )


class GeminiJudge:
    backend = "gemini"

    def __init__(self, cfg: dict):
        from google import genai
        self.model = cfg.get("model", "gemini-2.5-flash")
        self.timeout_s = float(cfg.get("timeout_s", 4.0))
        self.retries = int(cfg.get("retries", 1))
        self.selection_temperature = max(
            0.0, float(cfg.get(
                "selection_temperature", DEFAULT_SELECTION_TEMPERATURE)))
        self.shortlist_size = max(1, int(cfg.get("shortlist_size", 8)))
        self._rng = _random_source(cfg)
        self.client = genai.Client()
        self._fallback = MockJudge(cfg)

    def judge(self, scene: SceneRead, anti: AntiVibe,
              candidates: list[Candidate]) -> Verdict:
        if not candidates:
            raise ValueError("no candidates")
        try:
            from google.genai import types

            sampled = _temperature_shortlist(
                candidates, self.shortlist_size,
                self.selection_temperature, self._rng)
            shortlist = [
                {
                    "track_id": c.track.id,
                    "title": c.track.title,
                    "artist": c.track.artist,
                    "genres": c.track.genres,
                    "tags": c.track.tags,
                    "recognisability": c.track.recognisability,
                    "proposed_by": c.strategy,
                    "why": c.notes,
                }
                for c in sampled
            ]
            payload = {
                "scene": {
                    "setting": scene.setting,
                    "activity": scene.activity,
                    "social_context": scene.social_context,
                    "mood": scene.mood_label,
                    "audio": scene.audio_summary,
                    "vibe": scene.vibe.model_dump(),
                },
                "taboo_rationale": anti.rationale,
                "candidates": shortlist,
            }
            resp = call_with_timeout(
                lambda: self.client.models.generate_content(
                    model=self.model,
                    contents=f"{JUDGE_PROMPT}\n\n{json.dumps(payload, indent=2)}",
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema={
                            "type": "object",
                            "properties": {
                                "track_id": {"type": "string"},
                                "quip": {"type": "string"},
                                "reasoning": {"type": "string"},
                            },
                            "required": ["track_id", "quip", "reasoning"],
                        },
                    ),
                ),
                self.timeout_s,
                retries=self.retries,
                label="judge",
            )
            d = json.loads(resp.text)
            chosen = next(
                (c for c in sampled if c.track.id == d["track_id"]), sampled[0])
            return Verdict(
                track=chosen.track,
                strategy=chosen.strategy,
                mismatch=mismatch(scene.vibe, chosen.track.vibe),
                quip=d["quip"],
                reasoning=d["reasoning"],
                runner_ups=[c.track.title for c in candidates[:4] if c.track.id != chosen.track.id],
                source="gemini",
            )
        except Exception as e:
            print(f"[judge] gemini failed ({e}) -> mock judge")
            return self._fallback.judge(scene, anti, candidates)


def build_judge(cfg: dict):
    backend = resolve_backend(cfg.get("backend", "mock"), "GOOGLE_API_KEY", "judge")
    if backend == "gemini":
        try:
            return GeminiJudge(cfg)
        except Exception as e:
            print(f"[judge] gemini init failed ({e}) -> mock")
    return MockJudge(cfg)
