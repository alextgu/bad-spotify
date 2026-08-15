/**
 * The clips on offer in the picker.
 *
 * **All three currently resolve to the same file.** `public/videos/sample.mp4`
 * is the synthetic green test clip the repo ships, and the other two moments
 * have not been filmed. They are listed anyway, flagged `placeholder`, because
 * the alternative is a picker with one option in it — and because the flag is
 * the only switch: it drives the tag in the picker and the note in the
 * workbench, so shooting the footage and pointing `src` at it removes every
 * reminder at once.
 *
 * Written this way on purpose. The failure being designed out is someone
 * swapping in real footage and leaving "placeholder" showing in two other
 * places they didn't know about.
 */
export interface Sample {
  id: string;
  title: string;
  /** One line on what the agent is up against. */
  blurb: string;
  /** Timecode range, for the card. */
  length: string;
  src: string;
  /** Honest flag: this is not the footage it claims to be. */
  placeholder?: boolean;
}

export const samples: Sample[] = [
  {
    id: "kitchen",
    title: "Dinner for one",
    blurb: "A small kitchen at night. One pan, one plate, nobody else.",
    length: "01:12",
    src: "/videos/sample.mp4",
    placeholder: true,
  },
  {
    id: "rain",
    title: "Running for the 44",
    blurb: "Rain on glass, motion blur, somebody late for something.",
    length: "00:48",
    src: "/videos/sample.mp4",
    placeholder: true,
  },
  {
    id: "ceiling",
    title: "Ceiling, again",
    blurb: "A dark room, a phone glow, and no intention of sleeping.",
    length: "01:30",
    src: "/videos/sample.mp4",
    placeholder: true,
  },
];
