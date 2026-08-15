# EVALUATOR.md — a tour for reviewers

This file organises evidence. It tells you where things are and how to check
them; the judging is yours.

## What this is

Slopify is a wearable-style agent that reads the scene in front of a camera —
setting, activity, mood, confidence — inverts what it finds, and plays the
least appropriate song it can justify, showing its reasoning as it goes. It
deliberately does **not** try to pick good music, and no glasses hardware
exists: a webcam, a screen share, or a video file stands in for the wearable.

## Verify it yourself — three commands, no API keys

```bash
python -m venv .venv && .venv/bin/pip install -r requirements.txt   # one-time, ~2 min
.venv/bin/pytest -q                        # 222 tests, ~10 s on a laptop
PYTHONPATH=src .venv/bin/python run.py --source replay --ticks 8 --no-hud
```

- The test count is regenerable: `.venv/bin/pytest --collect-only -q` → `222 tests collected`.
- The third command replays canned scenes through the production graph and
  prints each verdict with its reasoning (~15 s). With no credentials it
  downgrades out loud — you will see
  `[config] player: 'spotify' requested but SPOTIFY_CLIENT_ID is unset -> using mock`
  (emitted by `src/badspotify/config.py:56`), then
  `backends: … perceive=mock judge=mock player=mock`.
- The site: `cd frontend && npm install && npm run dev` → localhost:3000. The
  try-it screen replays recorded sessions from `frontend/public/sessions/`
  with no backend — three of them from real filmed clips run through the live
  model on 15 Aug (`STATUS.md`, “Reading a photo into a description: Done”).

## Five things worth looking at

1. **Measured thresholds, with the measurement written beside the number.**
   `config.yaml:93-97`: sensor jitter moves the music target ≤ ~0.23 and flips
   the top pick 37% of the time; the smallest genuine scene change moves it
   0.56 (median 0.84); the DJ deadband sits in the gap at 0.30. Same numbers
   restated where they are used, `src/badspotify/dj/controller.py:61`.
   Guarded by `tests/test_dj_timing.py` (19 collected).

2. **The degradation chain.** Every backend — perception, judge, player,
   voice — drops to a working stand-in when its dependency or credential is
   missing, and says so on stderr rather than silently
   (`src/badspotify/config.py:56`). Under everything sits a pre-picked
   fallback deck (`src/badspotify/dj/controller.py`). Proof is the scrubbed-env
   run above; `tests/test_service.py` also asserts hosted surfaces never take
   the speakers by default.

3. **The confidence floor.** Below 0.35 the system does nothing
   (`config.yaml:103` → `dj/controller.py:75,90`). Pointed at an unreadable
   frame, the live model reported “obstructed or blocked camera view” at 0.10
   and the DJ correctly refused to act (recorded in `STATUS.md`, “Gemini is
   real now”).

4. **Strategies that genuinely disagree.** Six theories of “wrong” fan out and
   a judge picks (`src/badspotify/music/strategies.py`, `REGISTRY`, 6
   entries). Disagreement is asserted, not assumed:
   `tests/test_register_clash.py:68 test_it_disagrees_with_the_acoustic_strategy`,
   and `tests/test_service.py test_the_park_and_the_library_disagree`. The
   design refusal is also tested: there is no “how wrong” dial, and
   `tests/test_pipeline.py:32 test_reflection_has_no_dial` fails if one appears.

5. **One artefact where the three tracks meet.** `session.py` records a
   workflow's decisions over media; `frontend/lib/cues.ts` renders that same
   JSON as the site's try-it screen, losing candidates and scores included.
   Workflow → Media → Design, one file (`frontend/public/sessions/sample.json`).

## Where the criteria are met

**Technical execution.** A LangGraph pipeline with conditional edges and a
sequential fallback with identical semantics (`src/badspotify/agents/graph.py`);
a change gate that refuses to spend model calls on an unchanged scene
(`src/badspotify/capture/gate.py`); 222 tests of which roughly 87% assert
behaviour rather than constants (365 asserts, 46 literal comparisons — counted
by grep, approximate). Perception ran against the live model at a measured
1.17 s median (4 models benchmarked, 3 calls each, `STATUS.md`).

**UX & intuition.** The reasoning is on every surface: the HUD ticker
(`src/badspotify/hud/`), the site's try-it panel with the losing candidates
(`frontend/components/SectionTryIt.tsx`), and the session replay. Controls
that don't work yet are visibly disabled and labelled, never wired to do
something else (`SectionTryIt.tsx`, the upload gate). Reduced motion is
honoured in every animated component (`grep -r motion-safe frontend/components`).

**Creativity.** The inversion is two systems arguing: geometric reflection
through a five-axis mood cube gives a defensible target instantly
(`src/badspotify/music/vibe.py`), and a model supplies the cultural half —
only it knows the true opposite of a sunlit park is funeral doom
(`semantic_opposite`, `strategies.py`). Six strategies compete per decision;
a softmax sampler at temperature 0.20 keeps one room from producing one
answer forever (`agents/judge.py`).

**Originality.** An agent whose failure mode and feature are the same thing.
The refusal to add a cruelty dial is enforced by a test
(`test_reflection_has_no_dial`), and the corpus carries hand-assigned
recognisability 0.12–0.98 (`data/corpus.seed.json`, 47 tracks) because the
joke depends on the audience knowing the song — a design constraint, not a
model choice.

## What isn't done

- **No glasses.** `capture/glasses.py` is a stub; nothing wearable exists.
- **Spotify playback is unproven live.** Built and tested against a stand-in
  (`tests/test_spotify_player.py`, 16 tests); no track has been heard from a
  real speaker yet.
- **Some site media is placeholder.** The hero film and demo film are labelled
  slots (`frontend/lib/site.ts`). The try-it clips are real: three filmed
  videos in `frontend/public/videos/` with sessions produced by the live
  model. The original `sample.mp4` remains synthetic.
- **The judge's live path is dormant.** `judge.backend: mock` in
  `config.yaml`; its configured model measured 5–8 s against a 4 s timeout, so
  enabling it as-is would silently fall back (noted in `config.yaml:70`).
- **Upload requires the local agent**; the button says so instead of playing
  the sample.

## Sixty seconds only?

Run the third command from the top block, watch three scenes get three wrong
songs with reasons, then open `config.yaml:93-97` — the measured numbers with
their measurement — and `STATUS.md` for what is and isn't proven.
