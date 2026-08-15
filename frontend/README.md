# Slopify — presentation site

## Analyze an uploaded video

Start the Python API with `python run.py --serve`. Then run this frontend with
`npm run dev` and open `/demo`. The page posts the selected video to
`http://127.0.0.1:8420/api/analyze-video` and displays the returned session.

Set `NEXT_PUBLIC_BADSPOTIFY_API_URL` when the API uses another host or port.
Three bundled videos and their footage-derived sessions remain available
through the `Use sample` button.

The site judges look at. **Not a product**: it does not run the agent, it
replays a recording of the agent. That's deliberate — no backend to host, no
API keys in a browser, and nothing that can fail live.

```bash
npm install
npm run dev          # http://localhost:3000
```

The launch-page photo and film slots are mapped at runtime in
`public/media.json`. Local photos live in `public/images/`; the current park
and library examples use `forest.jpg` and `library.jpg` there.

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
  page.tsx         the launch page             [working]
  demo/page.tsx    the demo ground             [working]
components/
  LogoMark         animated pink-and-purple mark [working]
  BlurFade         fade-and-unblur on scroll
  MomentCard       one decision, explained     [working]
  Timeline         where each song lands       [working]
  PipelineDiagram  the six steps               [working]
lib/
  brand.ts         name, tagline, all copy     ← RENAME HERE
  types.ts         the contract with the agent [done]
  session.ts       loading + which moment is live
public/
  sessions/        recorded runs
  videos/          the footage
```

## The name

**Slopify**, settled 15 Aug. `lib/brand.ts` holds it, along with the tagline
and the positioning line. **Change `brand.name` there and it updates the
wordmark, the page title, the metadata, and the footer.** Don't hardcode it
anywhere else.

The hero names Spotify once, as a comparison. That is nominative use and it has
to stay that way — no Spotify mark, no Spotify green, nothing implying
affiliation or endorsement.

## The look

**Not described anywhere, on purpose.** It is being restarted, and every
document that specified the previous one has been removed so a new direction
isn't arguing with a specification nobody chose any more.

The one thing to preserve is the **section ordering**, and it lives in
`app/page.tsx` — the imports and the comment above them, in order. That's the
wireframe. Everything else about how the page looks is open.

## What's left

- **The landing page.** Skeleton. Needs the framing judges read first.
- **Drag-and-drop.** Spec says drop in a video and see the picks. Until the
  agent runs server-side, this should fall back to the sample and say so.
- **Losing candidates.** The session file records what it *considered* and
  rejected. Showing that makes the reasoning much more convincing — three
  competing strategies are more interesting than one answer appearing.

## Two things to keep

**The card order is the argument.** *It sees* → *so it wants* → *so it plays*.
That sequence is what separates this from a shuffle button. Don't reorder it to
lead with the song.

**The site survives a dead video.** Click a timeline dot and the cards still
work even if the footage doesn't load — codec support varies and a projector
laptop is not our laptop. Don't make anything depend on video playback.

## Hosting

Static. Uncomment `output: "export"` in `next.config.mjs` and `npm run build`
gives a plain folder that works on GitHub Pages, Netlify, Vercel, or a USB stick.
