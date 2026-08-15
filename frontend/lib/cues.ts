/**
 * What the agent was doing at each point in the sample clip.
 *
 * PLACEHOLDER DATA. The shape deliberately mirrors what the live HUD shows and
 * what `public/sessions/sample.json` already records — scene read, confidence,
 * latency, the palette pulled out of the frame, the track, and the running
 * decision log. When the try-it panel is wired to the session file, this file
 * is deleted and the same fields come from there.
 *
 * `at` is a fraction of the clip, because the scrub knows progress, not
 * seconds — the video's duration is not known until its metadata loads.
 */
export interface Cue {
  /** Fraction through the clip, 0–1. */
  at: number;
  /** Timecode shown on the timeline. */
  time: string;
  /** Short label on the timeline itself. */
  label: string;
  /** The scene read, as a sentence. */
  sees: string;
  register: string;
  confidence: number;
  /** Milliseconds the read took. */
  latency: number;
  model: string;
  /** Colours pulled out of the frame. Any length; four reads best. */
  palette: string[];
  track: string;
  artist: string;
  /** One line on why that track, shown under it. */
  why: string;
  /** Newest first. Mono, timestamped, exactly as the HUD prints them. */
  log: string[];
}

export const cues: Cue[] = [
  {
    at: 0,
    time: "00:00",
    label: "Kitchen, warm light",
    sees: "a small kitchen at night, one pan on the hob, nobody else in frame",
    register: "domestic",
    confidence: 0.88,
    latency: 1204,
    model: "gemini",
    palette: ["#2A2724", "#C8B79A", "#7C6A52", "#E4DED4"],
    track: "Duel of the Fates",
    artist: "John Williams",
    why: "Dinner for one, scored like the end of a war.",
    log: [
      "PLAY  — target gate approved; scene shifted 0.71",
      "READ  — domestic · confidence 0.88 · 1204ms via gemini",
      "LOOK  — frame + 4s audio",
    ],
  },
  {
    at: 0.26,
    time: "00:18",
    label: "Someone leaves",
    sees: "the same kitchen, a door closing at the edge of frame, one place setting",
    register: "domestic",
    confidence: 0.81,
    latency: 1338,
    model: "gemini",
    palette: ["#241F1C", "#B7A98C", "#6E5C46", "#DCD4C8"],
    track: "Duel of the Fates",
    artist: "John Williams",
    why: "Holding. The room did not change enough to be worth a new pick.",
    log: [
      "HOLD  — target moved 0.12 < 0.30; still the right answer",
      "READ  — domestic · confidence 0.81 · 1338ms via gemini",
      "LOOK  — frame + 4s audio",
    ],
  },
  {
    at: 0.45,
    time: "00:31",
    label: "Lights down",
    sees: "the room darker now, a single lamp, plates cleared to one side",
    register: "solitary",
    confidence: 0.9,
    latency: 1121,
    model: "gemini",
    palette: ["#15120F", "#8E7A5E", "#4A3D2E", "#C9BCA6"],
    track: "Macarena",
    artist: "Los del Río",
    why: "The room went quiet, so it did not.",
    log: [
      "PLAY  — interrupt earned; scene shifted 0.62 after 31s",
      "JUDGE — register_clash beat genre_antipode",
      "READ  — solitary · confidence 0.90 · 1121ms via gemini",
    ],
  },
  {
    at: 0.68,
    time: "00:47",
    label: "Room empties",
    sees: "an empty room, the lamp still on, no movement for several seconds",
    register: "empty",
    confidence: 0.72,
    latency: 1402,
    model: "gemini",
    palette: ["#100E0C", "#6F5F49", "#3A3128", "#B9AC97"],
    track: "Macarena",
    artist: "Los del Río",
    why: "Nobody there to be wrong at. Still playing.",
    log: [
      "HOLD  — target moved 0.08 < 0.30; still the right answer",
      "READ  — empty · confidence 0.72 · 1402ms via gemini",
      "LOOK  — frame + 4s audio",
    ],
  },
  {
    at: 0.92,
    time: "01:06",
    label: "Quiet",
    sees: "the lamp off, the room lit only from the window, nothing moving",
    register: "empty",
    confidence: 0.64,
    latency: 1290,
    model: "gemini",
    palette: ["#0C0B0A", "#5A4E3E", "#2B2620", "#A79A85"],
    track: "Macarena",
    artist: "Los del Río",
    why: "Confidence dropping. One more quiet read and it stops deciding.",
    log: [
      "HOLD  — confidence 0.64 near the 0.35 floor",
      "READ  — empty · confidence 0.64 · 1290ms via gemini",
      "LOOK  — frame + 4s audio",
    ],
  },
];

/** The cue in force at a given fraction through the clip. */
export function cueAt(progress: number): Cue {
  let current = cues[0];
  for (const cue of cues) if (progress >= cue.at) current = cue;
  return current;
}
