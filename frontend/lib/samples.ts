/**
 * The clips on offer in the picker.
 *
 * There is one, because there is one recorded run: `public/sessions/
 * sample.json`, a park read at 0s that gets Drowning Pool five seconds later.
 * The three invented options that used to be here — a kitchen, a bus, a
 * ceiling — were removed once the panel started showing real session data,
 * because picking "Dinner for one" and then reading "sunlit public park" in
 * the reasoning column is exactly the kind of mismatch that costs the whole
 * screen its credibility.
 *
 * `placeholder` is still true: the *decision* is real, the *footage* is not.
 * `sample.mp4` is the synthetic test clip, because nobody has filmed the park.
 * That flag drives the tag in the picker and the note under the video, so
 * dropping in real footage and clearing it removes both reminders at once.
 *
 * To add another: `python run.py --video yourclip.mp4 --record yourclip`, put
 * the JSON in `public/sessions/` and the footage in `public/videos/`, and give
 * `lib/cues.ts` the new import.
 */
export interface Sample {
  id: string;
  title: string;
  /** One line on what the agent is up against. */
  blurb: string;
  /** Timecode range, for the card. */
  length: string;
  src: string;
  /** Honest flag: the footage is not what it claims to be. */
  placeholder?: boolean;
}

export const samples: Sample[] = [
  {
    id: "park",
    title: "Sunlit park",
    blurb:
      "People reading on the grass, someone walking slowly on a path. Read as peaceful at 0.90 confidence — then answered with nu metal.",
    length: "00:30",
    src: "/videos/sample.mp4",
    placeholder: true,
  },
];
