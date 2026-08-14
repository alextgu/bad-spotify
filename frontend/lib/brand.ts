/**
 * Everything nameable, in one place.
 *
 * The name is a PLACEHOLDER. When the team picks the real one, change `name`
 * here and it updates the wordmark, the page title, the metadata, and every
 * mention in the copy. Don't hardcode the name anywhere else.
 */
export const brand = {
  /**
   * WORKING TITLE, agreed 13 Aug: keep the repo's own name for now.
   * It cannot ship publicly — Spotify's developer terms forbid "Spotify" in a
   * product name — so this still has to change before anything goes out.
   * Change it here and the wordmark, title, metadata and copy all follow.
   */
  name: "bad spotify",

  /** Shown small above the wordmark. Optional. */
  eyebrow: "Introducing",

  tagline: "The worst music for the best moments.",
  taglineSecond: "And vice versa.",

  /** One sentence, for metadata and for anyone who asks what it is. */
  description:
    "A wearable agent that reads the room, works out exactly what it should play, and plays the opposite.",

  /** The three-beat statement. Kept short on purpose. */
  creed: ["It watches you.", "It understands you.", "It does not help you."],
} as const;

/**
 * Numbers for the specs strip. Keep these HONEST — a judge may ask, and
 * "we made it up" is a bad answer. Update as the real system is measured.
 */
export const specs = [
  { value: "5s", label: "between looks at the room" },
  { value: "3", label: "competing theories of wrong" },
  { value: "47", label: "songs, chosen by hand" },
  { value: "0", label: "requests taken" },
] as const;

/** The loop, for the how-it-works section. Mirrors PIPELINE.md. */
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
    body: "Three ideas of “worst” compete. The funniest wins.",
  },
  {
    n: "06",
    title: "Commit",
    body: "Queue it — or cut the music off, if the moment deserves it.",
  },
] as const;
