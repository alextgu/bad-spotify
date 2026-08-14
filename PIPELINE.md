# How it works

Plain language, no code. **This file explains how the thing works.** For what's
built versus not built, see `STATUS.md` — keeping those separate is the only way
they stay accurate.

Anything marked **TEMPORARY** isn't settled. Don't build on it without saying so.

---

## The loop

Six steps, over and over, about every five seconds.

**1. Look.** Take a picture and listen to the last few seconds of sound.

**2. Has anything changed?** Compare against the last look. If the room is
different — someone walked in, it got loud, the lights changed — carry on to the
expensive thinking. If it's the same, skip it and reuse what we already worked
out. Either way we still go to step 6, because "nothing changed" is useful
information too. It's the difference between *the scene is stable* and *we don't
know what the scene is*.

**3. Understand the moment.** Describe what's happening: where we are, what
people are doing, how it feels. One description covering everything, produced in
one go.

**4. Flip it.** Work out the opposite of that feeling. This is the whole point
of the project.

**5. Pick the song.** Three different ideas of "worst" each propose candidates.
Then one final choice picks the funniest of them, and writes a one-line remark
to say out loud.

**6. Queue it, or cut in.** Usually it lines the song up to play next. But if the
room changed a lot *and* the current song has already had a fair run, it cuts in
immediately — wrong music is much funnier while the moment is still happening.

---

## What it notices about a moment

Everything in this table comes back in **one answer**, not one question per row.
Asking separately would cost more, take longer, and give more chances to fail.

| | What it means |
|---|---|
| Mood | Happy, tense, sad, calm |
| Speed | Fast or slow — pace, drums, how much is going on |
| Steady or not | A regular beat versus something loose, like jazz |
| Instruments and sounds | What a genre is made of |
| Colour | What colours are in the scene, and what they'd sound like |
| Nicheness | Mainstream versus deep cut. **TEMPORARY** — agreed as an idea, not used yet |
| Weather | **TEMPORARY** — would be looked up, not seen |

It also says how sure it is. If it isn't sure, nothing happens — see the
guardrails below.

---

## There is no "how wrong should it be" setting

It always fully flips the mood. There used to be a dial for this and it was
removed, because it described something the system doesn't do: this reads a
mood and inverts a mood, and there's no meaningful halfway.

What we *do* have is a **measurement**. After it picks a song, we work out how
far apart the moment and the music actually turned out to be — a number from 0
to 1 called the mismatch — and show that. It's a result, not a request.

## How it decides what's "worst"

Two things, and it needs both.

**The maths.** Every moment and every song is scored on the same handful of
qualities. "Opposite" is just flipping every score. Fast, free, and easy to show
someone on a slide.

**The taste.** The maths on its own gives boring answers — usually some obscure
noise record nobody has heard of. A genuinely funny choice has to be *specific*
and it has to be *recognised*. Funeral music at a birthday party. A Christmas
song in August. A silly chase tune during a tense moment. Only something that
understands culture spots that.

**So the maths makes a shortlist and taste picks the winner.** Never one alone.

**On nicheness:** the joke dies if nobody knows the song. Obscure is only funny
when the mismatch is obvious *without* knowing the track. Mainstream is the
default; reach for deep cuts on purpose, not by accident.

---

## How it's stopped from going haywire

- **Lining up the next song is cheap. Cutting one off has to be earned.**
  Queueing is nearly always allowed. Interrupting needs two things at once: the
  room genuinely changed, and the current song has already played long enough.
- A song is safe from being cut for its first stretch, whatever happens.
- It has to see the same change twice before acting. One odd reading isn't enough.
- If it isn't sure what it's looking at, it does nothing.
- If any part breaks, a backup list of always-wrong songs plays anyway.

**The rule: it is never silent.** Silence is the only actual bug. Playing the
wrong thing is the product working correctly.

---

## Where the music comes from

- **A hand-picked list of songs, scored by hand.** Small on purpose: famous songs
  beat a huge pile of unknown ones, because recognition is what makes it land.
- **We don't analyse audio to work out what songs are.** We label them once,
  ourselves. Spotify's own music-analysis tools were shut off to new apps in
  2024, and we don't need them.
- **Spotify is only the speaker.** It finds the track and plays it. All the
  judgement is ours.
- There's a public map of music genres arranged by similarity — useful for
  finding opposites. **TEMPORARY**: we can pull it in, but nothing uses it yet.
- Bigger free music datasets exist if the hand-picked list runs out.
  **TEMPORARY**: only if we need them.

---

## What people see

Three surfaces, for three different audiences.

**The DJ face** — what judges watch while it runs. A character that reacts: it
takes on the colours of the room, says its line, and shows what's playing and
whether it queued the song or cut in. Beside it, a running list of its reasoning.

**The engineering view** — what we use while building. The same information in
much more detail, plus a box where you type a situation ("a hospital waiting
room at 3am") and watch the whole thing run without a camera.

**The site** — our presentation format. It explains the project, and has a demo
area where you watch a video and see which song it chose at each point in the
footage. It replays a recording rather than running live, so there's nothing to
host and nothing that can fail on stage.

**We keep the reasoning visible on all of them.** Seeing *why* it chose funeral
doom is the difference between an agent and a shuffle button.

---

## For the demo: video instead of glasses

We don't have Ray-Bans, so we film something and feed the recording in as though
it were happening live. Nothing downstream knows the difference — same steps,
same timing, same decisions.

It's also better than a live camera for presenting: the same video gives the
same run at every rehearsal, and there's no camera, lighting, or permission to
fail on stage.

A run can be recorded to a file listing every song, **where in the video it
starts**, and why. That file is what the site replays.

---

## What we're using

| | For |
|---|---|
| Gemini | Understanding the scene, and picking the funniest song |
| LangGraph | Holding the steps together and keeping the order sane |
| ElevenLabs | The voice that announces what it's done |
| Spotify | Finding and playing the music. Needs Premium |
| Next.js | The presentation site |
| Twelve Labs | **TEMPORARY** — too slow for the live loop. Best use is a recap at the end: "here's every moment we ruined." Cut it if we don't build that screen |
| Training our own model | **Cut.** No time, and no need — good instructions plus a well-chosen song list does the job |

---

## Where to go next

| I want to know… | Read |
|---|---|
| What's actually finished, and what to work on | `STATUS.md` |
| How to run it, and who owns which part | `README.md` |
| How to add my part without breaking things | `INTEGRATION.md` |
| How the site connects to the agent | `frontend/README.md` |
