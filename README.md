# bad spotify

**A wearable agent whose only feature is playing the worst possible music for the moment.**

It watches what's around you, works out what the moment feels like, computes the
opposite, and plays that. It talks to you, but only to announce what it has done.
It will not take requests. It does not help with anything else.

Sunlit park with people reading → Drowning Pool, *Bodies*.
Toddler's birthday party → Johnny Cash, *Hurt*.
Silent library during exam week → Darude, *Sandstorm*.

---

## Which doc do I want?

| | |
|---|---|
| **README.md** | this file — how to run it, how it's built, who owns what |
| **PIPELINE.md** | how it works, in plain language, no code. Start here if you're new |
| **STATUS.md** | what's actually done, and what's only *built but unproven*. **Update it when you finish something** |
| **frontend/README.md** | the site, and the one file that connects it to the agent |

Each file has one job. PIPELINE never says what's finished; STATUS never explains
how anything works. That's what stops them drifting apart.

---

## Quickstart

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python scripts/build_seed_corpus.py     # writes data/corpus.seed.json
python run.py                           # then open http://127.0.0.1:8420/dj
```

**Every backend runs on a mock by default.** A fresh clone with no API keys, no
Spotify account and no camera still runs the whole thing end to end. That's
deliberate — nobody should be blocked on credentials to work on their layer.
Swap in real backends one at a time via `config.yaml`.

```bash
python run.py --video clip.mp4                  # a recording, treated as live
python run.py --video clip.mp4 --realtime       # ...at its true speed
python run.py --video clip.mp4 --record demo1   # + write data/sessions/demo1.json
python run.py --source webcam                   # real camera + mic
python run.py --ticks 10 --no-hud               # bounded headless run
python run.py --cruelty 1.0                     # maximum hostility
pytest tests/ -q                                # 48 tests
```

### Two screens, one server

| | |
|---|---|
| `/dj` | **The presentation face.** An orb that takes on the room's colours, the spoken line in big type, now-playing with a queued/cut-in badge, and a compact reasoning ticker. This is what judges see. |
| `/` | **The engineering view.** Vibe-gap chart, cruelty dial, scene injection, full event trace. This is what we debug with. |

Keep both. The reasoning being visible is what separates this from a shuffle
button, and it's most of why the technical work reads as serious.

### Video as live

We don't have Ray-Bans, so we film something and feed the recording in as though
it were happening now. Nothing downstream knows the difference — same interface,
same timing, same decisions. It's also better than a live camera for presenting:
repeatable across rehearsals, and it can't fail on stage.

Needs `ffmpeg` on PATH for the audio track; without it, vision-only.

`--record NAME` writes every decision to `data/sessions/NAME.json` — which song,
**where in the video it starts**, and why. That file is what the site replays,
so the site needs no backend and no API keys.

### Spotify

Needs **Premium** — the Web API refuses playback control on free accounts.

```bash
# 1. make an app at https://developer.spotify.com/dashboard
#    add redirect URI: http://127.0.0.1:8888/callback
# 2. put the client id/secret in .env
# 3. open Spotify somewhere and press play on anything once
python scripts/spotify_setup.py
```

Six checks in order, stopping at the first real problem with an instruction
rather than a stack trace: credentials → login → Premium → device → resolve all
47 songs → play a test track out loud. Resolved URIs cache to
`data/spotify_uris.json`.

**Read the unresolved list.** Spotify search returns karaoke versions, tribute
bands, and different artists with the same song title — there's a filter for
that (`players/spotify_match.py`, 13 tests) but reality gets a vote. Fix
mismatches before demo day: correct the title in `scripts/build_seed_corpus.py`,
or paste a URI straight into the cache file.

### Sampling a video on its own

`src/videofeed/` is a standalone package: a video in, model-ready segments out.
Fixed cadence **plus** event triggers (scene cut, audio onset, motion, light
changes), with the audio window attached to each sample. It imports nothing from
this project, and the model side is a documented stub rather than a guess.

```bash
PYTHONPATH=src python -m videofeed clip.mp4 --interval 5 \
    --triggers scene-cut,audio-onset --out runs/demo1
```

Full docs: `src/videofeed/README.md`.

### The site

```bash
cd frontend && npm install && npm run dev   # http://localhost:3000/demo
```

Next.js, TypeScript, Tailwind. Static on purpose — it replays a recorded run
rather than calling the agent. See `frontend/README.md`.

### Going live

Copy `.env.example` to `.env`, fill in what you have, and flip the matching
`backend:` keys in `config.yaml` from `mock` to `gemini` / `elevenlabs` /
`spotify`. Anything missing degrades back to a mock instead of crashing.

---

## Architecture

```
  CAPTURE          a frame + the last few seconds of audio
     │             (webcam, or a video file pretending to be live)
     ▼
  CHANGE GATE      did the world change? local, ~1ms, no model call
     │
     ├── no ────▶  STABLE           reuse the last read.
     │                              Costs nothing, and still counts as
     │                              evidence — see the note below.
     │                                        │
     └── yes ───▶  PERCEIVE         1 Gemini call → the whole SceneRead
                        │
                        ▼
                   ANTAGONIZE       fan-out: 3 competing theories of wrongness
                        │
                        ▼
                   JUDGE            1 Gemini call: picks the funniest, writes
                        │           the line it says out loud
                        │                     │
                        └─────────┬───────────┘
                                  ▼
                                 DJ            hysteresis · cooldown · commitment
                                  │            → queue it, or cut in?
                                  ▼
                          speak → play → screens
```

Both paths end at the DJ. That matters: a quiet tick is not nothing, it's
evidence the scene is *stable*, which is exactly what the hysteresis rule is
waiting for. (Skipping the DJ on quiet ticks is what caused the deadlock
described at the bottom of this file.)

### Four decisions worth defending

**One perception call, not one agent per field.** Mood, tempo, meter and colour
all derive from the same frame. Four agents would buy 4× the cost, 4× the
failure surface and the latency of the slowest — for data one structured-output
call already returns. Agents split by *failure mode*, never by output field.

**Fan-out where the theories actually differ.** `genre_antipode` (wrong on every
axis), `tempo_clash` (wrong about energy and pulse), `lyrical_irony` (wrong in
meaning regardless of sound) produce genuinely different shortlists, and a judge
picks between them. That's a judge panel with real diversity, not parallelism
theatre.

**Geometry shortlists, culture chooses.** Reflection through the centre of the
vibe cube is deterministic, offline, instant and explainable in one slide — but
"most distant in vibe space" is often a noise record nobody knows. The true
opposite of a calm sunny park is *funeral doom*, or a Christmas song in August,
or Yakety Sax. Only a language model knows that. Distance gives defensibility,
the model gives the punchline, and we never use one alone.

**Queue is the default; interrupting is earned.** Cutting the music off needs
two things at once: the room genuinely changed, *and* the current track has had
a fair run. A system that interrupts constantly reads as broken; one that never
interrupts misses the joke, because wrong music is funniest while the moment is
still happening. The DJ decides per moment — it isn't a setting.

### Layout

| Path | What lives there |
|---|---|
| `src/badspotify/capture/` | `CaptureSource` interface — webcam, **video file**, replay, glasses stub — plus the change gate |
| `src/badspotify/perceive/` | Gemini scene read, local librosa audio features, text injection |
| `src/badspotify/music/` | **the antipode engine**, corpus, three candidate strategies |
| `src/badspotify/agents/` | LangGraph wiring, the judge |
| `src/badspotify/dj/` | bounds, queue-vs-interrupt, the fallback ladder |
| `src/badspotify/players/` | mock / local files / Spotify + the search matcher |
| `src/badspotify/voice/` | ElevenLabs narrator |
| `src/badspotify/hud/` | FastAPI + websocket; `dj.html` and `index.html` |
| `src/badspotify/session.py` | records a run to JSON for the site |
| `src/videofeed/` | **standalone**: samples a video on a cadence *and* on triggers (cuts, onsets, motion), attaches the audio, hands segments to whatever you plug in. Imports nothing from `badspotify` — see its own README |
| `frontend/` | **the presentation site** (Next.js, separate from the agent) |
| `scripts/` | corpus builder, Spotify setup, every-noise scraper |

---

## Splitting this across the team

Six workstreams with clean seams. Each can be built against mocks without
waiting on the others.

**1. Perception** — `perceive/`
Own the Gemini call and the prompt. The bar: accurate, calibrated, sub-second,
honest about `confidence`. Tune against real frames. Don't let this become four
calls.

**2. The joke engine** — `music/`
The highest-leverage work in the repo. Own `TABOO_RULES`, the corpus, and the
strategies. Grow the corpus past 47 tracks, add nicheness scores, maybe a fourth
strategy. Success is whether the room laughs, not any metric in this file.

**3. Reliability** — `dj/`, `agents/`
Own the bounds and the fallback ladder. The one unacceptable failure mode is
silence. Every path from a dead API back to *something terrible playing* is
yours.

**4. The agent's screens** — `hud/`
Own `/dj` and `/`. The DJ face is what judges watch; the engineering view is how
everyone else debugs. Both read the same event stream.

**5. Integration** — `players/`, `voice/`, `.env`
Own Spotify OAuth, device selection, ElevenLabs latency, audio ducking. Get
Premium sorted early — the OAuth loop is the most annoying hour in the project
and it's better spent on day one than on demo morning.

**6. The site** — `frontend/`
Own the presentation format. `lib/types.ts` is the contract with the agent; the
only thing crossing the boundary is a recorded session file.

---

## Constraints we already checked

**Meta Ray-Ban.** The Wearables Device Access Toolkit is real and exposes video,
photo, mic and audio out for Ray-Ban Meta Gen 1/2, Display, and the Oakley Meta
line — but it's Developer Preview, a **native iOS/Android SDK**, publishing is
disabled, and access is gated to AI-glasses-supported countries. So the port
isn't a Python import: it's a thin native app that owns the SDK session and
posts frames to `capture/glasses.py` over localhost. Everything above that file
is already hardware-agnostic. Audio *out* needs no SDK at all — the glasses are
a Bluetooth sink today.

**Spotify.** `audio-features`, `audio-analysis`, `recommendations` and
`related-artists` were restricted in Nov 2024 to apps already in extended quota
mode. New apps can't get them. Search, metadata and **playback control still
work**. So Spotify is our speaker, not our brain — all music intelligence lives
in our own vibe space. That division is a feature: the interesting part is ours
and the streaming is a swappable backend.

**Every Noise at Once.** `scripts/scrape_everynoise.py` pulls ~6000 genres with
2D coordinates out of the genre map's inline CSS — a free offline genre
embedding. The site's data is frozen (its maintainer left Spotify), which is
fine: we need stable geometry, not fresh charts. **Verified 13 Aug 2026: 6291
genres off the live page.** But its raw opposites are unusable as-is — it says
the opposite of death metal is `funk bh, cartoon, kikuyu pop`, which is
geometrically right and comedically dead. Nothing consumes it until there's a
recognisability filter in front of it. See `STATUS.md`.

**Twelve Labs.** Indexing is asynchronous and won't serve a five-second loop. If
we use it, it belongs at the *end*: index the session afterwards and close with
"here's every moment we ruined, with timestamps."

---

## Scaling the corpus

47 hand-picked tracks ship in `scripts/build_seed_corpus.py`. Hand-picked
because **the joke only lands if the judges recognise the song** — breadth is
worthless, recognisability is everything. When you outgrow them:

- **MTG-Jamendo** — 55k tracks, 59 mood/theme tags, CC-licensed actual audio
- **Deezer Mood Detection Dataset** — valence/arousal, mapped to MSD ids
- **Every Noise** — genre coordinates via the scraper

Keep `recognisability` honest as it grows. An obscure track that's technically
the perfect opposite is a worse pick than a famous one that's merely very wrong.

---

## Tracks and criteria

Submitting into **Workflows** (the agent graph is the product), **Media** (the
output is a generated audiovisual experience) and **Design** (the DJ face and
the site are how the agent's mind is made legible).

| Criterion | Where it's answered |
|---|---|
| Technical execution | Real graph with conditional edges; a change gate that cuts model calls; every backend degrades instead of crashing; 48 tests guarding specific live-demo failures |
| UX & intuition | A DJ character with a reacting orb, onboarding, one honest control, and a site that walks judges through the reasoning |
| Creativity | Geometric opposition *plus* a cultural judge; three competing theories of wrongness rather than one similarity score |
| Originality | An assistant that is deliberately useless. The failure mode and the feature are the same thing, which is why it holds up live |

---

## Known gaps

See `STATUS.md` for the current state of each part. The standing ones:

- No session memory — it'll repeat a joke on a long run
- Nobody has timed the real thing end to end
- Nicheness is agreed as an idea but isn't scored or used anywhere
- `capture/glasses.py` is a stub — needs the native companion app
- The corpus has no audio files; local playback needs `data/library/` populated

**One bug worth knowing about**, because the shape of it could recur: a calm
scene used to deadlock. The change gate suppressed repeat reads to save model
calls, but the "see it twice before acting" rule needed exactly those repeats —
so on quiet footage nothing ever played. Fixed by treating a quiet tick as
positive evidence the scene is stable, which costs no model call.
