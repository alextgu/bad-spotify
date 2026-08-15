/**
 * Every word on the landing page, in one file.
 *
 * The page's rule is that the picture is the argument and the text is a
 * caption under it — so there is deliberately not much here, and any section
 * that grows a paragraph has probably lost its image.
 *
 * The shoot list lives here too, as the `shot` and `note` on each slot: the
 * page renders what it is waiting for, so there is no separate document to
 * keep in sync.
 */

/** A photograph or film that has not been shot yet. */
export interface Shot {
  /** Filename to drop into `public/`. Rendered in the placeholder. */
  readonly file: string;
  /**
   * Art direction. Rendered in the placeholder, one line per entry.
   *
   * `readonly` so that the `as const` data below — which is what makes the
   * copy literal-typed and stops a stray edit from widening it to `string` —
   * still satisfies this shape. Nothing ever mutates a shot note.
   */
  readonly note: readonly string[];
}

export const hero = {
  headline: "Music for the room you're",
  /** Set in italic serif — the only emphasis on the page. */
  headlineAccent: "in",
  sub: "It reads the room you're standing in, not the songs you played last Tuesday.",
  shot: {
    file: "hero.mp4",
    note: [
      "fills the inset card · muted loop",
      "someone alone in a real room, headphones on",
      "slow push in · no faces to camera",
      "keep the LEFT THIRD dark — the type sits there",
    ],
  } satisfies Shot,
  clip: {
    file: "clip-teaser.mp4",
    note: ["15s loop"],
  } satisfies Shot,
};

export const statement =
  "Your phone knows what you played last Tuesday. It has never once looked up.";

export const trio = [
  { title: "Reads the room", body: "Light, motion, reverb, who else is here" },
  { title: "Scores it", body: "Energy, valence, tension" },
  { title: "Drops the needle", body: "Perfect, or exactly wrong" },
] as const;

/* --------------------------------------------------------------------------
   Sections 4 and 5 of the mockup are one section now: the film, then the
   three moments underneath it, read as a single piece of evidence rather than
   as a film followed by an unrelated grid.
-------------------------------------------------------------------------- */
export const evidence = {
  film: {
    file: "demo.mp4",
    note: [
      "full bleed · 21:9 · unedited screen capture",
      "phone in hand, song audibly changing",
      "keep under 60s",
    ],
  } satisfies Shot,
  filmCaption: { left: "Live capture", right: "1.4s, scene to sound" },
  moments: [
    {
      time: "18:30",
      title: "Dinner for one",
      shot: {
        file: "moment-kitchen.jpg",
        note: ["4:5 · one pan, warm light", "no face"],
      } satisfies Shot,
    },
    {
      time: "08:41",
      title: "Running for the 44",
      shot: {
        file: "moment-bus.jpg",
        note: ["4:5 · rain on glass, motion blur", "shot from the seat"],
      } satisfies Shot,
    },
    {
      time: "23:47",
      title: "Ceiling, again",
      shot: {
        file: "moment-ceiling.jpg",
        note: ["4:5 · dark room, phone glow", "ceiling from the bed"],
      } satisfies Shot,
    },
  ],
};

/** The three panels that change as the day scrolls past. */
export const dayPanels = [
  { index: "01", label: "Sense", title: "It reads the room." },
  { index: "02", label: "Score", title: "Space becomes three numbers." },
  { index: "03", label: "Cue", title: "Then it drops the needle." },
] as const;

/** One day, six cues. Image first; the song is the caption. */
export const day = [
  {
    time: "07:12",
    title: "Third snooze",
    track: "Ride of the Valkyries",
    artist: "Wagner",
    shot: { file: "cue-01-bed.jpg", note: ["4:5", "dark bedroom, phone face down"] },
  },
  {
    time: "08:41",
    title: "Running for the 44",
    track: "The Sound of Silence",
    artist: "Simon & Garfunkel",
    shot: { file: "cue-02-rain.jpg", note: ["4:5", "rain, motion blur, running"] },
  },
  {
    time: "11:20",
    title: "Camera off",
    track: "Careless Whisper",
    artist: "George Michael",
    shot: { file: "cue-03-desk.jpg", note: ["4:5", "laptop, grid of faces, muted"] },
  },
  {
    time: "13:05",
    title: "Dumped, by text",
    track: "Celebration",
    artist: "Kool & The Gang",
    shot: { file: "cue-04-pavement.jpg", note: ["4:5", "wet pavement, phone in hand"] },
  },
  {
    time: "18:30",
    title: "Dinner for one",
    track: "Duel of the Fates",
    artist: "John Williams",
    shot: { file: "cue-05-kitchen.jpg", note: ["4:5", "one pan, warm light"] },
  },
  {
    time: "23:47",
    title: "Ceiling, again",
    track: "Macarena",
    artist: "Los del Río",
    shot: { file: "cue-06-ceiling.jpg", note: ["4:5", "ceiling, phone glow"] },
  },
] as const;

/**
 * Four numbers, printed rather than counted up.
 *
 * The mockup animated these from zero. A number that spins is a number
 * asking to be admired — and two of these are interesting precisely because
 * they are small. `0 images stored` loses everything by arriving as a
 * flourish; it should just be sitting there, already true.
 */
export const metrics = [
  { value: "1.4", unit: "s", label: "Scene to sound" },
  { value: "40", unit: "kb", label: "Per sample" },
  { value: "0", unit: "", label: "Images stored" },
  { value: "6", unit: "", label: "Cues per day" },
] as const;

export const broke = {
  title: "What broke in the first six hours.",
  items: [
    "Spotify audio features",
    "Always-on camera",
    "Cursed mode as the side joke",
  ],
} as const;

export const invite = {
  lines: ["Twenty people.", "One week each."],
  shot: {
    file: "prefooter.jpg",
    note: [
      "full bleed · 88vh · the product held, in daylight",
      "warmest frame you have",
    ],
  } satisfies Shot,
  actions: [
    { label: "Get the build", href: "#", primary: true },
    { label: "Repo", href: "#", primary: false },
  ],
};

export const faq = [
  {
    q: "Is it watching me all day?",
    a: "It samples a frame every four seconds, turns it into a sentence, and throws the image away.",
  },
  {
    q: "Why would I want the wrong song?",
    a: "Everyone who tried it left it on Cursed.",
  },
  {
    q: "Doesn't Spotify already do this?",
    a: "From your history, not from the room you're standing in.",
  },
  {
    q: "What's faked for the demo?",
    a: "The scene-change threshold is hand-tuned per location; everything else is live.",
  },
  {
    q: "Isn't this one prompt in a trenchcoat?",
    a: "The prompt is the cheapest part and we're not pretending otherwise.",
  },
] as const;

export const footer = { right: "Built in 24 hours" };
