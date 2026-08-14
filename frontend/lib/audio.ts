/**
 * The agent's recorded voice lines.
 *
 * **Character note, and it is load-bearing: the agent thinks it is doing a
 * good job.** It is a conscientious DJ, pleased with its choices, sincerely
 * confident it has matched the room. It never winks, never jokes, never
 * acknowledges a mismatch. Every line here must be one a genuinely helpful DJ
 * would say. The comedy is the gap between that sincerity and the pick — the
 * moment a line is knowing, it collapses into someone doing a bit.
 *
 * These are pre-rendered on purpose. The site is static and has no API key, so
 * anything spoken here is a file that shipped with the page — no request, no
 * latency, nothing to fail on stage.
 *
 * **The files do not exist yet**, and that is deliberate: the project isn't
 * named, and the name is in the first line. Everything is wired anyway, so
 * adding them later is one command and no code:
 *
 *     python scripts/voice_lines.py --list        # pick a voice
 *     python scripts/voice_lines.py --audition    # ...by ear
 *     python scripts/voice_lines.py --render      # writes these files
 *
 * Until then the UI shows the line as text instead of playing it, which reads
 * as "not recorded yet" rather than as a broken button. `text` is what it will
 * say and what a screen reader gets either way — keep the two identical, and
 * keep the keys in step with LINES in the render script.
 */
export interface VoiceLine {
  /** Under frontend/public/. Written by scripts/voice_lines.py --render. */
  file: string;
  /** The exact words. Shown when the audio isn't there, and used as a caption. */
  text: string;
}

export const VOICE_LINES = {
  /** Also the line the running program speaks at startup. Re-render when the
   *  project is named -- the greeting says the name. */
  intro: {
    file: "/audio/intro.mp3",
    text: "Hello. I'm your DJ. I'll help you choose the perfect music for any moment.",
  },
  nowPlaying: {
    file: "/audio/now-playing.mp3",
    text: "Now playing Bodies by Drowning Pool — the perfect fit for your silent library during exam week.",
  },
  noRequests: {
    file: "/audio/no-requests.mp3",
    text: "No need for requests. I already know what this moment needs.",
  },
} as const satisfies Record<string, VoiceLine>;

export type VoiceLineKey = keyof typeof VOICE_LINES;
