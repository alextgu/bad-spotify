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
  headline: "Music that",
  headlineRest: "narrates your",
  headlineAccent: "life",
  headlineTail: "in the worst possible way",
  /**
   * The caption under the headline, and the punchline of the screen.
   *
   * The headline is atmospheric and gives nothing away; this lands flat and
   * admits what the thing actually does. The gap between the two is the joke,
   * so it stays a single deadpan line — explaining it here would spend the
   * whole hero, and the FAQ is where the reasoning lives.
   */
  sub: "A peaceful trail becomes a metal rock concert.",
  shot: {
    file: "hero.mp4",
    note: [
      "fills the inset card · muted loop",
      "someone alone in a real room, headphones on",
      "slow push in · no faces to camera",
      "keep the LEFT THIRD dark — the type sits there",
    ],
  } satisfies Shot,
  /**
   * The floating card in the hero. Currently a coming-soon state rather than a
   * slot, because the cinematic has not been cut — kept here so that when it
   * exists this is where its filename and direction go, and the card in
   * `SectionHero` goes back to rendering a `Slot`.
   */
  clip: {
    file: "clip-teaser.mp4",
    note: ["15s loop", "not shot yet"],
  } satisfies Shot,
};

/* ------------------------------------------------------- 2 · description -- */
export const description = {
  statement: "We find the worst possible song for every occasion.",

  /**
   * What goes in and what comes out, as a chain rather than a paragraph.
   *
   * The glasses are the input and a Spotify track is the output, and the three
   * steps between them are the only claim the section makes. Each line is
   * short on purpose: this sits beside a rotating object and has to be
   * readable at a glance, not studied.
   */
  chain: [
    {
      step: "See",
      title: "Camera glasses catch the scene",
      body: "A frame every few seconds, plus a short slice of ambient sound.",
    },
    {
      step: "Read",
      title: "It understands the moment",
      body: "It identifies the setting, activity, and mood, then stops if the read is uncertain.",
    },
    {
      step: "Invert",
      title: "It finds the musical opposite",
      body: "Five mood axes flip, then six competing strategies argue over what fits worst.",
    },
    {
      step: "Play",
      title: "Spotify plays the worst fit",
      body: "The winner is queued or cut in, with the reason shown alongside it.",
    },
  ],
  /** Three moves. Any more and this stops fitting one screen. */
  points: [
    { title: "Reads the room", body: "Light, motion, reverb, who else is here" },
    { title: "Scores it", body: "Energy, valence, tension" },
    { title: "Drops the needle", body: "Perfect, or exactly wrong" },
  ],
  /**
   * Two worked examples, shown one at a time as the section is scrolled.
   *
   * **Both are real output.** `park -> Bodies` is lifted from the recorded run
   * in public/sessions/sample.json, down to the 0.911 score and the genres the
   * inversion went hunting for. `library -> Sandstorm` is the other case the
   * headless run is checked against — see the verified commands in AGENTS.md.
   *
   * Two, not four. The point lands on the second one; a third is a list.
   */
  examples: [
    {
      id: "park",
      scene: "A sunlit park",
      read: "peaceful · confidence 0.90 · slow",
      track: "Bodies",
      artist: "Drowning Pool",
      why: "It scored the park as about as pleasant as a scene gets, inverted that, and went looking for funeral doom, drone and noise. Nu metal was the closest thing in the corpus, at 0.911 — the highest wrongness score of anything it considered.",
      shot: {
        file: "example-park.jpg",
        note: ["16:9 · grass, low sun, people sitting", "no faces, nothing happening"],
      } satisfies Shot,
    },
    {
      id: "library",
      scene: "A quiet library",
      read: "still · low arousal · steady",
      track: "Sandstorm",
      artist: "Darude",
      why: "A different strategy wins here. Nothing in the room is loud, so genre distance has little to work with — tempo_clash takes it instead, on the grounds that the one thing a silent room cannot survive is relentless arousal.",
      shot: {
        file: "example-library.jpg",
        note: ["16:9 · long desks, warm lamps, stacks behind", "one person, far away"],
      } satisfies Shot,
    },
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
  caption: { left: "Live capture", right: "vision read: 1.17s median" },
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
  /* One sentence. It was three, and the third column of notes below had
     nowhere to go — this screen is the diagram, not the prose. */
  body: "Six steps, about every five seconds. The two worth watching are where the line bends.",
  /**
   * The three decisions underneath the diagram that a drawing can't show.
   * Kept to three because the diagram is the subject of the screen and this
   * is the caption — a fourth would push the section past one viewport.
   */
  notes: [
    {
      title: "Distance defends, the model lands it",
      body: "The mood vector is reflected through the centre of the cube — instant, and arguable. But distance alone picks noise records nobody knows. Only a model knows the true opposite of a sunlit park is funeral doom.",
    },
    {
      title: "Six theories that disagree",
      body: "Wrong on every axis, wrong about energy, wrong in meaning, wrong about the setting, wrong about the occasion, and one that goes looking outside the corpus. Three that argue beat five that agree.",
    },
    {
      title: "It knows when it doesn't know",
      body: "Below 0.35 confidence it does nothing. Pointed at an unreadable frame it reported “obstructed or blocked camera view” at 0.10 and correctly refused to act.",
    },
  ],
} as const;

/* ----------------------------------------------------------- 6 · results -- */
export const results = {
  title: "What came out of it.",
  /**
   * Every one of these is measured or countable in the repo.
   *
   * "1.4s scene to sound" used to sit here and has been removed: the vision
   * call is measured at a 1.17s median across four models, three calls each,
   * but nothing measures the full scene-to-speaker path, so the number was a
   * guess wearing a decimal point.
   */
  metrics: [
    { value: "1.17", unit: "s", label: "Scene read, median" },
    { value: "215", unit: "", label: "Tests" },
    { value: "47", unit: "", label: "Songs, by hand" },
    { value: "0", unit: "", label: "Images stored" },
  ],
  /** Things that are true, and checkable in the repo. Keep it to three. */
  proud: [
    {
      title: "It is never silent",
      body: "Every model, player and voice degrades to a stand-in, and under all of them sits a pre-picked fallback deck. Silence is the only real bug.",
    },
    {
      title: "The reasoning is the product",
      body: "Watching it read a room correctly and then queue the worst possible answer is the whole thing in one screen. A shuffle button can't show its working.",
    },
    {
      title: "Nothing here is faked",
      body: "Where something is a placeholder the interface says so. The bundled clips carry real Gemini sessions, and an upload either shows its own analysis or fails plainly.",
    },
  ],
} as const;

/* --------------------------------------------------------------- 7 · faq -- */
/**
 * Answers, not punchlines.
 *
 * These were one-liners reaching for a laugh — "everyone who tried it left it
 * on Cursed" — and they cost the section its job. This is the last screen, it
 * is where a sceptic goes to find out whether the thing is real, and a joke
 * there reads as not having an answer. The page is funny enough by then; the
 * FAQ is where it stops performing and shows its working.
 *
 * Every number below is measured and lives somewhere in the repo. Do not add
 * one that isn't.
 */
export const faq = [
  {
    q: "Is it watching me all day?",
    a: "It takes one frame about every five seconds, gets a sentence back from the model, and discards the image. Nothing is stored — the read it keeps is text like “sunlit public park, people reading on the grass”. Most ticks never reach a model at all: a local change gate drops the frame when the room hasn't moved.",
  },
  {
    q: "Why would anyone want the wrong song?",
    a: "Because deliberately wrong is the only version you can check. A recommender aiming to be right hides its failures in taste; when the goal is the opposite of the room, every pick is falsifiable — you can see the read, the inversion, and whether it followed. Flip one sign and the same machinery hunts for the best song instead.",
  },
  {
    q: "Doesn't Spotify already do this?",
    a: "Spotify recommends from listening history. The input here is the physical scene in front of a camera: setting, activity, light, and how confident the read is. Spotify is playback only — their audio-features endpoints closed to new apps in 2024, so scoring runs on our own hand-built corpus of 47 tracks.",
  },
  {
    q: "Why is the logo the opposite?",
    a: "The big music apps converge on dark, round, and green; ours is light, square, and purple for the same reason the music is wrong — it turns round what the moment expects. It is also deliberate AI slop, gradient and sparkles and watermark included. Naming the tells is the point.",
  },
  {
    q: "What's real and what isn't?",
    a: "Perception has run live on three filmed clips, and the site replays those recorded sessions with the losing candidates and scores. Unproven: the Spotify player is tested only against a stand-in, and nobody has heard a track from a real speaker yet. Your own upload needs the local agent running, and says so.",
  },
  {
    q: "Isn't this one prompt in a trenchcoat?",
    a: "The prompt is the cheapest part — two model calls per decision at most. Around it: a change gate that skips perception when nothing moved, six strategies that genuinely disagree about what “wrong” means, a judge that picks between them, and a sampler at temperature 0.20 so one room doesn't produce one answer forever.",
  },
  {
    q: "What broke along the way?",
    a: "A four-second timeout sat below the model's real 5–8s latency, so every call silently fell back to a canned read and looked fine. Two safety mechanisms deadlocked and nothing played on calm footage. And the DJ changed track every other tick on a static scene until it gated on the inverted target — 62 seconds went from six tracks to one.",
  },
] as const;

export const footer = { right: "Built in 48~ish hours" };
