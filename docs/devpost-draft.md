# Slopify: Devpost draft

Copy each block into the matching field on Devpost. Section headings match
Devpost's own. Nothing here is invented: every number came out of a terminal,
and the notes at the bottom say which command produced it.

---

## Elevator pitch (200 characters)

Camera glasses that look at the room, work out what music belongs there, and
play the exact opposite. On Spotify. Out loud.

---

## Inspiration

Spotify's DJ knows what you listened to last Tuesday. It does not know that
you are at a funeral.

That gap bothered us more than it should have. Every recommender we have ever
used is trying to be right, and the whole industry has spent fifteen years
getting slightly better at the same trick. Nobody has built the other one. So
we made the DJ that reads the room correctly and then does the worst possible
thing with that information, on purpose, with total confidence.

The rule we set on day one was that "worst" had to mean something specific.
Not random, not offensive, not shuffle with a filter. Musically and culturally
opposite, and able to explain itself. If it cannot tell you why funeral doom
belongs at a picnic, it is a shuffle button wearing a costume.

## What it does

Slopify looks at whatever you are looking at, understands the moment, and
queues the most wrong song for it.

A funeral service gets Yakety Sax. A dentist waiting room gets Slayer. The
supermarket aisle gets the Macarena. A yoga class gets "Welcome to the Jungle".
A lecture hall, mid-lecture, gets Tubthumping. A silent library during exam
week gets Sandstorm. A monastery at dawn gets "Enter Sandman". A wedding first
dance gets "50 Ways to Leave Your Lover", which is a song about leaving,
played at the exact moment two people promise not to.

Those are real outputs. We did not write them for the pitch.

Most of what it does is like that: ordinary places, treated with total
seriousness, ruined precisely. The joke is usually the room, not the reference.

The part we care about most is that it picks *how* to be wrong, because loud
where it should be quiet is the boring version and it is all a mood vector can
give you. So the model chooses an axis first:

- **counter_register**: a solemn place gets a song with no dignity at all. This is the one that fires most.
- **counter_lyrics**: the sound can even fit. The words must not. Break-up songs at weddings live here.
- **counter_genre**: a string quartet in a candlelit chamber gets Cannibal Corpse.
- **counter_era**: a torchlit medieval hall gets 100 gecs.
- **counter_energy**: the blunt one, used when nothing sharper fits.
- **counter_rivalry**: and occasionally it gets specific. Point it at a Lakers
  game and it queues Boston anthems, because it knows what a Lakers game is.
  That one is rarer and it is the one people remember.

It runs on your phone, uses the glasses as eyes and ears, and plays through
Spotify. It also runs on a laptop with a webcam, a shared screen, or a video
file, because we wanted to be able to test it without wearing anything.

Two rules it will not break. It never goes silent: every model, player and
voice degrades to a stand-in, and under all of them sits a hand-picked
fallback deck. And it says nothing about anyone's race, religion, sex or
politics. It reads places, occasions and institutions. A stadium has a rival.
A kind of person does not.

## How we built it

A frame goes in. A song comes out. In between:

1. A cheap local change detector decides whether anything actually moved. Most
   frames do not earn a model call.
2. Gemini reads the frame into a structured scene: setting, activity, occasion,
   mood, five vibe axes, dominant colours, and a confidence score.
3. That mood gets inverted, which is arithmetic and instant.
4. Five strategies argue in parallel about what to play. Four score the
   hand-curated corpus different ways. The fifth ignores it entirely and asks
   the model to name famous songs along whichever axis of opposition bites
   hardest.
5. A judge picks the winner and writes the line explaining it.
6. The DJ decides whether to act at all, then queues or cuts in.
7. Spotify resolves the winning name to a real track and plays it.

Python, LangGraph, FastAPI, Gemini, Spotify Web API, Next.js for the site.
215 tests, because the demo is the product and every one of them guards a
specific way it could break on stage.

The design decision we would defend hardest is that **the reasoning is the
product**. Watching it read a room correctly and then queue the worst possible
answer is the whole thing in one screen. So every surface shows the scene it
read, the axis it chose, the song, and the sentence explaining the clash. A
shuffle button cannot show its working.

## Challenges we ran into

**Every single Gemini call was silently failing.** The timeout was set to 4
seconds. We measured the model at 5 to 8. So every call timed out, fell back
to a canned response, and produced perfectly plausible output that had nothing
to do with the camera. It looked like it was working. We only caught it by
timing the calls instead of trusting them. Benchmarking four models got us to
1.17 seconds median, which is a 5.6x cut, and the descriptions got *more*
specific rather than less.

**It changed the song six times in 62 seconds while staring at a wall.** The
scene never moved. Every decision logged `scene shifted 0.00` and it kept
committing new tracks anyway. The cause was not the picker. Already-played
tracks are excluded from the shortlist, so the judge was forced to return
something new every pass, and the guard that was supposed to catch "you picked
what is already playing" could never fire. It was re-deciding because it
could, not because anything had changed. Six tracks became one after we made
it ask about the target instead of the scene.

**One Christmas song won the monastery, the dentist and the football stadium.**
Any scene that matched none of the nine hand-written rules fell through to a
single fallback tag, which exactly two tracks in the corpus carry. So for
eleven months of the year, one song was winning by elimination. From outside
it looked exactly like a hardcoded lookup table, which is what we got accused
of, fairly.

**Spotify locked us out for 23 hours.** We were resolving all eight suggested
songs to real tracks before the judge picked one, so seven lookups per scene
went in the bin. Fourteen searches for one moment. The app hit its rate limit
and told us to come back in 82,058 seconds, with no appeal. We restructured so
only the *winning* track is ever resolved, which took it from fourteen searches
to one, and added a stand-down that stops asking the moment Spotify says stop.

**The Premium check could never pass, for anyone.** It compared the account's
subscription level against "premium", but the scope that populates that field
was never requested, so it was always empty and every account was rejected.
Premium ones included. Nobody had run it, so nobody knew.

**Spotify has closed most of its music API to new apps.** Recommendations
return 404. Related artists, audio features and browse return 403. The
popularity field is not in the response at all. Our original plan was to
search by genre and rank by fame, and both halves of that turned out to be
impossible. There is no recommendation engine available to us, which forced
the architecture we ended up preferring: the model does the thinking, and
Spotify is a resolver and a speaker.

## Accomplishments that we're proud of

**It knows when it does not know.** Pointed at a covered lens it reported
"obstructed or blocked camera view" at 0.10 confidence and did nothing at all.
That is the behaviour we are proudest of, because a comedy machine that is
confidently wrong about an empty room is just noise.

**The timing is measured, not tuned by feel.** The model disagrees with itself
by at most 0.173 on an unchanged frame. The smallest genuine scene change moves
the target 0.563. Every threshold sits in the gap between those two numbers,
and the reasoning is written next to the values so nobody retunes them by
vibes later. A stable scene holds on one track. A hard cut is answered in one
read.

**Five strategies that genuinely disagree.** We have a test that fails if a new
strategy keeps proposing what an existing one already found. Three arguing
beats five agreeing, and the losing candidates are shown on screen with their
scores because the argument is more interesting than the verdict.

**It survives its own dependencies.** No API key, no problem: every backend has
a working stand-in, so a teammate can run the entire pipeline on a laptop with
nothing configured. Rate limited, still fine: the hand-curated corpus carries
it.

## What we learned

**Ship it into a terminal before you believe any of it.** Four of our worst
bugs were invisible from the code and obvious the first time we watched real
output. The timeout, the Premium check, the Christmas song and the rate limit
were all sitting in a repo that passed its tests.

**A field you never requested reads exactly like a field that says no.** The
Premium bug is the general lesson. If you gate on something an API returns,
check that you asked for the scope that fills it, and treat missing as unknown
rather than as no.

**Fame beats accuracy, and we could not measure fame.** A technically perfect
opposite that nobody recognises is a worse joke than a famous song that is
merely very wrong. We assumed we would rank by popularity and Spotify does not
expose it any more, so we ask the model for famous songs instead. Asking turned
out to work better than measuring would have.

**The clipping was the design working.** Our site pins every section to exactly
one screen and clips whatever overflows, deliberately, so an oversized section
is a bug you can see. On a laptop, two sections lost their last line of text.
The fix was not those sections. The type scaled with viewport width while the
sections had to fit viewport height, so a wide short screen grew the words
without growing the room.

**Write down why, next to the number.** Every threshold in this repo has the
measurement that produced it in a comment beside it. It is the only reason we
could come back a day later and change them without guessing.

## What's next for Slopify

The native companion app. Nothing runs on Ray-Ban Meta itself: the Wearables
Device Access Toolkit gives a phone app the camera, mics and speakers, and
publishing is disabled while it is in preview. Our capture layer was built for
that shape from the start, and the browser companion already posts frames to
the exact endpoint the native app will use, so it is a port rather than a
rewrite. Audio out needs none of it, because the glasses are already a
Bluetooth speaker.

Memory across sessions, so it stops reaching for the same joke twice in an
evening. Track duration, so it knows when a song ends instead of inferring it.
And a real corpus: the hand-picked 47 are the safety net, and the live
catalogue is where the good jokes are.

The name is also a placeholder we have grown attached to.

## Built With

python, langgraph, fastapi, google-gemini, spotify-web-api, spotipy,
opencv, librosa, next.js, typescript, tailwind, gsap, uvicorn, gradio,
elevenlabs, meta-wearables-device-access-toolkit

---

## Notes for us, not for Devpost

Every number above is reproducible:

| Claim | Where it came from |
|---|---|
| 1.17s median, 5.6x cut | 4 models benchmarked, 3 calls each, same frame and prompt |
| 6 tracks in 62 seconds | `tests/test_dj_timing.py`, the regression that started the rework |
| 0.173 noise vs 0.563 real change | 6 reads of one unchanged frame vs pairwise across the demo scenes |
| 82,058 seconds | the actual rate limit response from Spotify |
| 14 searches to 1 | measured before and after, counting requests on one decision |
| 215 tests | `pytest tests -q` |
| confidence 0.10 refusal | live run against unreadable frames |

Still missing before submission:
- The demo video.
- Real footage. Every frame the model has read so far has been synthetic or a
  screen recording.
- Screenshots of `/live` mid-decision and the phone companion.
- A decision on whether "Slopify" is the final name.
