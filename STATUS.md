# Status

**Update this file when you finish something.** One line is enough. It's the
only place that says what's actually true right now.

Three states, and the middle one matters most:

| | Means |
|---|---|
| **Done** | Built, and someone has watched it work for real |
| **Built, unproven** | The code exists and runs on fake input. Nobody has pointed it at the real thing yet. **Assume it's broken until someone checks.** |
| **Not started** | — |

Last updated: 14 Aug 2026

---

## Where we are

| Part | State | Who |
|---|---|---|
| The loop holding it all together | Done | |
| Deciding when to change the song | Done — reworked 14 Aug, see below | |
| Backup list when things break | Done | |
| Finding songs on Spotify | Built, unproven | |
| Playing songs on Spotify | Built, unproven | |
| Reading a photo into a description | Gemini proven live 14 Aug on synthetic frames; **still unproven on real footage** | |
| Working out the opposite | Built, unproven | |
| The song list (47 songs) | Built, unproven | |
| Picking the funniest one | Built, unproven | |
| The voice | Scoped down 14 Aug | Nelson (`6OzrBCQf8cjERkYgzSg8`), listened to and approved. **Not in the live loop**: one greeting at startup, and pre-rendered clips on the site. That deletes the latency, ducking and mid-song-interrupt risks entirely — none of them can bite a line spoken before the music starts. Still needs a key to render the site's three clips |
| Video file as input | Built, unproven — now sampled by `videofeed` | |
| Recording a run for the site | Built, unproven | |
| Screens — DJ face and engineering view | Built, unproven | |
| Site — scaffold + demo ground | Built, unproven | |
| Site — launch page | Built, unproven | |
| Site — pipeline diagram | Done — watched it render at 1440px and at a 360px container; six steps, the gate's skip-back edge, and the three-strategy fan-out all draw. Inline SVG, no dependency. `tsc --noEmit` and `next build` pass | |
| Local video upload and mood timeline | Built, unproven | |
| Video sampler (`src/videofeed/`) | Done — 17 tests, incl. a real generated clip | |
| Engine (`service.py`) — one decision, no loop | Built, unproven | |
| Gradio app (`app.py`) | Built, unproven | |
| Naming and logo | Placeholder in `frontend/lib/brand.ts` | |
| Glasses | Not started — and not needed | |

"Built, unproven" is not a criticism. Everything was deliberately built to run
on stand-ins so nobody was blocked on accounts and hardware. But it does mean
**nothing has been seen working end to end with real accounts yet**, and that's
the single biggest risk to the demo.

---

## Done

- **The loop.** Look → check if anything changed → understand → flip it → pick a
  song → queue or cut in. Runs end to end today with fake versions of every piece.
- **When to change the song.** Won't thrash. Needs to see a change twice before
  reacting. Ignores itself when unsure. Queues by default, only cuts the music
  off when the room really changed *and* the current song has had a fair run.
- **Backup list.** If anything upstream dies, a pre-picked list of always-wrong
  songs plays anyway. It is never silent.
- **Tests.** 83 of them, each guarding a specific way the demo could break.
- **Timeouts on the model calls.** A slow answer is abandoned and retried
  rather than freezing the loop. A late answer is worth less than a fast fallback.

## What just changed

**Gemini is real now, and the timeout was hiding it.** A key finally existed, so
the perception path ran against the live API for the first time. It works — it
returns schema-valid JSON and is honest about what it can't see (pointed at
unreadable frames it said "obstructed or blocked camera view" at confidence 0.10
and the DJ correctly did nothing). But `timeout_s: 4.0` was **below what the old
model actually took**: `gemini-2.5-flash` measured 5–8s, so every call would have
timed out and fallen back to a canned read, silently, and looked like it was
working. Now on `gemini-3.5-flash-lite` at a measured **1.17s median** (4 models
benchmarked, 3 calls each), timeout 3.0s.
*Proven by:* running `run.py --ticks 12` and watching `via gemini` with
1525–1950ms latencies in the tick output.
*Still unknown:* whether the descriptions are any good on real footage. Every
frame it has seen was synthetic.

**The song stops changing when nothing changes.** The DJ used to ask "should I
act?" *after* paying for perception, three strategies and a judge — and then
acted anyway, because `played_ids` excludes whatever is playing, so the judge was
forced to propose a new track every pass and the "already playing" guard could
never fire. It now gates on the **antivibe target** rather than the raw scene,
and asks before the expensive work: two rooms that invert to the same music
don't cost a track.
*Proven by:* a scene held perfectly constant for 62s went from **6 tracks to 1**,
and a hard cut is still answered within one read (2.5s). 11 new tests in
`tests/test_dj_timing.py`; 120 pass.
*Thresholds are measured, not taste:* jitter moves the target ≤0.23 and flips
the top pick 37% of the time; the smallest real scene change moves it 0.56.
The deadband sits in that gap at 0.30.

**Three gaps that made the repo fail its own tests are closed.**
`EventBus.unsubscribe` (without it every `watch()` leaked a recorder onto a
module-level bus), `graph.decide_from_scene` (so the Gradio app runs the real
compiled graph instead of a second hand-rolled pipeline), and `force` — which
was being set but silently dropped, because LangGraph discards state keys that
aren't declared on the TypedDict.

**The local video upload path is built.** FastAPI accepts a bounded temporary
video, samples it through the current video source, and returns a mood and music
timeline to `/demo`. Stable mood samples keep the current song choice. A new
choice needs a different mood and enough vibe distance, and carries a two-second
crossfade marker. Four focused tests pass, all 83 project tests pass, and the
frontend type check and production build pass. It has been tried with rain footage.

## Built, but nobody has run it for real

Ordered by how badly it hurts if it turns out broken.

**1. Spotify — playing songs**
There's a one-command setup (`python scripts/spotify_setup.py`) that logs in,
checks the account is Premium, finds a speaker, looks up all 47 songs in advance,
tells you which ones it couldn't find, and plays a test track.
*To prove it:* run that script and hear a song come out of a speaker.
*Already covered:* 15 tests run the player against a stand-in Spotify — free
accounts, no devices awake, the named device missing, karaoke results, queue vs
interrupt, and a device falling asleep mid-call. The logic is sound.
*Still unknown:* whether real search returns what we expect for our 47 songs.
**Read the unresolved list when you run it.**

**2. Reading a photo**
Returns canned answers right now. Never been pointed at a real camera or a real
photo.
*To prove it:* show it five real photos and check the descriptions match.

**3. Picking the song**
Works, but only on the canned descriptions.
*To prove it:* run it on real photos and see whether the picks are funny.

**4. The voice**
Never run with a real account.
*To prove it:* hear it say a line out loud, over music, without lagging.

**5. The screen**
Two of them now, on the same server:
`/dj` is the presentation face — a reacting orb that takes on the room's colours,
the spoken line in big type, now-playing, and a compact reasoning ticker.
`/` is the engineering view we already had. Keep both: judges see the character,
we see the wiring.
*To prove it:* watch it drive off a real video on the projector.

**6. Video as input**
Feeds a recording in as though it were live — samples a frame every few seconds,
pulls the matching audio out with ffmpeg, and reports where in the video it is.
Tested against a generated clip, never against real footage.
*To prove it:* run it on an actual video someone filmed.
*Needs:* ffmpeg installed, otherwise it runs vision-only.

**7. The site**
`frontend/` — Next.js, TypeScript, Tailwind. Builds clean.
The launch page has its sections in the agreed order; the visual layer is being
restarted and is not described anywhere on purpose.
The demo ground works: it replays a recorded run against the video and pops up
each decision where the song lands.
Still missing: the real name, and the new look.
*To prove it:* drop in real footage and a real recording, and walk someone through it.

**8. Recording a run**
`--record NAME` writes every decision to `data/sessions/NAME.json` — which song,
where in the video it starts, and why. This is what the presentation site will
read, so the site needs no backend and no keys.
*To prove it:* record a real clip and check the timings line up with the footage.

---

## The demo plan

Decided 13 Aug. We don't have Ray-Bans, so:

**Feed it a video file and let the backend treat it as live.** Same code path,
same timing, same everything — it just reads frames from a recording instead of
a camera. This is better than a live camera for presenting: it's repeatable, it
can't fail on stage, and we can pick footage that produces good jokes.

**Built.** `python run.py --video clip.mp4`. Needs ffmpeg for the audio.

**The look: a small DJ icon, like Spotify's DJ.** Not a dashboard. A character
that reacts, with a good voice. The current screen is an engineering view — it's
useful for us and it's the wrong thing to show a judge.

**Built, at `/dj`.** The reasoning stayed — as a compact ticker beside the orb
rather than the full dashboard. Showing it is a real differentiator and half of
why the technical work reads as serious, so it was worth keeping in a smaller form.

**A hosted site — this is our presentation format, not a product.** The spec:

- Explains the whole thing with a clear diagram
- Has a testing area: drop in a video, and it shows which songs it picked and
  *where in the video* each one plays
- Ships with a hardcoded sample video so it always works

**Mostly built.** The launch page and the demo area both work, and the loop
diagram is drawn. Missing: the real name. Don't sink more time into polish until the
backend has been proven with real footage — a beautiful site replaying a bad run
helps nobody.

**Audio on the site:** it names the song and people can look it up themselves.
For our own demo videos the music is overlaid onto the video. That sidesteps the
problem entirely — no visitor login, no licensing mess, no live playback to fail.

---

## Decisions we've already made

Don't re-open these without a reason.

- **14 Aug** — **When to change the song is decided on the music target, not the
  scene.** Two rooms that invert to the same music keep the same song. The
  numbers (`hold_threshold` 0.30, `jump_threshold` 0.85, `min_change_seconds` 20)
  were measured against the corpus, and the reasoning is recorded next to them in
  `config.yaml` — don't retune them by feel without re-running that measurement.
- **14 Aug** — **A big change acts on one read; a moderate one waits for two.**
  Uniform confirmation forced a choice between thrashing and lagging. Making the
  confirmation requirement depend on how far the target moved buys both.
- **14 Aug** — **The voice is not part of the running product.** It says one
  line at startup ("Hello. I'm your [name]. I'll help you choose the perfect
  music for any moment.") and then stays quiet. Everything else people hear is
  pre-rendered for the website demo. Narrating every track cost a TTS call per
  decision and talked over the music, to say what the screens already show.
  `voice.say: every_track` in `config.yaml` turns it back on if we're wrong.
- **13 Aug** — Queue by default, interrupt only when the room changed a lot and
  the song has had a run. Not a setting; the system decides per moment.
- **13 Aug** — Feed it a video file for the demo rather than a live camera.
- **13 Aug** — Look and feel is a DJ character, not a dashboard.
- **13 Aug** — The site is our presentation format, not a working product. Build
  it late, once the backend is proven.
- **13 Aug** — The site names songs rather than playing them; demo videos have
  the music overlaid. No visitor login, no licensing problem.
- **13 Aug** — Two screens, not one. The DJ face at `/dj` for judges, the
  engineering view at `/` for us. The reasoning stays visible on both — it's the
  difference between an agent and a shuffle button.
- **13 Aug** — The site is Next.js, in its own `frontend/` folder, and static.
  It replays a recorded run rather than calling the agent, so there's no backend
  to host and nothing live to fail.
- **Earlier** — One question to understand the scene, not one per detail.
- **Earlier** — Our own song list and scoring; Spotify is only the speaker.
  (Their music-analysis endpoints were shut off to new apps in 2024.)
- **Earlier** — Hand-picked famous songs over a huge database. The joke needs
  people to recognise the song.
- **Earlier** — No training our own model. No time, no need.
- **13 Aug** — Tagline: “The worst music for the best moments. And vice versa.”
- **~~13 Aug~~ — Reopened 14 Aug.** There was a decision here about how the site
  should look. The visual layer is being restarted, so it no longer holds and
  has been removed rather than left to be read as current. The section ordering
  in `frontend/app/page.tsx` is the part that survives.
- **13 Aug** — Name is a placeholder in `frontend/lib/brand.ts` until we pick
  one. It should play off “DJ”. Note: Spotify's terms forbid “Spotify” in a
  product name, so the current working title can't ship publicly.
- **13 Aug** — No inversion dial. Always fully invert; measure and report the
  mismatch instead. `Verdict.mismatch` is an outcome, never an input.
- **13 Aug** — One decision path. Anything holding a scene already enters the
  same compiled graph via `decide_from_scene`; there is no second pipeline.
- **Earlier** — Glasses aren't needed to win.

---

## Next three things

1. **Run the Spotify setup script.** It's the only part that can quietly fail on
   the day, and it has the fiddliest setup. Everything else can be improved up to
   the deadline; this one either works or it doesn't.
2. **Point the photo-reader at real photos.** Everything downstream is judged on
   whether this is any good, and right now it's guesswork.
3. **Film a real demo clip and run it.** Everything needed to do this now exists.
   Whatever comes out of `--record` is the raw material for the site.

---

## Still open

- It'll repeat the same joke if left running a long time. No memory yet.
- Nobody's timed the real thing end to end.
- Nicheness is agreed as an idea but isn't scored or used anywhere.
- The genre map has now been scraped to `data/genre_map.json`, but still
  nothing reads it.
- ~~Two video readers.~~ **Resolved.** `capture/video.py` is now a thin adapter
  over `src/videofeed/`, so there's one video reader and one set of triggers.
  Video input now samples on scene cuts and audio onsets as well as on a clock,
  and those samples skip the local gate because the sampler already knows the
  world changed. `capture/gate.py` still serves the live webcam path, where we
  don't have the whole file up front.
- A calm scene used to deadlock: the change-detector suppressed repeat reads, so
  the "see it twice before acting" rule was never satisfied and nothing played.
  Fixed — a quiet tick now counts as evidence the scene is stable. Worth knowing
  in case something similar shows up elsewhere.
