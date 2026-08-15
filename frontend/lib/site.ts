/**
 * Every word on the landing page, in one file.
 *
 * The page is seven screens and each screen is exactly one viewport — so the
 * real constraint on everything here is that it has to FIT. If a section grows
 * a second paragraph it stops being one page, and the whole structure goes
 * with it. Cut rather than shrink the type.
 *
 * The shoot list lives here too, as the `shot` on each slot: the page renders
 * what it is waiting for, so there is no separate document to keep in sync.
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

/* -------------------------------------------------------------- 1 · hero -- */
export const hero = {
  headline: "Music for the room you're",
  headlineAccent: "in",
  /**
   * The caption under the headline, and the punchline of the screen.
   *
   * The headline is atmospheric and gives nothing away; this lands flat and
   * admits what the thing actually does. The gap between the two is the joke,
   * so it stays a single deadpan line — explaining it here would spend the
   * whole hero, and the FAQ is where the reasoning lives.
   */
  sub: "Picks the worst possible music for your life.",
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

/* ------------------------------------------------------- 2 · description -- */
export const description = {
  statement:
    "Your phone knows what you played last Tuesday. It has never once looked up.",
  /** Three moves. Any more and this stops fitting one screen. */
  points: [
    { title: "Reads the room", body: "Light, motion, reverb, who else is here" },
    { title: "Scores it", body: "Energy, valence, tension" },
    { title: "Drops the needle", body: "Perfect, or exactly wrong" },
  ],
} as const;

/* -------------------------------------------------------------- 3 · demo -- */
export const demo = {
  film: {
    file: "demo.mp4",
    note: [
      "full bleed · 21:9 · unedited screen capture",
      "phone in hand, song audibly changing",
      "keep under 60s",
    ],
  } satisfies Shot,
  caption: { left: "Live capture", right: "1.4s, scene to sound" },
};

/* ------------------------------------------------------------ 4 · try it -- */
export const tryIt = {
  title: "Try it on your own footage.",
  body: "Drop in a video. It reads the mood every few seconds and shows you which track it would have put on, and where.",
  /** The demo ground is a real route in this app — see app/demo/page.tsx. */
  action: { label: "Open the demo", href: "/demo" },
  note: "Runs against a local model. Ships with a sample clip, so it works with nothing plugged in.",
} as const;

/* ---------------------------------------------------------- 5 · pipeline -- */
export const pipeline = {
  title: "A closer look.",
  body: "Six steps, about every five seconds. The two that matter are the ones where the line bends: nothing changes, so it doesn't spend a model call — and six theories of the right wrong answer, argued out by a judge.",
} as const;

/* ----------------------------------------------------------- 6 · results -- */
export const results = {
  title: "What came out of it.",
  metrics: [
    { value: "1.4", unit: "s", label: "Scene to sound" },
    { value: "40", unit: "kb", label: "Per sample" },
    { value: "0", unit: "", label: "Images stored" },
    { value: "6", unit: "", label: "Cues per day" },
  ],
  /** Things that are true, and checkable in the repo. Keep it to three. */
  proud: [
    {
      title: "It is never silent",
      body: "Every model, player and voice degrades to a stand-in, and under all of them sits a pre-picked fallback deck.",
    },
    {
      title: "Six theories, not one score",
      body: "Mood, tempo, lyrics, setting, occasion and catalogue each propose a different wrong answer. A judge picks between them.",
    },
    {
      title: "192 tests",
      body: "Each one guarding a specific way the demo could break, including the three that already had.",
    },
  ],
} as const;

/* --------------------------------------------------------------- 7 · faq -- */
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
