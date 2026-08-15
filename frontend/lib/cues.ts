import type { Session } from "@/lib/types";
import { momentTime, stamp } from "@/lib/types";

/** One point on the timeline: something the agent did, at a time in the clip. */
export interface Cue {
  at: number;
  time: string;
  label: string;
  sees: string;
  register: string;
  confidence: number;
  tempo: string;
  meter: string;
  palette: string[];
  track: string;
  artist: string;
  why: string;
  log: string[];
  considered: { strategy: string; title: string; artist: string; score: number }[];
  lookingFor: string[];
}

const fallbackCue: Cue = {
  at: 0,
  time: "00:00",
  label: "No decision recorded",
  sees: "No usable scene was recorded for this clip.",
  register: "unknown",
  confidence: 0,
  tempo: "unknown",
  meter: "unknown",
  palette: [],
  track: "-",
  artist: "Nothing selected",
  why: "The analyzer did not produce a playable moment.",
  log: ["HOLD - no recorded decision"],
  considered: [],
  lookingFor: [],
};

function buildCues(session: Session, durationS: number): Cue[] {
  const duration = Math.max(durationS || session.duration_s || 1, 1);

  return (session.moments ?? []).flatMap((moment): Cue[] => {
    const chosen = moment.chosen;
    const played = moment.played;
    if (!chosen?.title || !played) return [];

    const seconds = momentTime(moment);
    const considered = Object.entries(moment.considered ?? {})
      .flatMap(([strategy, list]) =>
        list.map((candidate) => ({
          strategy,
          title: candidate.title,
          artist: candidate.artist ?? "Unknown artist",
          score: candidate.score ?? 0,
        })),
      )
      .sort((a, b) => b.score - a.score);

    const setting = moment.scene.setting ?? "unknown setting";
    const activity = moment.scene.activity;
    const confidence = moment.scene.confidence ?? 0;
    const lookingFor = moment.opposite?.looking_for ?? [];
    const strategy = chosen.strategy ?? "local judge";
    const action = played.mode ? played.mode.toUpperCase() : "SELECT";

    return [
      {
        at: Math.max(0, Math.min(seconds / duration, 1)),
        time: stamp(seconds),
        label: `Chooses - ${chosen.title}`,
        sees: activity ? `${setting}, ${activity}` : setting,
        register: moment.scene.mood ?? "unknown",
        confidence,
        tempo: moment.scene.tempo ?? "unknown",
        meter: moment.scene.meter ?? "unknown",
        palette: moment.scene.colors ?? [],
        track: chosen.title,
        artist: chosen.artist ?? "Unknown artist",
        why: chosen.quip ?? chosen.why ?? "Chosen as the strongest mismatch.",
        log: [
          `${action} - ${strategy} won`,
          `JUDGE - ${chosen.why ?? "strongest available mismatch"}`,
          `INVERT - looking for ${lookingFor.slice(0, 3).join(", ") || "an opposite"}`,
          `READ - ${moment.scene.mood ?? "unknown"} / confidence ${confidence.toFixed(2)}`,
        ],
        considered,
        lookingFor,
      },
    ];
  });
}

/** Build workbench checkpoints from a selected clip's recorded session. */
export function cuesFor(session: Session, durationS: number): Cue[] {
  const built = buildCues(session, durationS);
  return built.length ? built : [fallbackCue];
}

/** Convert an uploaded analysis response without hiding an empty result. */
export function cuesFromSession(raw: unknown, durationS: number): Cue[] {
  return buildCues(raw as Session, durationS);
}

/** The cue in force at a given fraction through the selected clip. */
export function cueAt(progress: number, list: Cue[]): Cue {
  let current = list[0] ?? fallbackCue;
  for (const cue of list) if (progress >= cue.at) current = cue;
  return current;
}
