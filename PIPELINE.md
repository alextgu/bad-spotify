# How it works

Anything marked **TEMPORARY** isn't settled yet. Don't build on it without flagging it.

## The loop

Six steps, over and over, about every five seconds.

1. **Look.** Take a picture and listen for a few seconds.
2. **Is anything new?** If the room looks and sounds the same as last time, stop here and save the effort. Only carry on when something actually changed — someone walked in, it got loud, the lights changed.
3. **Understand the moment.** Describe what's happening in one go: where we are, what people are doing, how it feels.
4. **Flip it.** Work out the exact opposite of that feeling. This is the whole point of the project.
5. **Pick the song.** Come up with a handful of candidates for "worst possible right now," then choose the funniest one and write a one-line remark to say out loud.
6. **Queue it, or cut in.** Usually it just lines the song up next. But if the room has changed a lot *and* the current song has had a fair run, it cuts in immediately — because the wrong music is much funnier while the moment is still happening.

## What we notice about a moment

| | What it means |
|---|---|
| Mood | Happy, tense, sad, calm |
| Speed | Is it fast or slow — drums, pace, how much is happening |
| Steady or not | A regular beat versus something loose like jazz |
| Instruments and sounds | What a genre is made of |
| Colour | What colours are in the scene, and what they'd sound like |
| Nicheness | How obscure something is — mainstream versus deep cut. **TEMPORARY** |
| Weather | **TEMPORARY** — probably looked up, not seen |

All of this comes back in one answer, not one question per item. Asking separately costs more, takes longer, and gives more chances to fail.

## How we decide what's "worst"

Two things, and we need both.

**The maths.** Every moment and every song gets scored on the same handful of qualities. "Opposite" is just flipping every score. It's fast, it's free, and it's easy to show someone on a slide.

**The taste.** The maths alone gives boring answers — often some obscure noise record nobody's heard of. The genuinely funny choice needs to be *specific* and it needs to be *recognised*. Funeral music at a birthday party. A Christmas song in August. A silly chase tune during a tense moment. Only something that understands culture can spot that.

So the maths narrows it down to a shortlist, and taste picks the winner. Never one without the other.

**On nicheness:** the joke dies if nobody knows the song. Obscure is only funny when the *mismatch* is obvious without knowing the track. Treat mainstream as the default and reach for deep cuts deliberately.

## How we stop it going haywire

- **Lining up the next song is cheap; cutting one off has to be earned.** Queueing is nearly always allowed. Interrupting needs two things at once: the room genuinely changed, and the current song has already played long enough.
- A song is safe from being cut for its first stretch, no matter what happens in the room.
- It has to see the same change twice before reacting. One odd reading isn't enough.
- If it's unsure what it's looking at, it does nothing.
- If any part breaks, there's a backup list of always-wrong songs ready to go.

**The rule: it is never silent.** Silence is the only actual bug. Playing the wrong thing is the product working.

## Where the music comes from

- A hand-picked list of songs, each scored by hand. Small on purpose — famous songs beat a huge pile of unknown ones, because recognition is what makes it land.
- We're not analysing audio to work out what songs are. We label them once, ourselves.
- There's a public map of music genres laid out by how similar they are. Useful for finding opposites. **TEMPORARY** — we've got a way to pull it in, but nothing uses it yet.
- Bigger free music datasets exist if the hand-picked list runs out. **TEMPORARY** — only if we need them.

## What you see on screen

Cards in the top-right corner, Jarvis-style, showing what it's thinking as it thinks it: what it saw, what it decided was the opposite, what it considered, what it picked, and why.

Plus a dial for how cruel it's allowed to be, and a box where you can type a situation — "a hospital waiting room at 3am" — and watch the whole thing run without needing a camera. That's the button we press when demoing.

## What we're using

| | For |
|---|---|
| Gemini | Understanding the scene, and picking the funniest song |
| LangGraph | Holding the steps together and keeping the order sane |
| ElevenLabs | The voice that announces what it's done |
| Spotify | Actually playing the music |
| Twelve Labs | **TEMPORARY** — too slow for the live loop. Best use is a recap at the end: "here's every moment we ruined." Cut it if we don't build that screen |
| Training our own model | Cut. No time, and no need — good instructions plus a well-chosen song list does the job |

## Still open

- It'll repeat the same joke if left running a long time. No memory yet.
- Nobody's timed the real thing end to end.
- Glasses aren't wired up — building for normal video first, moving over later.

## What's left to build

Every part below already exists as a working stand-in, so the whole thing runs
end to end today with fake versions of each piece. Finishing a part means
swapping the stand-in for the real thing. They can be done in any order, by
different people, without waiting on each other.

**1. Seeing the moment**
*World in, description out.* Getting pictures and sound off a real camera, and turning them into an honest description of what's happening. Right now it returns canned answers and has never been pointed at a real camera.
*Finished when:* it runs off a real laptop or phone for ten minutes without falling over, and the descriptions it gives back actually match the room — including saying so when it isn't sure.

**2. Choosing the worst song**
*Description in, song out.* The opposite-finder, the song list, and the final pick. All three are working, but on fake input only, and the song list is about fifty tracks with no nicheness scores yet.
*Finished when:* it covers the situations we'll actually demo, doesn't repeat itself, and the picks make a room laugh more often than not — funny, not just technically opposite.

**3. Playing it out loud**
*Song in, sound out.* Spotify playback and the voice that announces it. Spotify is now built — there's a one-command setup that logs you in, checks the account, finds a speaker, looks up all our songs in advance, and plays a test track to prove it works. Nobody has run it yet. The voice is still untested.
*Finished when:* someone runs the setup script clean, and a song we choose actually starts playing with the voice line on top and the music dipping underneath.

**4. The screen**
Built and working — the thinking cards, the cruelty dial, and the type-a-situation box all run today.
*Finished when:* it also shows what the camera sees, and there's an end-of-session recap.

**Already done:** deciding *when* to change the song — the timing rules and the backup list. Tested. Leave it alone unless it misbehaves.

**Not needed to win:** glasses. A small companion app feeds pictures and sound in from them; nothing else has to change.

**Do #3 first.** It's the only one that can quietly fail on demo day and it has the fiddliest setup. Everything else can be improved right up to the deadline; that one either works or it doesn't.
