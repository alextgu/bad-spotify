/**
 * The contract between the agent and this site.
 *
 * These types mirror exactly what `python run.py --video clip.mp4 --record NAME`
 * writes to `data/sessions/NAME.json`. If the backend changes that shape, this
 * file is the first thing to update -- everything else is typed off it.
 *
 * The site never calls the agent. It reads one of these files. That is why it
 * can be hosted anywhere, needs no API keys, and cannot fail during a demo.
 */

/** All five axes run 0..1. Both the scene and the target song sit in this space. */
export interface Vibe {
  valence: number;      // bleak -> joyful
  arousal: number;      // still -> frantic
  density: number;      // sparse -> overwhelming
  brightness: number;   // dark -> glaring
  organicness: number;  // synthetic -> human
}

export interface Scene {
  setting: string | null;
  activity: string | null;
  mood: string | null;
  confidence: number | null;
  tempo: string | null;
  meter: string | null;
  colors: string[];     // hex, straight from the frame -- good for theming
  vibe: Partial<Vibe>;
}

export interface Opposite {
  target_vibe: Partial<Vibe>;
  looking_for: string[];   // the genres/tags it decided would be worst
  why: string;
}

export interface CandidatePick {
  title: string;
  artist?: string;
  score?: number;
  why?: string;
}

/** Keyed by strategy name: genre_antipode | tempo_clash | lyrical_irony */
export type Considered = Record<string, CandidatePick[]>;

export interface Chosen {
  title: string;
  artist: string | null;
  quip: string | null;      // what it says out loud
  strategy: string | null;  // which theory of wrongness won
  /** How far apart the moment and the music turned out to be, 0-1.
   *  MEASURED after the fact. There is deliberately no dial for it. */
  mismatch: number | null;
  why: string | null;
  runner_ups: string[];
}

export interface Played {
  /** Where in the video the song actually starts. USE THIS for the timeline. */
  at_video_time: number | null;
  /** "queue" lines it up next; "interrupt" cuts the current song off. */
  mode: "queue" | "interrupt" | null;
  track_id: string | null;
  genres: string[];
  latency_ms: number | null;
}

export interface Moment {
  /** Where the scene was READ. Usually a few seconds before it played. */
  video_time: number | null;
  wall_time: number;
  scene: Scene;
  opposite?: Opposite;
  considered?: Considered;
  chosen?: Chosen;
  played?: Played;
}

export interface Session {
  session: string;
  source: string;
  moment_count: number;
  sample_interval_s?: number;
  duration_s?: number;
  model?: string;
  README: string;
  moments: Moment[];
}

/** Seconds -> "01:23". Timeline labels want this everywhere. */
export function stamp(seconds: number | null | undefined): string {
  if (seconds == null || !Number.isFinite(seconds)) return "--:--";
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
}

/** When the song lands, falling back to when the scene was read. */
export function momentTime(m: Moment): number {
  return m.played?.at_video_time ?? m.video_time ?? 0;
}

/** How wrong this pick is: distance between the scene and the target. */
export function vibeGap(m: Moment): number {
  const a = m.scene?.vibe ?? {};
  const b = m.opposite?.target_vibe ?? {};
  const keys: (keyof Vibe)[] = [
    "valence", "arousal", "density", "brightness", "organicness",
  ];
  const sum = keys.reduce((acc, k) => {
    const d = (a[k] ?? 0.5) - (b[k] ?? 0.5);
    return acc + d * d;
  }, 0);
  return Math.sqrt(sum);
}
