/**
 * The preset clips on offer in "Try it yourself".
 *
 * A preset is a pair: footage, and the session file the agent produced when it
 * watched that footage. Both are static assets — the site never calls the
 * agent, so nothing here can fail on stage.
 *
 * To add one:
 *   python run.py --video myclip.mp4 --record mycliip
 *   cp myclip.mp4                     frontend/public/videos/myclip.mp4
 *   cp data/sessions/myclip.json      frontend/public/sessions/myclip.json
 * ...then add a row below.
 */
export interface Clip {
  id: string;
  label: string;
  /** One line on what the agent was up against. */
  blurb: string;
  video: string;
  session: string;
  /** Honest flag: placeholder footage, not a real recording. */
  placeholder?: boolean;
}

export const CLIPS: Clip[] = [
  {
    id: "sample",
    label: "Sample run",
    blurb:
      "Placeholder footage — a synthetic clip, kept only so this page works on a fresh clone. Replace with real filming.",
    video: "/videos/sample.mp4",
    session: "/sessions/sample.json",
    placeholder: true,
  },
];
