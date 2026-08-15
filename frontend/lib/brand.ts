/**
 * The name, and the two lines that describe the product.
 *
 * `name` is a placeholder and is meant to look like one — it renders as
 * literally `[name]` in the wordmark, the tab title and the footer, so nobody
 * can mistake it for a decision that was made. Change it here and it changes
 * everywhere; don't hardcode it anywhere else.
 *
 * Everything else the page says lives in `lib/site.ts`.
 */
export const brand = {
  name: "[name]",

  tagline: "Music for the room you're in.",

  description:
    "It reads the room you're standing in, not the songs you played last Tuesday.",
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
