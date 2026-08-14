"""The judge: picks the funniest, not the most opposite.

Geometry already ranked the candidates by how wrong they are. That is the
wrong final metric -- "most distant in vibe space" is often just a random
noise record nobody knows. Comedy needs specificity and recognition, and
that is exactly the thing an LLM has and a distance metric does not.

So: geometry shortlists, the model chooses, and it must justify the choice
in one line that we then speak aloud. The quip IS the product.
"""
from __future__ import annotations

import json
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

Then write `quip`: what the agent says out loud as it starts the track.
Deadpan, smug, under 15 words, never explains the joke. It is not sorry.
Good: "You looked comfortable." / "This is a funeral now."
Bad: "Ha ha, I'm playing the opposite of what you'd want!"

Return JSON: {"track_id", "quip", "reasoning"}"""

_MOCK_QUIPS = [
    "You looked comfortable.",
    "This is a funeral now.",
    "I've read the room. I'm ignoring it.",
    "Everyone here needs to hear this.",
    "Correcting the atmosphere.",
    "You'll thank me eventually. You won't, but you'll say it.",
    "The moment was getting too coherent.",
]


class MockJudge:
    backend = "mock"

    def __init__(self, cfg: dict | None = None):
        self._rng = random.Random(0xBADBEEF)

    def judge(self, scene: SceneRead, anti: AntiVibe,
              candidates: list[Candidate]) -> Verdict:
        if not candidates:
            raise ValueError("no candidates")
        top = candidates[0]
        return Verdict(
            track=top.track,
            strategy=top.strategy,
            mismatch=mismatch(scene.vibe, top.track.vibe),
            quip=self._rng.choice(_MOCK_QUIPS),
            reasoning=f"highest wrongness score via {top.strategy}: {top.notes}",
            runner_ups=[c.track.title for c in candidates[1:4]],
            source="mock",
        )


class GeminiJudge:
    backend = "gemini"

    def __init__(self, cfg: dict):
        from google import genai
        self.model = cfg.get("model", "gemini-2.5-flash")
        self.timeout_s = float(cfg.get("timeout_s", 4.0))
        self.retries = int(cfg.get("retries", 1))
        self.client = genai.Client()
        self._fallback = MockJudge()

    def judge(self, scene: SceneRead, anti: AntiVibe,
              candidates: list[Candidate]) -> Verdict:
        if not candidates:
            raise ValueError("no candidates")
        try:
            from google.genai import types

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
                for c in candidates[:12]
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
                        temperature=1.0,  #Allows more varied jokes
                    ),
                ),
                self.timeout_s,
                retries=self.retries,
                label="judge",
            )
            d = json.loads(resp.text)
            chosen = next((c for c in candidates if c.track.id == d["track_id"]), candidates[0])
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
