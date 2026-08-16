# Slopify

**A wearable-style agent whose only feature is playing the worst possible music for the moment.** (No hardware exists; a camera, a screen share, or a video file stands in for the glasses.)

It watches what's around you, works out what the moment feels like and what the
setting implies, computes the opposites, and plays that. It talks to you, but
only to announce what it has done.
It will not take requests. It does not help with anything else.

Sunlit park with people reading → Drowning Pool, *Bodies*.
Toddler's birthday party → Johnny Cash, *Hurt*.
Silent library during exam week → Darude, *Sandstorm*.

---

## See it work in three commands

No API keys, no accounts. Everything below runs on the built-in mocks.

```bash
python -m venv .venv && .venv/bin/pip install -r requirements.txt   # one-time, ~2 min
.venv/bin/pytest -q                                                  # 225 tests, ~10 s
PYTHONPATH=src .venv/bin/python run.py --source replay --ticks 8 --no-hud
```

The third command replays canned scenes through the real pipeline and prints
each verdict with its reasoning — the park, the library and the birthday party
from the top of this file, decided live by the same graph the demo uses. With
no credentials set it says so and downgrades out loud:
`[config] player: 'spotify' requested but SPOTIFY_CLIENT_ID is unset -> using mock`.

For the full tour aimed at reviewers, see [EVALUATOR.md](EVALUATOR.md).

---

## Which doc do I want?

Three documents, one job each. **Don't add a fourth** — we had eight and they
drifted apart within a day.

| | |
|---|---|
| **README.md** | this file — what it does, how to run it, how it's built |
| **AGENTS.md** | the rules, the seams you plug into, the traps. Read before your first change. Symlinked as `CLAUDE.md`, so agents get it automatically |
| **STATUS.md** | what's actually done, and what's only *built but unproven*. **Update it when you finish something** |

Plus one README beside each part that ships on its own: `frontend/`,
`src/videofeed/`, `scripts/io/`.

README never says what's finished; STATUS never explains how anything works.
That's what stops them drifting apart.

---

## How it works, in plain language

Six steps, over and over, about every five seconds.

**1. Look.** Take a picture and listen to the last few seconds of sound.

**2. Has anything changed?** Compare against the last look. If the room is
different — someone walked in, it got loud, the lights changed — carry on to the
expensive thinking. If it's the same, skip it and reuse what we already worked
out.

Either way we still go to step 6, because "nothing changed" is useful
information too. It's the difference between *the scene is stable* and *we don't
know what the scene is*. Getting that wrong once deadlocked the whole thing on
calm footage: nothing ever played, because the rule that waits to see a change
twice never got its second look.

**It doesn't only look on a timer.** With video it also samples the moment the
picture cuts or the sound spikes — so a five-second rhythm doesn't mean missing
the door opening at second three. When something like that fires, we already
know the world changed, so we skip the checking and go straight to thinking.

**3. Understand the moment.** Describe what's happening: where we are, what
people are doing, how it feels, and traits of the setting. One description
covering everything, in one go.

**4. Flip it.** Invert both the feeling and the setting traits, then associate
those opposite traits with genres. Fast food can become inexpensive and casual
→ luxurious and formal → opera or classical.

**5. Pick the song.** Six different ideas of "worst" each propose candidates.
Then one final choice picks the funniest, and writes a line to say out loud.

**6. Queue it, or cut in.** Usually it lines the song up to play next. But if the
room changed a lot *and* the current song has already had a fair run, it cuts in
immediately — wrong music is much funnier while the moment is still happening.

### What it notices

All of this comes back in **one answer**, not one question per row. Asking
separately would cost more, take longer, and give more chances to fail.

| | What it means |
|---|---|
| Mood | Happy, tense, sad, calm |
| Speed | Fast or slow — pace, drums, how much is going on |
| Steady or not | A regular beat versus something loose, like jazz |
| Instruments and sounds | What a genre is made of |
| Colour | What colours are in the scene, and what they'd sound like |
| Recognisability | Scored per track, and it weights every strategy — the joke dies if nobody knows the song |
| Weather | **TEMPORARY** — would be looked up, not seen |

It also says how sure it is. Below 0.35 confidence, nothing happens.

### There is no "how wrong should it be" setting

It always fully flips the mood. There used to be a dial and it was removed: it
described something the system doesn't do. This reads a mood and inverts a mood,
and there's no meaningful halfway.

What we *do* have is a **measurement**. After it picks, we work out how far apart
the moment and the music turned out to be — `mismatch`, 0 to 1 — and show it.
A result, not a request. A test asserts the dial can't come back.

### What "worst" means, and what it doesn't

**Musically opposite to the moment.** Five mood axes — valence, arousal,
density, brightness, organicness — plus setting-only semantic opposites. It can
label a venue casual or formal; it never labels the people in it. The system
has no notion of anyone's race, sex, religion, politics or identity, and must
never acquire one.

It takes two things to be funny, and it needs both:

**The maths.** Every moment and every song is scored on the same qualities.
"Opposite" is flipping every score. Fast, free, explainable on one slide.

**The taste.** The maths alone gives boring answers — usually some obscure noise
record nobody has heard of. A genuinely funny choice has to be *specific* and
*recognised*: funeral music at a birthday party, a Christmas song in August.
Only something that understands culture spots that.

So the maths makes a shortlist and taste picks the winner. Never one alone.

The setting chain is inferred in the same structured perception call as the
mood; there is no fast-food, gallery, or other scenario lookup table. When the
model backend is unavailable, the offline fallback leaves those semantic fields
empty instead of pretending it inferred them.

The shortlist is sampled by score before the final judge chooses. A softmax
temperature of `0.20` keeps weak matches unlikely while allowing several strong
songs to rotate for the same mood. This happens after perception and inversion,
so it cannot change the scene mood, and it makes no Spotify request.

### How it's stopped from going haywire

- Lining up the next song is cheap. Cutting one off has to be earned: the room
  must have genuinely changed **and** the current song must have had a fair run.
- A song is safe from being cut for its first stretch, whatever happens.
- **It asks whether the *music* should change, not whether the room did.** Two
  rooms that call for the same wrong song keep the same wrong song. This is what
  stops it shuffling: before, a room that never changed still got a new track
  every ten seconds, because the picker was never allowed to re-pick what was
  already playing.
- **How sure it needs to be depends on how big the change is.** A moderate shift
  has to show up in two readings in a row. A dramatic one — the party ends, the
  lights come up — is acted on immediately, because waiting for a second opinion
  is how the joke arrives after the moment has gone.
- If it isn't sure what it's looking at, it does nothing.
- If any part breaks, a backup list of always-wrong songs plays anyway.

**The rule: it is never silent.** Silence is the only actual bug. Playing the
wrong thing is the product working correctly.

---

## Quickstart

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python scripts/build_seed_corpus.py     # writes data/corpus.seed.json
python run.py                           # then open http://127.0.0.1:8420/dj
```

Every external service degrades to a mock when its credentials or packages are
unavailable. The checked-in configuration selects Gemini perception and Spotify
playback; switch `perceive.backend` to `huggingface` for local CLIP, or select
the mock backends explicitly, in `config.yaml`.

```bash
python run.py --video clip.mp4                  # a recording, treated as live
python run.py --video clip.mp4 --realtime       # ...at its true speed
python run.py --video clip.mp4 --record demo1   # + write data/sessions/demo1.json
python run.py --source webcam                   # real camera + mic
python run.py --ticks 10 --no-hud               # bounded headless run
pytest tests/ -q                                # 225 tests
```

## Local video upload app

This path uses the perception backend selected in `config.yaml`. Gemini needs
`GOOGLE_API_KEY` in `.env`. The key-free option is `huggingface`, which uses the
local `openai/clip-vit-base-patch32` checkpoint; its first analysis downloads
the model and later runs use the local cache.

```bash
# terminal 1
pip install -r requirements.txt
python run.py --serve

# terminal 2
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000/demo`, choose a video, and wait for the result.
The browser sends the file to the local FastAPI server. The server samples one
frame every five seconds, reads the matching audio window, classifies the mood,
and sends each mood through the existing opposite music agent. The page keeps
the video in the browser and shows the chosen track at each timestamp.

When `player.backend` is `spotify`, the page verifies the Premium account and
configured device without starting sound, then shows **Spotify playback
connected** beside the device name. Pressing Play on the analyzed video starts
the chosen corpus track at each timeline marker; pausing or ending the video
pauses Spotify. Only corpus track IDs returned by the analyzer are accepted by
the playback endpoint. Without a Spotify player, analysis and replay still work
and the badge explains that playback is unavailable.

`ffmpeg` is optional. Install it and place it on `PATH` to include video audio.
Without it, the same flow runs with images, colour, blur, and motion only.

The upload endpoint accepts common video extensions, uses generated temporary
filenames, enforces a 200 MB limit, and removes each upload after analysis.
Change the limit with `hud.max_upload_mb` in `config.yaml`.

CLIP produces relative scores over this project's fixed mood taxonomy. These
scores are useful for a prototype, but they are not a clinical emotion reading
and they should be tested with representative demo footage before presentation.

### Implementation references

- [Hugging Face zero shot image classification](https://huggingface.co/docs/transformers/tasks/zero_shot_image_classification)
- [CLIP ViT B 32 model card](https://huggingface.co/openai/clip-vit-base-patch32)
- [OpenAI CLIP license](https://github.com/openai/CLIP/blob/main/LICENSE)
- [FastAPI file uploads](https://fastapi.tiangolo.com/tutorial/request-files/)
- [OpenCV video position properties](https://docs.opencv.org/4.9.0/d4/d15/group__videoio__flags__base.html)
- [MDN FormData](https://developer.mozilla.org/en-US/docs/Web/API/FormData)
- [OWASP file upload guidance](https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html)
- [Next.js July 2026 security release](https://nextjs.org/blog/july-2026-security-release)

### Two screens, one server

| | |
|---|---|
| `/dj` | **The presentation face.** An orb that takes on the room's colours, the spoken line in big type, now-playing with a queued/cut-in badge, and a compact reasoning ticker. This is what judges see. |
| `/` | **The engineering view.** Vibe-gap chart, scene injection, full event trace. This is what we debug with. |

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

### One script per feature

Each step of the pipeline is also a standalone script that reads JSON in and
writes JSON out, so two people can work on two steps at once, and any step can
be swapped without the others noticing.

```bash
python scripts/io/describe.py --text "a toddler's birthday party" \
  | python scripts/io/invert.py \
  | python scripts/io/choose.py \
  | python scripts/io/play.py
```

`describe.py` is the swappable one — if you want to try HuggingFace, or split
audio and video into separate models, that's the only file that changes. See
`scripts/io/README.md`.

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
                   ANTAGONIZE       fan-out: 6 competing theories of wrongness
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

**No dial for how wrong to be.** There used to be a `cruelty` setting. It was
removed: the product reads a mood and inverts a mood, and a knob labelled "how
far past inappropriate to go" described something else. How wrong a pick turned
out is measured after the fact (`Verdict.mismatch`, 0–1) and reported. An agent
whose premise is that it ignores you shouldn't take a parameter for how much to
ignore you.

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
| `src/badspotify/music/` | **the antipode engine**, corpus, six candidate strategies |
| `src/badspotify/agents/` | LangGraph wiring, the judge |
| `src/badspotify/dj/` | bounds, queue-vs-interrupt, the fallback ladder |
| `src/badspotify/players/` | mock / local files / Spotify + the search matcher |
| `src/badspotify/voice/` | ElevenLabs narrator |
| `src/badspotify/hud/` | FastAPI + websocket; `dj.html` and `index.html` |
| `src/badspotify/session.py` | records a run to JSON for the site |
| `src/badspotify/service.py` | `Engine` — one decision at a time, no loop. What the Gradio app and any future glasses app both sit on |
| `src/videofeed/` | standalone video sampler: samples on a clock **and** on events (scene cuts, audio onsets). Imports nothing from `badspotify` |
| `app.py` | Gradio surface — describe a scene, drop a photo, drop a video |
| `frontend/` | **the presentation site** (Next.js, separate from the agent) |
| `scripts/io/` | **one script per pipeline step** — JSON in, JSON out, pipeable |
| `scripts/` | corpus builder, Spotify setup, every-noise scraper |
| `src/badspotify/log.py` | diagnostics to stderr, so stdout stays pipeable |

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
strategies. Grow the corpus past 47 tracks or add a genuinely disagreeing
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
fine: we need stable geometry, not fresh charts. **Unverified against the live
page — run it and check the count before relying on it.**

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

The three tracks meet in one artefact: the recorded session file
(`src/badspotify/session.py` writes it, `frontend/lib/cues.ts` reads it). A
workflow's decisions, over media, rendered as the site's try-it screen — the
same JSON is all three tracks at once.

| Criterion | Where it's answered |
|---|---|
| Technical execution | Real graph with conditional edges; a change gate that cuts model calls; every backend degrades instead of crashing; 225 tests guarding specific live-demo failures |
| UX & intuition | A DJ character with a reacting orb, onboarding, one honest control, and a site that walks judges through the reasoning |
| Creativity | Geometric opposition *plus* a cultural judge; six competing theories of wrongness rather than one similarity score |
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
