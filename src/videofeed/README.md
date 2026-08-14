# videofeed

**A video goes in. Model-ready segments come out.**

Samples a clip on a fixed cadence *and* whenever something happens — a cut, a
bang, the lights changing — and attaches the audio around each sample. Then it
hands each one to whatever you plug in.

There is **no model in here**, on purpose. `handoff.py` is the agreed shape of
the next step so that the model can be written independently of the sampler.

Nothing in this package imports anything else in this repo. Copy the folder into
another project and it works.

---

## Why not just sample every 5 seconds?

Because a fixed cadence is either too slow or too expensive, and usually both.
Slow enough to be cheap, and you miss the moment someone walks into frame. Fast
enough to catch that, and you're paying for a model call every second of
footage where nothing happened.

So this does both. It walks the video taking cheap **probes** several times a
second — a 32×32 greyscale thumbnail plus the recent audio — and turns a probe
into a **segment** when either the cadence is due or a trigger fires.

Probes cost microseconds. Segments cost whatever your model costs.

---

## Quick start

```python
from videofeed import VideoFeed, SceneCut, AudioOnset

feed = VideoFeed("clip.mp4", interval_s=5.0,
                 triggers=[SceneCut(), AudioOnset()])

with feed:
    for seg in feed.segments():
        print(seg)          # Segment(#3 t=12.50s reasons=scene_cut frame=y audio=y)
        seg.frame           # HxWx3 uint8 BGR (OpenCV order)
        seg.audio           # mono float32, the 3s ending at seg.t
        seg.reasons         # ["interval"] or ["scene_cut", "audio_onset"]
        # hand it to a model here
```

From a shell, no Python needed:

```bash
PYTHONPATH=src python -m videofeed clip.mp4                       # print what it samples
PYTHONPATH=src python -m videofeed clip.mp4 --interval 3 --out runs/demo1
PYTHONPATH=src python -m videofeed clip.mp4 --triggers scene-cut,audio-onset,motion-spike
PYTHONPATH=src python -m videofeed 0 --interval 2 --no-audio      # webcam, vision-only
```

`PYTHONPATH=src` because this repo runs from `src/` without being installed —
same reason `run.py` does `sys.path.insert(0, "src")`.

Run it with no `--out` first. One line per segment tells you whether the
sampling is right, before anyone spends a token finding out it wasn't.

---

## What comes out

```
Segment
  index          0-based, in emission order
  t              seconds into the video          <- what downstream cares about
  reasons        ["interval"] | ["scene_cut", ...] | both
  triggered      True if anything but the cadence caused it
  frame          HxWx3 uint8 BGR, or None
  audio          mono float32 in [-1, 1], the window ENDING at t, or None
  sample_rate    16000 by default
  source         file name
  duration_s     length of the whole clip
  meta           yours; nothing in this package reads it
```

Handy methods: `seg.frame_jpeg()` for bytes to post to an API,
`seg.save_frame(path)` / `seg.save_audio(path)` for disk, `seg.to_dict()` for
JSON (arrays are described, not embedded).

The audio window **ends** at `t` — it is what was just heard, not what happens
next. That matters: a model asked "what is happening here?" should not be given
three seconds of the future.

---

## Triggers

| name | fires when |
|---|---|
| `scene-cut` | the picture changed a lot since the last probe |
| `motion-spike` | movement well above *this clip's* own baseline |
| `audio-onset` | suddenly louder than this clip has been |
| `audio-drop` | it went quiet |
| `brightness-shift` | the light level moved (indoors→outdoors, lights down) |

The audio ones compare against a rolling median rather than a fixed threshold,
so they work in a library and in a bar without retuning.

Write your own — the contract is `name` and `check(probe) -> bool`:

```python
from videofeed import FunctionTrigger

feed = VideoFeed("clip.mp4", triggers=[
    FunctionTrigger("someone_shouted", lambda p: p.rms > 0.3),
    FunctionTrigger("went_dark",       lambda p: p.brightness < 0.05),
])
```

A probe gives you `t`, `index`, `dt`, `gray` (32×32 float 0..1), `frame`,
`audio`, `rms` and `brightness`. Triggers run on every probe, so keep them
cheap — anything that costs a model call belongs downstream.

Triggers hold state (most compare against what they saw last), so one instance
belongs to one feed. A trigger that raises is logged and ignored; it never takes
the run down.

### Tuning

- `min_trigger_gap_s` (default 1.5) — one event fires several probes in a row;
  this stops you getting nine near-identical frames of the same door opening.
- `probe_fps` (default 4) — how responsive triggers are, against CPU.
- `audio_window_s` (default 3) — shorter makes `audio-onset` snappier, because
  a long window dilutes a short sound into its own context.
- `interval_s=0` — triggers only, no cadence.

---

## Plugging a model in

The contract is one method:

```python
class MyModel:
    name = "my-model"

    def handle(self, segment):
        jpeg = segment.frame_jpeg()
        ...                                  # call whatever you like
        return {"caption": "a dog, mid-air"} # or None

    def close(self):
        pass
```

Then:

```python
from videofeed import VideoFeed, SceneCut, DirectorySink, run

run(VideoFeed("clip.mp4", triggers=[SceneCut()]),
    [DirectorySink("runs/demo1"), MyModel()])
```

`run()` never lets one handler's failure kill the walk — a model that
rate-limits or a disk that fills up costs you that segment, not the session.

Two handlers ship, and both are useful before any model exists:

- **`NullHandoff`** — prints one line per segment. Checks the *sampler*
  independently of the model.
- **`DirectorySink`** — writes `0000.jpg`, `0000.wav` and an append-only
  `manifest.jsonl` (one segment per line, flushed as it goes, so a run that dies
  halfway still leaves a usable record).

---

## Using it as this repo's capture source

`badspotify` has its own `capture/video.py` that predates this and samples on a
fixed interval only. To drive the agent off this instead, adapt a segment into
an `Observation` — no changes needed on either side:

```python
from badspotify.capture.base import Observation
from videofeed import VideoFeed, SceneCut, AudioOnset

def observations(path):
    feed = VideoFeed(path, interval_s=5.0, triggers=[SceneCut(), AudioOnset()])
    with feed:
        for seg in feed.segments():
            yield Observation(
                frame=seg.frame, audio=seg.audio, sample_rate=seg.sample_rate,
                meta={"source": "videofeed", "video_time": seg.t,
                      "duration": seg.duration_s, "index": seg.index,
                      "reasons": seg.reasons},
            )
```

Note the agent's own `ChangeGate` runs *after* sampling, so it can only react as
fast as the sampler does — which is exactly the gap the triggers here close.

---

## Requirements

`opencv-python` and `numpy` (already in `requirements.txt`). `ffmpeg` on PATH for
audio; without it you get vision-only segments rather than an exception.

Decoding is sequential, never seeking — seeking by timestamp lands on the
nearest keyframe on a lot of real files, which can be seconds off. Frames that
aren't probe points are skipped with `grab()`, so the walk is cheap.

## Tests

```bash
pytest tests/test_videofeed.py -q     # 17 tests
```

They build a real mp4 and walk it. The failures worth catching — a trigger that
fires on every probe, an audio window off by a second, a codec that won't seek —
only show up against a real file.
