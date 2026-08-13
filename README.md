# bad spotify

**A wearable agent whose only feature is playing the worst possible music for the moment.**

It watches what's around you, works out what the moment feels like, computes the
opposite, and plays that. It talks to you, but only to announce what it has done.
It will not take requests. It does not help with anything else.

Sunlit park with people reading → Drowning Pool, *Bodies*.
Toddler's birthday party → Johnny Cash, *Hurt*.
Silent library during exam week → Darude, *Sandstorm*.

---

## Quickstart

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python scripts/build_seed_corpus.py     # writes data/corpus.seed.json
python run.py                           # HUD at http://127.0.0.1:8420
```

**Every backend runs on a mock by default.** A fresh clone with no API keys, no
Spotify account and no camera still runs the entire graph end to end. That is
deliberate — nobody on the team should be blocked on credentials to work on
their layer. Swap in real backends one at a time via `config.yaml`.

```bash
python run.py --source webcam        # real camera + mic
python run.py --ticks 10 --no-hud    # bounded headless run
python run.py --cruelty 1.0          # maximum hostility
pytest tests/ -q                     # 8 tests, all guard a specific demo failure
```

To go live, copy `.env.example` to `.env`, fill in what you have, and flip the
matching `backend:` keys in `config.yaml` from `mock` to `gemini` / `elevenlabs`
/ `spotify`. Anything missing silently degrades back to a mock instead of
crashing.

---

## Architecture

```
capture ──▶ [change gate] ──no change──▶ stop
                 │                          (local, ~1ms, no model call)
              change
                 ▼
            PERCEIVE          1 Gemini Flash call → the whole SceneRead
                 ▼
           ANTAGONIZE         fan-out: 3 competing theories of wrongness
                 ▼
             JUDGE            1 Gemini call: picks the funniest, writes the quip
                 ▼
              DJ              bounds: cooldown / commitment / hysteresis
                 ▼
         speak → play → HUD
```

### Three decisions worth defending

**One perception call, not one agent per field.** Mood, tempo, meter and colour
all derive from the same frame. Four agents would buy 4× the cost, 4× the
failure surface and the latency of the slowest — for data one structured-output
call already returns. Agents are split by *failure mode*, never by output field.

**Fan-out where the theories actually differ.** `genre_antipode` (wrong on every
axis), `tempo_clash` (wrong about energy and pulse), `lyrical_irony` (wrong in
meaning regardless of sound) produce genuinely different shortlists. A judge then
picks. That is a judge panel with real diversity, not parallelism theatre.

**Geometry shortlists, culture chooses.** Reflection through the centre of the
vibe cube is deterministic, offline, instant and explainable in one slide — but
"most distant in vibe space" is often a noise record nobody knows. The true
opposite of a calm sunny park is *funeral doom*, or a Christmas song in August,
or Yakety Sax. Only a language model knows that. So distance gives
defensibility, the LLM gives the punchline, and we never use one alone.

### Layout

| Path | What lives there |
|---|---|
| `src/badspotify/capture/` | `CaptureSource` interface, webcam, replay, glasses stub, change gate |
| `src/badspotify/perceive/` | Gemini scene read, local librosa audio features, text injection |
| `src/badspotify/music/` | **the antipode engine**, corpus, three candidate strategies |
| `src/badspotify/agents/` | LangGraph wiring, the judge |
| `src/badspotify/dj/` | bounds and the fallback ladder |
| `src/badspotify/players/` | mock / local files / Spotify |
| `src/badspotify/voice/` | ElevenLabs narrator |
| `src/badspotify/hud/` | FastAPI + websocket, the product surface |
| `scripts/` | seed corpus builder, every-noise genre-map scraper |

---

## Splitting this across the team

Five workstreams with clean seams. Each one can be built against mocks without
waiting on the others.

**1. Perception** — `perceive/`
Own the Gemini call and the prompt. The bar: accurate, calibrated, sub-second,
and honest about `confidence`. Tune against real frames from a phone. Do not let
this become four calls.

**2. The joke engine** — `music/`
The highest-leverage work in the repo. Own `TABOO_RULES`, the corpus, and the
strategies. Grow the corpus past the 47 seed tracks and add a fourth strategy.
Success is measured by whether the room laughs, not by any metric in this file.

**3. Reliability** — `dj/`, `agents/`
Own the bounds and the fallback ladder. The one unacceptable failure mode is
silence. Every path from a dead API back to *something terrible playing* is
yours. Add retries, timeouts, and a session recorder.

**4. Interface** — `hud/`
UX is a quarter of the score and this is the whole of it. Own the onboarding
flow, the reasoning trace, and the scene-injection stage button. Add the camera
preview and a session recap screen.

**5. Integration** — `players/`, `voice/`, `.env`
Own Spotify OAuth, device selection, ElevenLabs latency and the audio ducking.
Get a Premium account early; the OAuth loop is the most annoying hour in the
project and it is better spent on day one than on demo morning.

---

## Constraints we already checked

**Meta Ray-Ban.** The Wearables Device Access Toolkit is real and exposes video,
photo, mic and audio out for Ray-Ban Meta Gen 1/2, Display, and the Oakley Meta
line — but it is Developer Preview, a **native iOS/Android SDK**, publishing is
disabled, and access is gated to AI-glasses-supported countries. So the port is
not a Python import: it is a thin native app that owns the SDK session and posts
frames to `capture/glasses.py` over localhost. Everything above that file is
already hardware-agnostic. Audio *out* needs no SDK at all — the glasses are a
Bluetooth sink today.

**Spotify.** `audio-features`, `audio-analysis`, `recommendations` and
`related-artists` were restricted in Nov 2024 to apps already in extended quota
mode. New apps cannot get them. Search, metadata and **playback control still
work**. So Spotify is our speaker, not our brain — all music intelligence lives
in our own vibe space. That division is a feature: the interesting part is ours
and the streaming is a swappable backend.

**Every Noise at Once.** `scripts/scrape_everynoise.py` pulls ~6000 genres with
2D coordinates out of the genre map's inline CSS — a free offline genre
embedding. The site's data is frozen (its maintainer left Spotify), which is
fine: we need stable geometry, not fresh charts.

**Twelve Labs.** Indexing is asynchronous and will not serve a 5-second loop.
If we use it, it belongs at the *end*: record the session, index it after, and
close the demo with "here is every moment we ruined, with timestamps."

---

## Scaling the corpus

47 hand-curated tracks ship in `scripts/build_seed_corpus.py`. They are
hand-picked because **the joke only lands if the judges recognise the song** —
breadth is worthless, recognisability is everything. When you outgrow them:

- **MTG-Jamendo** — 55k tracks, 59 mood/theme tags, CC-licensed actual audio
- **Deezer Mood Detection Dataset** — valence/arousal, mapped to MSD ids
- **Every Noise** — genre coordinates via the scraper

Keep `recognisability` honest as you grow. An obscure track that is technically
the perfect opposite is a worse pick than a famous one that is merely very wrong.

---

## Tracks and criteria

Submitting into **Workflows** (the agent graph is the product), **Media** (the
output is a generated audiovisual experience) and **Design** (the HUD is how the
agent's mind is made legible).

| Criterion | Where it's answered |
|---|---|
| Technical execution | Real graph with conditional edges; change gate cuts model calls; every backend degrades instead of crashing; 8 tests guarding specific live-demo failures |
| UX & intuition | Onboarding flow, live reasoning trace, one honest control (cruelty), scene injection so the demo never depends on luck |
| Creativity | Geometric opposition *plus* a cultural judge; three competing theories of wrongness rather than one similarity score |
| Originality | An assistant that is deliberately useless. The failure mode and the feature are the same thing, which is why it holds up live |

---

## Known gaps

- `capture/glasses.py` is a stub — needs the native companion app
- Corpus has no audio files; local playback needs `data/library/` populated
- No session memory yet: it will happily repeat a joke across a long run
- The everynoise scraper is unverified against the live page — run it and check
  the count before relying on it
