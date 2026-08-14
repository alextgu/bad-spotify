# Prompt for Claude Code

Copy everything below the line into Claude Code from the repo root.

---

I'm working on a hackathon project in this repo. Read `README.md`, `PIPELINE.md`
and `STATUS.md` first — they explain what this is, how it works, and what's
actually finished. `STATUS.md` is the source of truth for state, and it uses
three levels: **Done** (someone watched it work for real), **Built, unproven**
(code exists, runs on mocks, nobody has pointed it at reality), and **Not
started**.

Almost everything is currently "Built, unproven". Your job is to move as much of
it as possible to "Done", and to clean up what we no longer need.

## Ground rules

1. **Update `STATUS.md` as you go.** When you prove something works, change its
   row and say how you proved it. When you find something broken, say so there.
   This file is how the team stays in sync — don't let it drift.

2. **Do not delete the mock backends.** Every model, player and voice has a mock
   that the system falls back to. They look like dead code and they are not:
   they're why a teammate can clone this with no API keys and still run the whole
   pipeline. Same for the fallback ladder in `dj/controller.py`.

3. **Never let it go silent.** The one unacceptable failure is silence. If you
   change anything in the DJ or player layers, confirm the fallback still fires.

4. **Ask before deleting anything you're unsure about.** Prefer moving to a
   `_review/` folder over deleting.

## Part 1 — verify what we built

Work through these in order and record the result in `STATUS.md`. Stop and tell
me if something fails rather than working around it.

**a. The test suite.** `pytest tests/ -q` — expect 48 passing. If any fail, that
is the first thing to fix.

**b. Clean install.** In a fresh venv, `pip install -r requirements.txt`, then
`python scripts/build_seed_corpus.py`, then `python run.py --ticks 6 --no-hud`.
You should see it choose Drowning Pool for a park and Sandstorm for a library.

**c. Both screens.** `python run.py`, then open `http://127.0.0.1:8420/dj` and
`http://127.0.0.1:8420/`. On `/dj` the orb should take the scene's colours and
the reasoning ticker should fill. On `/` use the scene-injection box — type
"a hospital waiting room at 3am" and confirm the whole pipeline runs.

**d. Video as input.** Find or record a real video (10–60s, with sound), then:
`python run.py --video yourclip.mp4 --record demo1`.
Check `data/sessions/demo1.json` — does `played.at_video_time` line up with what
actually happens in the footage? Needs `ffmpeg` on PATH.

**e. The site.** `cd frontend && npm install && npm run dev`. Check the landing
page at `/` and the demo ground at `/demo`. Copy your real clip to
`frontend/public/videos/sample.mp4` and your recording to
`frontend/public/sessions/sample.json`, then confirm the cards appear at the
right moments as the video plays.

**f. Gemini perception.** Set `GOOGLE_API_KEY` in `.env`, flip `perceive.backend`
and `judge.backend` to `gemini` in `config.yaml`, and run against real photos.
**This is the highest-value verification in the list** — everything downstream is
judged on whether the scene descriptions are actually accurate. Check that
`confidence` drops when the image is ambiguous. Measure how long the call takes
and put the real number in `STATUS.md`; the timeout is currently set to 4s and
nobody has checked whether that's generous or tight.

**g. Spotify.** `python scripts/spotify_setup.py`. Needs Premium, a Spotify app
at developer.spotify.com with redirect URI `http://127.0.0.1:8888/callback`, and
the Spotify app awake (press play on something first). **Read the unresolved
list** — some songs won't be findable. For each one, either fix the title in
`scripts/build_seed_corpus.py` or paste a URI into `data/spotify_uris.json`.

**h. The voice.** Set `ELEVENLABS_API_KEY`, flip `voice.backend` to `elevenlabs`.
Confirm the line is spoken over the music and the music ducks underneath. Note
the latency — if the quip lands after the song is already going, that's a bug
worth reporting.

## Part 2 — clean up

Delete or remove these, checking each is really unused first:

- `_to_delete/` — my leftovers from moving files onto this machine. Safe.
- `HANDOFF_PROMPT.md` — this file, once you've started.
- `frontend/components/.gitkeep` — the folder has real components now.
- `frontend/public/videos/sample.mp4` — an 88KB green placeholder. Replace with
  real footage rather than deleting outright, or `/demo` breaks.
- `frontend/public/sessions/sample.json` — recorded from a synthetic video, so
  it's meaningless. Replace with a real recording.
- Any `__pycache__/`, `.pytest_cache/`, `.next/` that got committed.

Then check whether these are genuinely earning their place, and tell me what you
think before removing:

- `src/badspotify/capture/replay.py` — predates `video.py` and may now be
  redundant. It is the default source in `config.yaml` and needs no video file,
  so it's useful for a zero-setup run. Argue it either way, don't just delete.
- `scripts/scrape_everynoise.py` — written but never verified against the live
  page, and nothing consumes its output. Either make something use it or cut it.
- `run.py --turbo` — collapses the DJ timing bounds for fast test runs. Dev-only.

## Part 3 — what's actually missing

In rough priority order:

1. **The pipeline diagram** — `frontend/components/PipelineDiagram.tsx` is a
   placeholder. The six steps are listed in the file as a comment. Inline SVG,
   so it scales on a projector.
2. **The name** — currently a placeholder in `frontend/lib/brand.ts`. It should
   play off "DJ". Changing `brand.name` updates everything. Note that Spotify's
   terms don't allow "Spotify" in a product name, so the repo's working title
   can't ship publicly.
3. **Nicheness** — agreed as an input but not scored or used anywhere. See the
   note in `PIPELINE.md` about why obscure isn't automatically funnier.
4. **Session memory** — it will repeat the same joke on a long run.
5. **A camera preview** on the screens, and an end-of-session recap.

## What I care about

The joke only works if judges *recognise* the song, and the reasoning being
visible on screen is what separates this from a shuffle button. If you're
choosing between two options, pick the one that protects those two things.
