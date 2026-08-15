/**
 * The name, and the lines that place the product.
 *
 * `positioning` is the one sentence that says what this is by pointing at the
 * thing everyone already has. It sits in the hero, above the headline, because
 * "a DJ that goes on vibes instead of history" explains the product faster
 * than any amount of describing it from scratch does.
 *
 * On naming Spotify in our own copy: this is comparison, not affiliation.
 * Keep it that way — the moment the page implies endorsement or uses their
 * mark, it stops being comparison. No Spotify logo, no green lifted from
 * their brand sheet, no "official" anything.
 *
 * Everything else the page says lives in `lib/site.ts`.
 */
export const brand = {
  name: "Slopify",

  /**
   * Sits above the hero headline, set small in mono beside a pulsing dot.
   *
   * Deliberately says what it *doesn't* do first. "No history, no requests"
   * tells you the whole shape of the thing before the headline arrives, and
   * refusing to explain the rest is most of why the top of the page reads as
   * mysterious rather than as a feature list.
   */
  positioning: "No history · No requests · Only vibes",

  tagline: "Music for the room you're in.",

  description:
    "A DJ that picks from the room you're standing in, rather than from what you played last week.",
} as const;

/**
 * The six steps of the loop, as drawn by `components/PipelineDiagram.tsx`.
 *
 * **Nothing on the current landing page renders either of them.** The page was
 * rebuilt around the mockup, which has no diagram section; the component
 * survived that rebuild because it was updated to the six-strategy fan-out at
 * the same time and is a working, accurate drawing of the real pipeline.
 *
 * So this is a component waiting for a home rather than dead code — but if the
 * page never grows a place for it, delete the component and this export
 * together rather than leaving it to rot.
 */
export const steps = [
  { n: "01", title: "Look", body: "A picture, and the last few seconds of sound." },
  {
    n: "02",
    title: "Notice",
    body: "Has anything changed? If not, don't waste the thinking.",
  },
  {
    n: "03",
    title: "Understand",
    body: "Where we are, what people are doing, how it feels.",
  },
  { n: "04", title: "Invert", body: "Work out the exact opposite of that feeling." },
  {
    n: "05",
    title: "Choose",
    body: "Competing ideas of “worst”. The funniest wins.",
  },
  {
    n: "06",
    title: "Commit",
    body: "Queue it — or cut the music off, if the moment deserves it.",
  },
] as const;
