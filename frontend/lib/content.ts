/**
 * Page copy that isn't a name.
 *
 * `brand.ts` owns anything that changes when the product is renamed. This file
 * owns the argument: what it does, what it's built on, why any of it is hard,
 * and what happens next. Keeping it out of the components means the story can
 * be rewritten without touching layout.
 *
 * Keep every number here HONEST. A judge may ask, and "we made it up" is a bad
 * answer. Anything unproven is labelled as such -- see STATUS.md.
 */

/** Section 2 — what it actually does, in the order it does it. */
export const capabilities = [
  {
    title: "It watches the room",
    body: "A frame and a few seconds of sound, about every five seconds. Camera, or a recording fed in as though it were live.",
  },
  {
    title: "It decides what the moment feels like",
    body: "One model call returns the whole read: mood, pace, meter, instrumentation, colour, and how sure it is.",
  },
  {
    title: "It computes the opposite",
    body: "Every scene and every song sits in the same five-axis vibe space. The opposite is a reflection through the centre — deterministic, offline, instant.",
  },
  {
    title: "It picks the funniest wrong answer",
    body: "Three competing theories of wrongness each shortlist candidates. A second model call picks the winner and writes the line it says out loud.",
  },
  {
    title: "It commits, out loud",
    body: "Queue it, or cut the current track off if the room genuinely changed. Then it announces what it has done. It will not take requests.",
  },
] as const;

/** Section 2 — the stack, and what each piece is actually for. */
export const stack = [
  { name: "Gemini 2.5 Flash", role: "Reads the scene, and judges which wrong answer is funniest. Two calls per decision, never more." },
  { name: "LangGraph", role: "The agent graph: conditional edges, explicit state, and somewhere to hang retries and timeouts." },
  { name: "Spotify Web API", role: "The speaker, not the brain. Playback control and search only — their audio-analysis endpoints were closed to new apps in 2024." },
  { name: "ElevenLabs", role: "The narrator. Speaks over the track while the music ducks underneath." },
  { name: "librosa + OpenCV", role: "The local change gate and audio features. Roughly a millisecond, no network, no model call." },
  { name: "FastAPI + Next.js", role: "The agent's own two screens, and this site." },
] as const;

/** Section 5 — the parts that are actually hard, stated plainly. */
export const depth = [
  {
    heading: "A change gate, so thinking is rare",
    body: "Most ticks are boring. A local pixel-and-RMS diff decides whether the world moved enough to be worth a model call, and a quiet tick still counts as evidence the scene is stable. That one detail is why the loop is cheap enough to run continuously — and getting it wrong once deadlocked the whole system.",
  },
  {
    heading: "Geometry shortlists, culture chooses",
    body: "Reflection through the vibe cube is defensible and instant, but “most distant in vibe space” is usually a noise record nobody knows. Only a language model knows the true opposite of a sunlit park is funeral doom, or a Christmas song in August. Distance gives the defence, the model gives the punchline, and neither runs alone.",
  },
  {
    heading: "Three theories, not one score",
    body: "genre_antipode is wrong on every axis. tempo_clash is wrong about energy and pulse. lyrical_irony is wrong in meaning regardless of sound. They genuinely disagree, which is what makes the judge between them worth having rather than parallelism theatre.",
  },
  {
    heading: "Queueing is cheap, interrupting is earned",
    body: "Cutting the music off needs two things at once: the room really changed, and the current track has had a fair run. A system that interrupts constantly reads as broken; one that never interrupts misses the joke, because wrong music is funniest while the moment is still happening.",
  },
  {
    heading: "The only unacceptable failure is silence",
    body: "Every backend degrades instead of crashing: model down, Spotify down, no network, no keys. Underneath everything sits a pre-vetted deck of always-wrong songs that needs no model at all. Playing the wrong thing is the product working correctly.",
  },
] as const;

/** Section 6 — what we'd build next, honestly ordered. */
export const roadmap = [
  {
    title: "Onto the actual glasses",
    body: "Everything above the capture layer is already hardware-agnostic. The Ray-Ban port is a thin native app that owns the SDK session and posts frames to a localhost endpoint — the agent doesn't change at all.",
    state: "designed, blocked on hardware",
  },
  {
    title: "Memory, so it never repeats a joke",
    body: "Right now a long run will reach for the same track twice. Session memory turns the corpus into a set it draws down, and lets a running gag build across a night out.",
    state: "next",
  },
  {
    title: "Nicheness as a scored axis",
    body: "Obscure isn't automatically funnier — the joke dies if nobody recognises the song. Scoring recognisability lets it reach for a deep cut deliberately rather than by accident.",
    state: "next",
  },
  {
    title: "The end-of-session recap",
    body: "Index the whole session afterwards and close with every moment it ruined, timestamped. The one honest use for asynchronous video understanding in a five-second loop.",
    state: "sketched",
  },
] as const;

/** Section 6 — the close. */
export const theAsk = {
  heading: "We didn’t have the glasses.",
  body: "The Wearables Device Access Toolkit is real, it exposes video, photo, mic and audio out — and it is a Developer Preview native SDK, gated by country, with publishing disabled. So we built the entire agent hardware-agnostic and fed it a recording as though it were live. Same code path, same timing, same decisions. The only thing missing was the thing we couldn’t buy.",
  kicker: "Give us the glasses and this ships on Monday.",
} as const;
