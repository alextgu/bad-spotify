# AGENTS.md — the rules, the seams, and the traps

`CLAUDE.md` is a symlink to this file. Same rules for every agent and every
human. If you change how the project works, change this file in the same commit.

**The rule that matters most: everything in here is checkable, and was checked.**
Nothing below is aspiration or plan. If you can't verify a claim by running the
command next to it, it does not belong here — put it in `README.md` (how it
works) or `STATUS.md` (what's finished) instead.

Last verified: **14 Aug 2026**, against `main`.

---

## What this is

A wearable-style agent whose only feature is playing the worst possible music
for the moment it is in. It reads a scene, computes the musical opposite of that
scene's mood, picks a track from a hand-curated corpus, and announces it.

**"Worst" means musically opposite in mood, and nothing else.** Five axes —
`valence, arousal, density, brightness, organicness` (`schemas.py`). The system
has no notion of anyone's race, sex, religion, politics or identity, and must
never acquire one. There is no "how far to go" dial and there must not be one;
a test asserts this (`tests/test_pipeline.py::test_reflection_has_no_dial`).

---

## Which document owns what

Three, and one job each. **Don't add a fourth** — we had eight and they drifted
apart within a day.

| File | Owns | Does not contain |
|---|---|---|
| `README.md` | what it does, how it works in plain language, how to run it, architecture | claims about what is finished |
| `AGENTS.md` (this) | the rules, the seams you plug into, the traps, and what is *not* settled | prose explanations of how it works |
| `STATUS.md` | **state**: Done / Built-unproven / Not started, and how each was proven | explanations |

Plus one README beside each part that ships on its own: `frontend/`,
`src/videofeed/`, `scripts/io/`. Those stay with their code.

---

## Verified commands

Every one of these was run on 14 Aug 2026 and did what it says.

```bash
# tests — 83 pass
source .venv/bin/activate && python -m pytest tests/ -q

# the agent, bounded and headless (park -> Drowning Pool, library -> Sandstorm)
python run.py --ticks 6 --no-hud

# the agent with its two screens
python run.py                       # 127.0.0.1:8420/dj  and  127.0.0.1:8420/

# the hosted browser app (Gradio)
python app.py                       # 127.0.0.1:7860

# one step at a time, JSON in and out
python scripts/io/describe.py --text "a sunlit park" \
  | python scripts/io/invert.py | python scripts/io/choose.py

# the sampler, standalone
PYTHONPATH=src python -m videofeed clip.mp4 --interval 5 \
    --triggers scene-cut,audio-onset --out runs/demo1

# the site
cd frontend && npm install && npm run dev     # localhost:3000, /demo
cd frontend && npx tsc --noEmit && npm run build
```

`pytest` and `gradio` are in `requirements.txt`. `ffmpeg` on PATH is needed for
video audio; without it the sampler runs vision-only rather than failing.

### Test inventory (83, verified by `--collect-only`)

| File | Count | Guards |
|---|---|---|
| `tests/test_videofeed.py` | 17 | sampling a real generated mp4: cadence, triggers, rate limiting, sinks |
| `tests/test_pipeline.py` | 15 | vibe reflection, antivibe, strategies, DJ bounds, fallback |
| `tests/test_spotify_player.py` | 15 | the player against a stand-in Spotify |
| `tests/test_spotify_match.py` | 13 | search-result matching (karaoke, tribute bands, wrong artists) |
| `tests/test_service.py` | 12 | `Engine`: describe / look / watch, no speakers by default, no bus leak |
| `tests/test_video_and_session.py` | 7 | video-as-live and the recorded session format |
| `tests/test_local_video_app.py` | 4 | local perception, upload validation, and sampled analysis |

---

## Find your seam

Five of them, deliberately narrow. Work inside one and nothing else needs to
know you exist.

| You're building | Your seam | Contract |
|---|---|---|
| Anything that turns the world into a description | `perceive/scene.py` → `build_perceiver(cfg)` | returns an object with `.read(frame, audio_features, meta) -> SceneRead` |
| A new theory of what makes music wrong | `music/strategies.py` → `REGISTRY` | `fn(scene, anti, corpus, exclude, n) -> list[Candidate]` |
| A new way to pick the winner | `agents/judge.py` → `build_judge(cfg)` | returns an object with `.judge(scene, anti, candidates) -> Verdict` |
| A new way to get sound out | `players/base.py` → `build_player(cfg)` | `.play(track, mode)`, `.stop()`, `.set_volume(level)` |
| A new source of frames | `capture/base.py` → `build_capture(cfg)` | `.open()`, `.close()`, `.stream() -> Iterator[Observation]` |

Every one already has a **mock**. Read the mock first — it is the shortest
correct answer to "what shape must I return".

### The two contracts that actually matter

Everything else is internal. These cross boundaries, so changing them breaks
other people.

**`SceneRead`** (`schemas.py`) — produced by perception, consumed by everything
downstream.

| Field | Why anyone else cares |
|---|---|
| `setting`, `activity` | **The specificity lives here.** "toddler's birthday party, cake being cut" produces a joke; "indoor event" produces nothing. If your approach can't produce this, it isn't good enough, however clever it is |
| `vibe` — 5 floats, 0–1 | Gets flipped to find the opposite. Must actually span the range; if everything comes back near 0.5 the inversion is meaningless |
| `confidence` | Below 0.35 the system does nothing. **Be honest here.** Overconfidence on a blurry frame is worse than admitting you don't know |
| `mood_label`, `tempo_feel`, `meter` | Feed the strategies |

**The session file** — written by `session.py`, read by `frontend/lib/types.ts`.
If you change the shape, change both, in the same commit. The one that bites:
use **`played.at_video_time`** for anything on a timeline, not `video_time` —
the scene is usually read a few seconds before the song actually lands.

---

## What exists, in code

Entry points. They share one graph.

```
run.py                the live loop: capture -> gate -> perceive -> antagonize ->
                      judge -> dj -> play, plus the HUD. graph.tick(obs).
app.py                Gradio, four tabs. Sits on service.Engine.
python -m videofeed   the sampler alone. Imports nothing from badspotify.
scripts/io/*.py       one step each, JSON in and out, pipeable.
```

| Path | What is actually in it |
|---|---|
| `src/badspotify/capture/` | `base` (Observation + factory), `gate` (change gate), `replay`, `video`, `webcam`, `glasses` (stub) |
| `src/badspotify/perceive/` | `scene` (mock + Gemini + Hugging Face perceivers, `scene_from_text`), `audio_features` (librosa) |
| `src/badspotify/music/` | `vibe` (reflection, taboo rules), `corpus`, `strategies` (three) |
| `src/badspotify/agents/` | `graph` (LangGraph, two entry points), `judge` (mock + Gemini) |
| `src/badspotify/dj/` | `controller`: hysteresis, cooldown, queue-vs-interrupt, fallback deck |
| `src/badspotify/players/` | `mock`, `local`, `spotify`, `spotify_match` |
| `src/badspotify/voice/` | `narrator` (mock + ElevenLabs) |
| `src/badspotify/hud/` | FastAPI: `/`, `/dj`, `/api/session`, `/api/state`, `/api/inject`, `/api/analyze-video`, `/ws` |
| `src/badspotify/analysis.py` | uploaded video analysis with stable mood segments and no playback side effects |
| `src/badspotify/service.py` | `Engine`: `describe()`, `look()`, `watch()` — no loop |
| `src/badspotify/session.py` | records a run to the JSON the site replays |
| `src/badspotify/log.py` | `notice()` → stderr. See the stdout trap below |
| `src/videofeed/` | standalone sampler: cadence + triggers, audio window, handoff stub |
| `frontend/` | Next.js site. Two routes: `/` and `/demo` |

**LangGraph, both entry points** (`agents/graph.py`):

| Method | Used by | Enters at |
|---|---|---|
| `tick(obs)` | `run.py` | the change gate |
| `decide_from_scene(state)` | `service.Engine` → Gradio, and any glasses app | `antagonize` |

Same nodes, same edges. Without langgraph installed both fall back to a
sequential executor with identical semantics.

**The three strategies** are `genre_antipode`, `tempo_clash`, `lyrical_irony`
(`music/strategies.py` → `REGISTRY`). They fan out concurrently and a judge
picks between them.

**The corpus** is 47 tracks (`data/corpus.seed.json`, verified by counting).

---

## Hard rules

1. **It is never silent.** Silence is the only real bug; playing the wrong thing
   is the product working. Every backend degrades to a stand-in, and under
   everything sits the fallback deck in `dj/controller.py`. If you touch the DJ
   or player layers, confirm the fallback still fires.
2. **Don't delete the mocks.** Every model, player and voice has one. They are
   why a teammate with no API keys can run the whole pipeline. They are not dead
   code.
3. **No dial on the inversion, ever.** See the top of this file.
4. **`STATUS.md` is the state of the world.** Update it in the same change that
   makes it true, and say *how* something was proven. "Works" is not a proof.
   "Ran it against 5 real photos, descriptions matched, confidence dropped on
   the blurry one" is.
5. **Nothing plays out loud from a hosted surface by default.** `app.py` uses
   the mock player unless `--play` is passed.
6. **Ask before deleting.** Prefer moving to `_review/` (git-ignored).

Before you say you're done:

```bash
pytest tests/ -q                      # all 83, not just yours
python run.py --ticks 6 --no-hud      # the loop still runs on mocks
```

---

## Traps in this specific repo

Every one of these has already cost someone hours here. They are not
hypothetical.

**LangGraph silently drops state keys you didn't declare.** If you add something
to the pipeline state, add it to the `PipelineState` TypedDict in
`agents/graph.py` too. Otherwise it vanishes between nodes with no error — a
`force` flag was being set and discarded for exactly this reason, and the
symptom was "the button does nothing sometimes".

**stdout is reserved for data.** The scripts in `scripts/io/` pipe JSON to each
other. Never `print()` in library code — use `from ..log import notice`. A
single stray line of status output corrupts the stream and the next script dies
on a parse error.

**Don't add `from __future__ import annotations` to `hud/server.py`.** FastAPI
resolves handler annotations against module globals, and `WebSocket` is imported
lazily inside the function. Under postponed annotations it isn't found, FastAPI
treats the parameter as an unknown query field, and the browser gets a bare HTTP
403 with nothing in the server log. There's a comment there saying so; leave it.

**Cheap checks can starve the thing that depends on them.** The change gate
suppresses repeated reads to save model calls; the DJ needs two agreeing reads
before it acts. Together they deadlocked on calm footage — nothing ever played.
A quiet tick now counts as positive evidence that the scene is *stable*. If you
add another optimisation that skips work, ask what downstream was counting on
that work happening.

**Library versions move under you.** `librosa.beat.tempo` was removed in 1.0 and
the exception aborted the whole feature block, so tempo, centroid, flatness and
pulse regularity were silently zero on every tick for days. Gradio 6 moved
`theme` off the `Blocks` constructor and dropped `show_api` from `launch()`.
Check the installed version before trusting a remembered API.

**There is no dial for how wrong to be.** `Verdict.mismatch` is measured after
the fact, never set. Don't add a parameter for it — that was removed on purpose
and there's a test asserting its absence.

---

## Worked example: adding a fourth theory of wrongness

The whole change is one function and one line.

```python
# src/badspotify/music/strategies.py

def era_clash(scene, anti, corpus, exclude, n):
    """Wrong in TIME. A 1950s crooner at a rave is not sonically opposite --
    it's from the wrong century, and that reads as funnier than distance."""
    scored = []
    for t in corpus.filter(exclude, anti.banned_genres):
        # ... your scoring ...
        scored.append(Candidate(track=t, strategy="era_clash",
                                raw_distance=score, notes="why this one"))
    scored.sort(key=lambda c: c.raw_distance, reverse=True)
    return scored[:n]


REGISTRY["era_clash"] = era_clash
```

Then add `era_clash` to `antagonize.strategies` in `config.yaml`, and check it:

```bash
python scripts/io/describe.py --text "a rave at 2am" \
  | python scripts/io/choose.py --show-all
```

`--show-all` prints every candidate with the strategy that proposed it, so you
can see whether yours is contributing anything the others weren't.

**A new strategy earns its place by disagreeing.** If it keeps proposing what
`genre_antipode` already proposed, it's costing time and adding nothing. Three
strategies that argue beat five that agree.

---

## Not settled — do not invent

Genuinely open. If you need one of these decided, ask; do not write it into a
doc as though it were agreed.

- **Which surface is *the* demo.** Three exist now — the live loop with `/dj`,
  the Gradio app, and the static site replaying a recording. `STATUS.md` records
  a 13 Aug decision to demo a video file through `/dj`; the Gradio app arrived
  after that and no decision has been recorded about it.
- **Holding a song while the mood is unchanged.** Being built now. As of this
  commit, on a *completely stable* scene the DJ still commits a new queued track
  roughly every other tick — measured: 4 tracks across 35s of identical library
  footage, each one reporting `scene shifted 0.00`. Two things to know before
  changing it: `commit()` sets `started_at` and `state.current` for a *queued*
  track that hasn't started playing yet, so the timing bounds measure the wrong
  thing; and nothing anywhere knows when a track ends — no `Track.duration_s` is
  populated in the corpus, and no player surfaces playback progress.
- **Whether `videofeed` becomes the agent's sampler.** `service.Engine.watch()`
  uses it. `run.py` still uses `capture/video.py`, which samples on a fixed
  interval only. The adapter is six lines and documented in
  `src/videofeed/README.md`, but nobody has run the agent off it.
- **The Gemini prompt and its output schema.** Written in `perceive/scene.py`
  and `agents/judge.py`, never once run against the real API — there has been no
  `GOOGLE_API_KEY` on any machine that ran this. Timeout is 4s in `config.yaml`
  and that number is a guess.
- **The "best song" mode.** The site's FAQ says the same machinery would find the
  best song with the sign flipped. That is a design claim, not code — nothing
  implements it.
- **The name.** `bad spotify` is a working title in `frontend/lib/brand.ts`.
  Spotify's terms forbid "Spotify" in a product name, so it cannot ship as is.
- **The site's visual design.** The current pass is *framework only*: white
  showcase, tokens in `frontend/app/globals.css`, section 1 (advertisement) and
  section 2 (the rippling mark) are structural placeholders with named slots.
  Page transitions are planned; `.section-page` gives each section a one-screen
  floor, and scroll-snap is deliberately off.

---

## What to optimise for when you're unsure

Two things, in this order:

1. **The judges have to recognise the song.** An obscure track that is
   technically the perfect opposite is a worse pick than a famous one that is
   merely very wrong.
2. **The reasoning has to stay visible.** Seeing *why* it chose funeral doom is
   the difference between an agent and a shuffle button, and it's most of why
   the technical work reads as serious.

If a change helps one of those, it's probably right. If it quietly costs one of
them to gain something else, say so out loud rather than deciding alone.

---

## Keeping this file honest

When you finish a change, ask three questions and act on them in the same
commit:

1. Did I make something in here false? Fix it.
2. Did I prove something? Move its row in `STATUS.md` and say how.
3. Did I add a decision? It goes in `STATUS.md` under decisions, not here —
   this file records what *is*, not what was agreed.

If you cannot verify a claim, delete it rather than softening it. A hedge reads
as a fact to the next person.

**Two claims that were wrong for days**, as a warning about repeating what a doc
says without checking:

- **Recognisability is scored and used.** `Track.recognisability` exists, all 47
  corpus tracks carry a real hand-assigned value (0.12–0.98, none left at the
  default), and `_recog_weight()` multiplies the score in *all three* strategies.
  What does not exist is a separate "nicheness" concept, and nobody has checked
  whether the hand-assigned values are any good.
- **Repeats are already prevented within a run.** `DJState.played_ids` is passed
  to every strategy as an exclusion set and the fallback deck respects it. What
  is missing is memory *across* runs — a fresh process starts from a clean slate.
