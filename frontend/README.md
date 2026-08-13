# bad spotify — presentation site

The site judges look at. **Not a product**: it does not run the agent, it
replays a recording of the agent. That's deliberate — no backend to host, no
API keys in a browser, and nothing that can fail live.

```bash
npm install
npm run dev          # http://localhost:3000
```

## How it connects to the agent

There is exactly one seam, and it's a file:

```bash
# in the repo root, not here
python run.py --video yourclip.mp4 --record sample
cp data/sessions/sample.json frontend/public/sessions/sample.json
cp yourclip.mp4              frontend/public/videos/sample.mp4
```

That JSON holds every decision: which song, **where in the video it starts**,
and why. `lib/types.ts` is the typed mirror of it — if the backend changes the
shape, fix that file first and TypeScript will point at everything else.

Use `played.at_video_time` for anything on a timeline, not `video_time`. The
scene is usually read a few seconds before the song actually lands.

## Layout

```
app/
  page.tsx         landing — what it is        [skeleton]
  demo/page.tsx    the demo ground             [working]
components/
  MomentCard       one decision, explained     [working]
  Timeline         where each song lands       [working]
  PipelineDiagram  the six steps               [TODO]
lib/
  types.ts         the contract with the agent [done]
  session.ts       loading + which moment is live
public/
  sessions/        recorded runs
  videos/          the footage
```

## What's left

- **The diagram.** `components/PipelineDiagram.tsx` is a placeholder. The six
  steps are listed in the file. Inline SVG is probably right — scales on a
  projector, no dependency.
- **The landing page.** Skeleton. Needs the framing judges read first.
- **Drag-and-drop.** Spec says drop in a video and see the picks. Until the
  agent runs server-side, this should fall back to the sample and say so.
- **Losing candidates.** The session file records what it *considered* and
  rejected. Showing that makes the reasoning much more convincing — three
  strategies competing is more interesting than one answer appearing.

## Two things to keep

**The card order is the argument.** *It sees* → *so it wants* → *so it plays*.
That sequence is what separates this from a shuffle button. Don't reorder it to
lead with the song.

**The site survives a dead video.** Click a timeline dot and the cards still
work even if the footage doesn't load — codec support varies and a projector
laptop is not our laptop. Don't make anything depend on video playback.

## Styling

Tailwind, with the same palette as the agent's own screens (`tailwind.config.ts`)
so the site and the running product look like one thing. `scene` blue is the
world as it is; `target` orange is what we're about to do about it. That pairing
is used consistently — keep it.

## Hosting

Static. Uncomment `output: "export"` in `next.config.mjs` and `npm run build`
gives a plain folder that works on GitHub Pages, Netlify, Vercel, or a USB stick.
