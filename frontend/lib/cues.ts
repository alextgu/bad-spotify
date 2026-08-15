import sessionFile from "@/public/sessions/sample.json";

/**
 * The try-it panel's data, read from the real recorded session.
 *
 * This used to be hand-written placeholder cues about a kitchen. It is now
 * `public/sessions/sample.json` — an actual run of the agent, written by
 * `session.py --record`, containing the scene it read, the mood it inverted
 * to, every candidate each strategy proposed with its score, and the track
 * that won. Nothing here is written by hand any more, which is the point: the
 * panel is showing the agent's own output rather than an impression of it.
 *
 * **The recording has one decision in it.** That is the honest state of the
 * repo — nobody has filmed a real clip and recorded a long run yet. So the
 * timeline has two marks rather than six: where the scene was read, and where
 * the song actually landed. That gap is worth showing on its own; it is the
 * thing the session format's own README warns about.
 *
 * To replace it: `python run.py --video yourclip.mp4 --record yourclip`, drop
 * the JSON in `public/sessions/` and the footage in `public/videos/`, and
 * change the import. The shape is the contract — see `lib/types.ts`.
 */

interface RawMoment {
  video_time: number;
  scene: {
    setting: string;
    activity: string;
    mood: string;
    confidence: number;
    tempo: string;
    meter: string;
    colors: string[];
    vibe: Record<string, number>;
  };
  opposite: {
    target_vibe: Record<string, number>;
    looking_for: string[];
    why: string;
  };
  considered: Record<
    string,
    { title: string; artist: string; score: number; why: string }[]
  >;
  chosen: {
    title: string;
    artist: string;
    quip: string;
    strategy: string;
    why: string;
  };
  played: { at_video_time: number; mode: string; latency_ms: number };
}

const raw = sessionFile as unknown as {
  session: string;
  source: string;
  moments: RawMoment[];
};

/** One point on the timeline: something the agent did, at a time in the clip. */
export interface Cue {
  /** Fraction through the clip. */
  at: number;
  time: string;
  label: string;
  sees: string;
  register: string;
  confidence: number;
  /** From the scene read, not a model timing. See the note in the component. */
  tempo: string;
  meter: string;
  palette: string[];
  track: string;
  artist: string;
  why: string;
  /** Newest first, printed as the HUD prints them. */
  log: string[];
  /** Every candidate every strategy proposed, in score order. */
  considered: { strategy: string; title: string; artist: string; score: number }[];
  /** The genres the inversion was hunting for. */
  lookingFor: string[];
}

const clock = (seconds: number) =>
  `${String(Math.floor(seconds / 60)).padStart(2, "0")}:${String(
    Math.floor(seconds % 60),
  ).padStart(2, "0")}`;

/** The clip's length isn't recorded, so the marks are placed against this. */
const ASSUMED_LENGTH_S = 30;

const moment = raw.moments[0];

const considered = Object.entries(moment.considered)
  .flatMap(([strategy, list]) =>
    list.map((c) => ({ strategy, title: c.title, artist: c.artist, score: c.score })),
  )
  .sort((a, b) => b.score - a.score);

/**
 * Two cues from one moment: the read, and the commit.
 *
 * They are genuinely different states — at 0s it has understood the park and
 * has not played anything; at 5s it has interrupted with Drowning Pool. The
 * session README singles this gap out, because using `video_time` for a
 * timeline instead of `played.at_video_time` puts every song several seconds
 * before it actually starts.
 */
export const cues: Cue[] = [
  {
    at: moment.video_time / ASSUMED_LENGTH_S,
    time: clock(moment.video_time),
    label: "Reads the park",
    sees: `${moment.scene.setting}, ${moment.scene.activity}`,
    register: moment.scene.mood,
    confidence: moment.scene.confidence,
    tempo: moment.scene.tempo,
    meter: moment.scene.meter,
    palette: moment.scene.colors,
    track: "—",
    artist: "Nothing yet",
    why: "It has read the room and not acted on it. The DJ needs a second agreeing read before it will commit.",
    log: [
      `READ  — ${moment.scene.mood} · confidence ${moment.scene.confidence.toFixed(2)} · tempo ${moment.scene.tempo}`,
      `INVERT — looking for ${moment.opposite.looking_for.slice(0, 3).join(", ")}`,
      "LOOK  — frame + 4s audio",
    ],
    considered: [],
    lookingFor: moment.opposite.looking_for,
  },
  {
    at: moment.played.at_video_time / ASSUMED_LENGTH_S,
    time: clock(moment.played.at_video_time),
    label: `Cuts in — ${moment.chosen.title}`,
    sees: `${moment.scene.setting}, ${moment.scene.activity}`,
    register: moment.scene.mood,
    confidence: moment.scene.confidence,
    tempo: moment.scene.tempo,
    meter: moment.scene.meter,
    palette: moment.scene.colors,
    track: moment.chosen.title,
    artist: moment.chosen.artist,
    why: moment.chosen.quip,
    log: [
      `PLAY  — ${moment.played.mode} · ${moment.chosen.strategy} won`,
      `JUDGE — ${moment.chosen.why}`,
      `INVERT — looking for ${moment.opposite.looking_for.slice(0, 3).join(", ")}`,
      `READ  — ${moment.scene.mood} · confidence ${moment.scene.confidence.toFixed(2)}`,
    ],
    considered,
    lookingFor: moment.opposite.looking_for,
  },
];

/** Where the recording came from, printed under the video. */
export const source = raw.source.split("/").pop() ?? raw.source;

/** The cue in force at a given fraction through the clip. */
export function cueAt(progress: number, list: Cue[] = cues): Cue {
  let current = list[0];
  for (const cue of list) if (progress >= cue.at) current = cue;
  return current;
}

/**
 * The same conversion, for a session the visitor produced themselves.
 *
 * `POST /api/analyze-video` returns the shape `session.py --record` writes, so
 * an uploaded clip and the shipped recording become the same thing here and
 * the panel cannot tell them apart. That is the point: the screen has to show
 * the agent's own output either way, or it is a mock-up with an upload button.
 *
 * Unlike the recording above, an uploaded clip's real duration IS known, so
 * the marks land where they belong rather than against an assumed 30s.
 */
export function cuesFromSession(raw: unknown, durationS: number): Cue[] {
  const doc = raw as { moments?: RawMoment[] };
  const moments = doc.moments ?? [];
  const length = durationS > 0 ? durationS : ASSUMED_LENGTH_S;

  return moments.map((m) => {
    const ranked = Object.entries(m.considered ?? {})
      .flatMap(([strategy, list]) =>
        (list ?? []).map((c) => ({
          strategy,
          title: c.title,
          artist: c.artist,
          score: c.score,
        })),
      )
      .sort((a, b) => b.score - a.score);

    const at = (m.played?.at_video_time ?? m.video_time) / length;
    return {
      at: Math.min(Math.max(at, 0), 0.999),
      time: clock(m.played?.at_video_time ?? m.video_time),
      label: `Cuts in — ${m.chosen.title}`,
      sees: [m.scene.setting, m.scene.activity].filter(Boolean).join(", "),
      register: m.scene.mood,
      confidence: m.scene.confidence,
      tempo: m.scene.tempo,
      meter: m.scene.meter,
      palette: m.scene.colors ?? [],
      track: m.chosen.title,
      artist: m.chosen.artist,
      why: m.chosen.quip || m.chosen.why || "",
      log: [
        `PLAY  — ${m.chosen.strategy} won`,
        `JUDGE — ${m.chosen.why}`,
        `INVERT — looking for ${(m.opposite?.looking_for ?? []).slice(0, 3).join(", ")}`,
        `READ  — ${m.scene.mood} · confidence ${Number(m.scene.confidence).toFixed(2)}`,
      ],
      considered: ranked,
      lookingFor: m.opposite?.looking_for ?? [],
    };
  });
}
