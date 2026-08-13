# Status

**Update this file when you finish something.** One line is enough. It's the
only place that says what's actually true right now.

Three states, and the middle one matters most:

| | Means |
|---|---|
| **Done** | Built, and someone has watched it work for real |
| **Built, unproven** | The code exists and runs on fake input. Nobody has pointed it at the real thing yet. **Assume it's broken until someone checks.** |
| **Not started** | — |

Last updated: 13 Aug 2026

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
| The screen | Built, unproven | |
| Video file as input | Not started | |
| DJ icon look | Not started | |
| Hosted site (presentation format) | Deferred on purpose | |
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
- **Tests.** 25 of them, each guarding a specific way the demo could break.

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
Built and working locally — thinking-cards, a cruelty dial, and a box where you
type a situation and watch it run. Not styled the way we now want it (see below).

---

## The demo plan

Decided 13 Aug. We don't have Ray-Bans, so:

**Feed it a video file and let the backend treat it as live.** Same code path,
same timing, same everything — it just reads frames from a recording instead of
a camera. This is better than a live camera for presenting: it's repeatable, it
can't fail on stage, and we can pick footage that produces good jokes.

**Not started.** The input layer was built to be swappable, so this is adding one
small piece rather than changing anything else.

**The look: a small DJ icon, like Spotify's DJ.** Not a dashboard. A character
that reacts, with a good voice. The current screen is an engineering view — it's
useful for us and it's the wrong thing to show a judge.

**Not started.** Worth deciding early whether the thinking-cards stay visible
alongside the DJ icon. Showing the reasoning is a real differentiator and it's
half of why the technical execution reads as impressive — losing it entirely
would cost us.

**A hosted site — this is our presentation format, not a product.**

**Deferred. Don't build it yet.** Spec so far, so we don't lose it:

- Explains the whole thing with a clear diagram
- Has a testing area: drop in a video, and it shows which songs it picked and
  *where in the video* each one plays
- Ships with a hardcoded sample video so it always works

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
3. **Video-file input.** Unblocks rehearsing the actual presentation.

---

## Still open

- It'll repeat the same joke if left running a long time. No memory yet.
- Nobody's timed the real thing end to end.
- Nicheness is agreed as an idea but isn't scored or used anywhere.
- The genre map is scrapeable but nothing uses it.
