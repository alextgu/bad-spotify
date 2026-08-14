
export const brand = {

  name: "DJ 180",


  eyebrow: "Introducing",

  tagline: "The worst music for the best moments.",
  taglineSecond: "And vice versa.",


  description:
    "A wearable agent that reads the room, works out exactly what it should play, and plays the opposite.",


  creed: ["It watches you.", "It understands you.", "It does not help you."],
} as const;


export const specs = [
  { value: "5s", label: "between looks at the room" },
  { value: "3", label: "competing theories of wrong" },
  { value: "47", label: "songs, chosen by hand" },
  { value: "0", label: "requests taken" },
] as const;


export const steps = [
  { n: "01", title: "Look", body: "A picture, and the last few seconds of sound." },
  {
    n: "02",
    title: "Notice",
    body: "Has anything changed? If not, don't waste the thinking.",
  },
  {
    n: "03",
    title: "Understand",
    body: "Where we are, what people are doing, how it feels.",
  },
  { n: "04", title: "Invert", body: "Work out the exact opposite of that feeling." },
  {
    n: "05",
    title: "Choose",
    body: "Three ideas of “worst” compete. The funniest wins.",
  },
  {
    n: "06",
    title: "Commit",
    body: "Queue it — or cut the music off, if the moment deserves it.",
  },
] as const;
