# Status

**Update this file when you finish something.** One line is enough. It's the
only place that says what's actually true right now.

Three states, and the middle one matters most:

| | Means |
|---|---|
| **Done** | Built, and someone has watched it work for real |
| **Built, unproven** | The code exists and runs on fake input. Nobody has pointed it at the real thing yet. **Assume it's broken until someone checks.** |
| **Not started** | — |

Last updated: 13 Aug 2026 (evening)

---

## Where we are

| Part | State | Who |
|---|---|---|
| The loop holding it all together | Done | |
| Deciding when to change the song | Done | |
| Backup list when things break | Done | |
| Finding songs on Spotify | Built, unproven | |
| Playing songs on Spotify | Built, unproven | |
| Reading a photo into a description | Built, unproven | |
| Working out the opposite | Built, unproven | |
| The song list (47 songs) | Built, unproven | |
| Picking the funniest one | Built, unproven | |
| The voice | Built, unproven | |
| Video file as input | Built, unproven | |
| Recording a run for the site | Built, unproven | |
| Screens — DJ face and engineering view | Built, unproven | |
| Site — scaffold + demo ground | Built, unproven | |
| Site — diagram + landing page | Not started | |
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
- **Tests.** 30 of them, each guarding a specific way the demo could break.

## Built, but nobody has run it for real

Ordered by how badly it hurts if it turns out broken.

**1. Spotify — playing songs**
There's a one-command setup (`python scripts/spotify_setup.py`) that logs in,
checks the account is Premium, finds a speaker, looks up all 47 songs in advance,
tells you which ones it couldn't find, and plays a test track.
*To prove it:* run that script and hear a song come out of a speaker.
*Known risk:* Spotify search returns karaoke versions, tribute bands, and wrong
artists with the same song title. There's a filter for that, but it's only been
tested against made-up search results. **Read the unresolved list when you run it.**

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

**7. The site scaffold**
`frontend/` — Next.js, TypeScript, Tailwind. Builds clean. The demo ground works:
it reads a recorded run, plays the video, and pops up each decision at the point
in the footage where the song lands. The landing page and the diagram are
skeletons with notes left in them.
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

**Half built.** `frontend/` exists and the demo area works — it replays a
recorded run against the video. The diagram and the landing page are still
skeletons. Don't sink time into polish until the backend has been proven with
real footage; a beautiful site replaying a bad run helps nobody.

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
- The genre map is scrapeable but nothing uses it.
- A calm scene used to deadlock: the change-detector suppressed repeat reads, so
  the "see it twice before acting" rule was never satisfied and nothing played.
  Fixed — a quiet tick now counts as evidence the scene is stable. Worth knowing
  in case something similar shows up elsewhere.
