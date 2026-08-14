# Status

**Update this file when you finish something.** One line is enough. It's the
only place that says what's actually true right now.

Three states, and the middle one matters most:

| | Means |
|---|---|
| **Done** | Built, and someone has watched it work for real |
| **Built, unproven** | The code exists and runs on fake input. Nobody has pointed it at the real thing yet. **Assume it's broken until someone checks.** |
| **Not started** | — |

Last updated: 13 Aug 2026 (late evening — verification pass)

---

## Where we are

| Part | State | How it was proven |
|---|---|---|
| The loop holding it all together | Done | `python run.py --ticks 6 --no-hud` end to end; also watched live on both screens |
| Deciding when to change the song | Done | hysteresis, cooldown and commitment all observed holding in a live run |
| Backup list when things break | Done | forced `verdict=None` on both the normal and the forced path — chaos deck fired both times |
| The song list (47 songs) | Done | `build_seed_corpus.py` writes 47; corpus loads in every run |
| Working out the opposite | Done *on mock scene reads* | park → Drowning Pool, library → Sandstorm, hospital-at-3am → Barbie Girl. Never run on a real photo |
| Screens — DJ face and engineering view | Done | watched both at 127.0.0.1:8420: orb takes the scene colours, ticker fills, scene injection runs the whole pipeline |
| Test suite | Done | 65 passed (needs `pip install pytest` — it was missing from requirements, now added) |
| Video sampling — `src/videofeed/` | Done, model side deliberately stubbed | new standalone package: cadence + trigger sampling with audio. Verified on a real clip — the cut at 5.0s fired `scene_cut+motion_spike+brightness_shift`, the tone fired `audio_onset`, and `--out` wrote frames, WAVs and a manifest. 17 tests, all against a real mp4 |
| Clean install | Done | fresh venv, `pip install -r requirements.txt`, corpus, bounded run — no errors |
| Site — launch page | Done, rebuilt | restructured into six sections (see below); renders clean, `tsc --noEmit` clean |
| Site — pipeline diagram | Done | inline SVG, six steps + the change-gate bypass + the two model calls marked |
| Site — demo ground | Done, on placeholder assets | `/demo` and the new "Try it yourself" section both replay the sample session |
| Naming | Working title: **bad spotify** | decided 13 Aug to keep the repo name for now. Still cannot ship publicly — Spotify's terms forbid it |
| Finding songs on Spotify | Built, unproven | no Premium account available on 13 Aug |
| Playing songs on Spotify | Built, unproven | as above |
| Reading a photo into a description | Built, unproven | no `GOOGLE_API_KEY` available on 13 Aug |
| Picking the funniest one | Built, unproven | judge has only ever run on mock scene reads |
| The voice | Built, unproven | no `ELEVENLABS_API_KEY` available on 13 Aug |
| Video file as input | Built, unproven | no real footage filmed yet |
| Recording a run for the site | Built, unproven | only ever recorded from the synthetic clip |
| Nicheness | Not started | agreed as an input, still not scored or used |
| Session memory | Not started | it will repeat a joke on a long run |
| Camera preview + end-of-session recap | Not started | |
| Glasses | Not started — and not needed | |

The mock path is now **proven end to end**. What is still unproven is every
point where the system touches a real account: Gemini, Spotify, ElevenLabs, and
real footage. That remains the single biggest risk to the demo, and it is
blocked on credentials rather than on code.

---

## Fixed during the verification pass (13 Aug)

- **Audio features were silently dead.** `librosa.beat.tempo` was removed in
  librosa 1.0, and the exception aborted the rest of the block — so tempo,
  spectral centroid, flatness and pulse regularity were *all* zero on every
  tick, and the console printed `feature extraction degraded` each time.
  Now tries `feature.tempo` → `feature.rhythm.tempo` → `beat.tempo`, and a
  missing BPM no longer costs the other features. Verified against a 120 BPM
  click track: reads 117 BPM, and the other four fields populate.
- **Scene injection printed a raw epoch on screen.** It bypassed the DJ's
  bounds by zeroing `started_at`, so the reasoning ticker announced
  `scene shifted 1.24 after 1786674879s, cutting in` — in front of judges, on
  the screen whose whole job is making the reasoning legible. The bypass is now
  an explicit `force` flag through the graph; it still cuts in immediately and
  it now says `forced (scene injection); bounds bypassed, cutting in`.
- **`pytest` was missing from `requirements.txt`** even though the README tells
  you to run it. Added.

---

## Done

- **The loop.** Look → check if anything changed → understand → flip it → pick a
  song → queue or cut in. Runs end to end today with fake versions of every piece.
- **When to change the song.** Won't thrash. Needs to see a change twice before
  reacting. Ignores itself when unsure. Queues by default, only cuts the music
  off when the room really changed *and* the current song has had a fair run.
- **Backup list.** If anything upstream dies, a pre-picked list of always-wrong
  songs plays anyway. It is never silent.
- **Tests.** 48 of them, each guarding a specific way the demo could break.
- **Timeouts on the model calls.** A slow answer is abandoned and retried
  rather than freezing the loop. A late answer is worth less than a fast fallback.

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

**5. The screen — now proven, moved to Done**
Both watched working on 13 Aug. `/dj` takes the scene's colours, the quip lands
in big type, now-playing shows the queued/cut-in badge, and the reasoning ticker
fills. `/` runs the whole pipeline off the scene-injection box — typed
"a hospital waiting room at 3am" and it went scene → antivibe → three strategies
→ verdict (Barbie Girl, Aqua) → voice → play, cut in, all on screen.
*Still to do:* watch it drive off a real video on a projector.

**6. Video as input**
Feeds a recording in as though it were live — samples a frame every few seconds,
pulls the matching audio out with ffmpeg, and reports where in the video it is.
Tested against a generated clip, never against real footage.
*To prove it:* run it on an actual video someone filmed.
*Needs:* ffmpeg installed, otherwise it runs vision-only.

**7. The site — restructured 13 Aug, runs clean**
`frontend/` — Next.js, TypeScript, Tailwind. `npm install` + `npm run dev` clean,
`tsc --noEmit` clean. Rebuilt into six sections, in this order:

1. the launch — name, tagline, creed
2. the product — a rotating pair of camera glasses (CSS 3D, no dependency),
   what it does, the pipeline diagram, and the stack with a reason beside each part
3. the film — one uninterrupted watch-it-happen
4. try it yourself — preset clips, upload your own, a slider that steps through
   each decision, and a button that grabs the frame the agent was judging
5. the depth — the five decisions worth defending
6. what's next — roadmap, and the honest close about not having the glasses

**The UI is scaffolding on purpose.** Structure and behaviour first; the visual
pass is still to come.

*Known gap:* "upload your own" cannot run the agent — the site is static and
Gemini can't run in a browser tab. It takes your clip, hands you the exact
`run.py --video ... --record ...` command, and accepts the session file that
comes out. Faking a decision in the browser would make every real decision on
the page worthless.

*Unverified:* the frame-grab button. Chrome on this machine stopped decoding
`sample.mp4` partway through the session — `readyState` stuck at 0 on a file
that `ffprobe` confirms is H.264/AAC and that the same page decoded fine an hour
earlier, including on a page whose code hadn't changed. Looks like a browser
quirk rather than our code, but **nobody has watched a frame actually appear**.
Check it on another machine.

*To prove the rest:* drop in real footage and a real recording, and walk someone
through it.

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

**Mostly built.** The launch page and the demo area both work. Missing: the
pipeline diagram, and the real name. Don't sink more time into polish until the
backend has been proven with real footage — a beautiful site replaying a bad run
helps nobody.

**Audio on the site:** it names the song and people can look it up themselves.
For our own demo videos the music is overlaid onto the video. That sidesteps the
problem entirely — no visitor login, no licensing mess, no live playback to fail.

---

## Decisions we've already made

Don't re-open these without a reason.

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
- **13 Aug** — The site looks like a minimal product launch, played straight.
  The gap between the polish and what's being announced is the joke.
- **13 Aug** — Name is a placeholder in `frontend/lib/brand.ts` until we pick
  one. It should play off “DJ”. Note: Spotify's terms forbid “Spotify” in a
  product name, so the current working title can't ship publicly.
- **Earlier** — Glasses aren't needed to win.

---

## Next three things

Unchanged, and now all three are blocked on things code can't supply. As of the
13 Aug verification pass there was no `GOOGLE_API_KEY`, no Spotify Premium
account, no `ELEVENLABS_API_KEY` and no real footage on the machine, so every
one of these is still open.

1. **Run the Spotify setup script.** Needs Premium, an app at
   developer.spotify.com with redirect URI `http://127.0.0.1:8888/callback`, and
   the Spotify app awake. It's the only part that can quietly fail on the day.
   Read the unresolved list when it runs.
2. **Point the photo-reader at real photos.** Everything downstream is judged on
   whether this is any good, and right now it's guesswork. While you're there:
   time the call and put the real number here — `perceive.timeout_s` is 4.0 and
   nobody has checked whether that's generous or tight — and check that
   `confidence` actually drops on an ambiguous image.
3. **Film a real demo clip and run it.** `python run.py --video clip.mp4 --record demo1`,
   then check `played.at_video_time` against the footage. Whatever comes out is
   the raw material for the site, and it replaces two placeholders:
   `frontend/public/videos/sample.mp4` (88KB of green) and
   `frontend/public/sessions/sample.json` (recorded from that green clip, so the
   decisions in it mean nothing).

---

## Still open

- It'll repeat the same joke if left running a long time. No memory yet.
- Nobody's timed the real thing end to end. (The mock loop is instant, which
  tells us nothing — the number that matters is the Gemini round trip.)
- Nicheness is agreed as an idea but isn't scored or used anywhere.
- **The genre map now works, and that's the problem.**
  `scripts/scrape_everynoise.py` ran clean on 13 Aug: 6291 genres with 2D
  coordinates, pulled off the live page, written to `data/genre_map.json`. So it
  is no longer unverified. But look at what it returns — the opposite of *death
  metal* comes back as `funk bh, cartoon, bachchon ke geet, kikuyu pop`. That's
  the exact failure PIPELINE.md warns about: geometrically perfect, and nobody
  in the room has heard of any of it. **Keep the script** (it's a free offline
  genre embedding and it costs nothing to sit there), but nothing should consume
  it until there's a recognisability filter in front of it. Wiring it in as-is
  would make the picks worse, not better.

## videofeed — what's built and what isn't

`src/videofeed/` (added 14 Aug) takes a video and produces model-ready segments:
a frame, the audio window ending at that moment, and *why* it was sampled. It
samples on a fixed cadence and on triggers, so a slow cadence no longer means
missing the moment someone walks in. It imports nothing from `badspotify` — the
folder can be copied into another project as-is.

**Built and proven:** sequential decode (no seeking), cheap 32×32 probes several
times a second, five built-in triggers, a `FunctionTrigger` escape hatch,
per-trigger rate limiting, ffmpeg audio extraction that degrades to vision-only,
a CLI, and a `DirectorySink` that writes a replayable run to disk.

**Deliberately not built:** the model. `handoff.py` defines the seam —
`handle(segment) -> dict | None` — and ships `NullHandoff` so the sampler can be
checked before anyone spends a token. Whoever writes the model implements that
one method; nothing in the feed changes.

**Not wired into the agent.** `badspotify` still uses its own
`capture/video.py`, which samples on a fixed interval only. The adapter is six
lines and is written out in `src/videofeed/README.md`, but nobody has run the
agent off it yet — that's the next step if we want the DJ reacting to cuts and
bangs rather than to a 5-second tick.

## Two things checked and kept

- **`src/badspotify/capture/replay.py` — keep.** It looks redundant next to
  `video.py`, and it isn't. It's the default source in `config.yaml`, it needs no
  video file, and it synthesises frames when `data/replay/` is empty — which is
  what makes `git clone && pip install && python run.py` work with nothing else
  on the machine. It's also the only source that gives byte-identical runs, so
  it's what the tests and any "did I break the loop?" check run against. `video.py`
  is the demo path; `replay.py` is the zero-setup path. Different jobs.
- **`run.py --turbo` — keep.** Two lines, dev-only, collapses the DJ bounds so a
  bounded verification run doesn't spend its life in cooldown. The help text
  already says never to use it live. Deleting it would just mean editing
  `config.yaml` by hand every time.
- A calm scene used to deadlock: the change-detector suppressed repeat reads, so
  the "see it twice before acting" rule was never satisfied and nothing played.
  Fixed — a quiet tick now counts as evidence the scene is stable. Worth knowing
  in case something similar shows up elsewhere.
