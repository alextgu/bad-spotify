/**
 * The agent's recorded voice lines.
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
  intro: {
    file: "/audio/intro.mp3",
    text: "I'm the DJ. I have read the room, and I have decided against it.",
  },
  nowPlaying: {
    file: "/audio/now-playing.mp3",
    text: "Now playing Bodies by Drowning Pool, for your silent library during exam week.",
  },
  noRequests: {
    file: "/audio/no-requests.mp3",
    text: "I do not take requests.",
  },
} as const satisfies Record<string, VoiceLine>;

export type VoiceLineKey = keyof typeof VOICE_LINES;
