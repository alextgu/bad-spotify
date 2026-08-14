/**
 * The preset clips on offer in "Try it yourself", and the film at the top.
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


/* ---------------------------------------------------------------------------
   Swapping the placeholder for real footage
   ---------------------------------------------------------------------------

   The site currently ships synthetic footage so a fresh clone renders. When
   the real film exists:

     python run.py --video myfilm.mp4 --record myfilm
     cp myfilm.mp4                  frontend/public/videos/myfilm.mp4
     cp data/sessions/myfilm.json   frontend/public/sessions/myfilm.json

   ...then add a row above and DELETE `placeholder: true`. That flag is the
   only switch: it drives the warning under the film, the note in the picker,
   and the dev banner. Nothing else needs touching, and nothing has to be
   remembered — remove the flag and every reminder disappears at once.

   Written this way on purpose. The failure we're designing out is shipping a
   green test pattern as the second thing a judge sees, because the person who
   swapped the file didn't know there were three other places that said
   "placeholder".
--------------------------------------------------------------------------- */

/** The film at the top of the page. First entry, always. */
export const FILM: Clip = CLIPS[0];

/** Every clip still standing in for something real. */
export function placeholderClips(): Clip[] {
  return CLIPS.filter((c) => c.placeholder);
}

/** True while any asset on the page is still synthetic. */
export function hasPlaceholders(): boolean {
  return placeholderClips().length > 0;
}
