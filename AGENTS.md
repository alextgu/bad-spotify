# AGENTS.md — the source of truth for anyone (or anything) working in this repo

`CLAUDE.md` is a symlink to this file. Same rules for every agent and every
human. If you change how the project works, change this file in the same commit.

**The rule that matters most: everything in here is checkable, and was checked.**
Nothing below is aspiration or plan. If you can't verify a claim by running the
command next to it, it does not belong here — put it in `STATUS.md` (state) or
`PIPELINE.md` (how it works) instead.

Last verified: **14 Aug 2026**, by running the commands quoted throughout.

---

## What this is

A wearable-style agent whose only feature is playing the worst possible music
for the moment it is in. It reads a scene, computes the musical opposite of that
scene's mood, picks a track from a hand-curated corpus, and announces it.

**"Worst" means musically opposite in mood, and nothing else.** Five axes —
`valence, arousal, density, brightness, organicness` (`schemas.py:16`). The
system has no notion of anyone's race, sex, religion, politics or identity, and
must never acquire one. There is no "how far to go" dial and there must not be
one; a test asserts this (`tests/test_pipeline.py::test_reflection_has_no_dial`).

---

## Which document owns what

| File | Owns | Does not contain |
|---|---|---|
| `AGENTS.md` (this) | verified facts, commands, hard rules, and what is *not* settled | how anything works internally |
| `README.md` | how to run it, architecture, who owns which workstream | claims about what is finished |
| `PIPELINE.md` | how it works in plain language, no code | what is built vs unbuilt |
| `STATUS.md` | **state**: Done / Built-unproven / Not started, and how each was proven | explanations |
| `src/videofeed/README.md` | the standalone sampler package | anything about the agent |
| `frontend/README.md` | the site | anything about the agent |

Keeping these separate is the only reason they stay accurate. Don't merge them.

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

# the sampler, standalone
PYTHONPATH=src python -m videofeed clip.mp4 --interval 5 \
    --triggers scene-cut,audio-onset --out runs/demo1

# the site
cd frontend && npm install && npm run dev     # localhost:3000, /demo
cd frontend && npx tsc --noEmit && npm run build
```

`pytest` and `gradio` are in `requirements.txt`. `ffmpeg` on PATH is needed for
video audio; without it the sampler runs vision-only rather than failing.

---

## Test inventory (83, verified by `--collect-only`)

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

## What exists, in code

Three entry points. They share one graph.

```
run.py            the live loop: capture -> gate -> perceive -> antagonize ->
                  judge -> dj -> play, plus the HUD. graph.tick(obs).
app.py            Gradio, four tabs. Sits on service.Engine.
python -m videofeed   the sampler alone. Imports nothing from badspotify.
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
(`music/strategies.py:84`). They fan out concurrently and a judge picks between
them.

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
   makes it true, and say *how* something was proven, not just that it was.
5. **Nothing plays out loud from a hosted surface by default.** `app.py` uses
   the mock player unless `--play` is passed.
6. **Ask before deleting.** Prefer moving to `_review/` (git-ignored).

---

## Not settled — do not invent

Genuinely open. If you need one of these decided, ask; do not write it into a
doc as though it were agreed.

- **Which surface is *the* demo.** Three exist now — the live loop with `/dj`,
  the Gradio app, and the static site replaying a recording. `STATUS.md` records
  a 13 Aug decision to demo a video file through `/dj`; the Gradio app arrived
  after that and no decision has been recorded about it.
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

## Two claims that were wrong, now corrected

Both were in `STATUS.md` and both were repeated for days. Check before you
repeat something.

- **Recognisability is scored and used.** `Track.recognisability` exists
  (`schemas.py:103`), all 47 corpus tracks carry a real value (0.12–0.98, no
  defaults), and `_recog_weight()` multiplies the score in *all three*
  strategies (`strategies.py:24,37,54,74`). What does not exist is a separate
  "nicheness" concept, and nobody has checked whether the hand-assigned values
  are any good.
- **Repeats are already prevented within a run.** `DJState.played_ids` is passed
  to every strategy as an exclusion set and the fallback deck respects it
  (`dj/controller.py:32,162,181`). What is missing is memory *across* runs — a
  fresh process starts from a clean slate.

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
