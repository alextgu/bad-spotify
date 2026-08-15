#!/usr/bin/env python3
"""bad spotify — the hosted face of the agent.

    python app.py                       # http://127.0.0.1:7860
    python app.py --share               # public link (Gradio tunnel)
    python app.py --port 7861 --play    # let it actually control Spotify

This is the *hosting* half of the project. The site in `frontend/` explains the
idea and replays recorded runs; this runs the real agent live, from a browser,
with no terminal.

Three ways in, deliberately in this order:

  1. Describe a scene   — text → active perception → the whole pipeline. It
                          falls back offline when the model is unavailable.
  2. A photo            — one frame → one decision. Same call a Ray-Ban
                          companion app would make (`Engine.look`).
  3. A video            — sampled on a cadence *and* on cuts and bangs
                          (`videofeed`), then a decision per sampled moment.
                          Exports the exact session JSON the site replays.

Everything runs on mocks unless keys are present, so a fresh clone with no
credentials still demonstrates the whole thing. `--play` is opt-in for a
reason: a hosted page that hijacks the host machine's speakers is a bad
surprise, and the project's own decision was to *name* songs rather than play
them at an audience.

The scaffold for the glasses is the same `Engine`: a companion app that posts
frames calls `Engine.look(frame, audio)` and gets back the same Decision this
page renders. Nothing above that call changes when the hardware arrives.
"""
from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

import gradio as gr                                    # noqa: E402

from badspotify.service import FROM_CONFIG, Decision, Engine   # noqa: E402
from videofeed import BUILTIN_TRIGGERS                 # noqa: E402

ENGINE: Engine | None = None

EXAMPLE_SCENES = [
    "inside a McDonald's fast food restaurant during lunch rush",
    "a sunlit park, people reading on the grass",
    "a hospital waiting room at 3am",
    "a toddler's birthday party, cake being cut",
    "a silent library during exam week",
    "an empty parking garage at night",
    "a first date at a candlelit restaurant",
]

TRIGGER_CHOICES = sorted(BUILTIN_TRIGGERS)


def engine() -> Engine:
    """One engine for the whole process. Building it loads the corpus."""
    global ENGINE
    if ENGINE is None:
        ENGINE = Engine()
    return ENGINE


# ---------------------------------------------------------------- rendering --


def decision_markdown(d: Decision) -> str:
    """The decision, in the order that makes it an argument rather than a shuffle.

    Sees → wants → plays → why. Keep that order: it is the whole difference
    between this and a random button, and it's what people read on stage.
    """
    if not d.chosen:
        return f"### Nothing played\n\n`{d.reason}`"

    colors = " ".join(f"`{c}`" for c in (d.scene.get("colors") or [])[:4])
    confidence = d.scene.get("confidence")
    considered = "\n".join(
        f"- **{name}** — " + ", ".join(f"{p['title']}" for p in picks)
        for name, picks in (d.considered or {}).items()
    )
    cut = "cut in" if d.mode == "interrupt" else "queued"

    return f"""### {d.chosen['title']} — {d.chosen['artist']}

> “{d.chosen.get('quip') or ''}”

**It sees** {d.scene.get('setting')}
{d.scene.get('mood')}{f" · {round(confidence * 100)}% sure" if confidence else ""} · {d.scene.get('tempo')} · {colors}

**Setting traits** {', '.join(d.scene.get('setting_attributes') or []) or '(none inferred)'}

**Flipped traits** {', '.join(d.opposite.get('attributes') or []) or '(none inferred)'}

**So it wants** {', '.join((d.opposite.get('looking_for') or [])[:6])}

**So it plays** {d.chosen['title']}, {cut} — via `{d.chosen.get('strategy')}`
mismatch {d.chosen.get('mismatch')} · {d.chosen.get('why')}

**It also considered**
{considered or '- (nothing else scored)'}

<sub>{d.latency_ms} ms · perception: {d.scene.get('source')} · judge: {d.chosen.get('source')}</sub>
"""


def backends_markdown() -> str:
    b = engine().backends()
    rows = "\n".join(f"| {k} | `{v}` |" for k, v in b.items())
    mocked = [k for k, v in b.items() if v == "mock"]
    note = (f"\n\n**{len(mocked)} of these are stand-ins** "
            f"({', '.join(mocked)}). Set the matching key in `.env` and flip the "
            f"backend in `config.yaml` to use the real thing. Nothing here "
            f"crashes when a key is missing — it degrades."
            if mocked else "\n\nEverything is live.")
    return f"| part | backend |\n|---|---|\n{rows}{note}"


# ----------------------------------------------------------------- handlers --


def on_describe(text: str):
    if not (text or "").strip():
        return "Type a situation first — or click one of the examples.", {}
    eng = engine()
    d = eng.describe(text)
    return decision_markdown(d), d.to_dict()


def on_photo(image):
    """One frame in. The same call the glasses companion app will make."""
    if image is None:
        return "Upload a photo, or take one with the camera.", {}
    eng = engine()

    # Gradio hands over RGB; everything downstream is OpenCV's BGR.
    frame = image[:, :, ::-1].copy() if getattr(image, "ndim", 0) == 3 else image
    d = eng.look(frame, meta={"source": "photo"})
    return decision_markdown(d), d.to_dict()


def on_video(video_path, interval, triggers, max_segments,
             progress=gr.Progress()):
    """Walk a clip and decide about every sampled moment.

    Yields as it goes: on a long clip, watching the decisions arrive is the
    demo. The session file it writes is the same one `--record` produces, so it
    drops straight into `frontend/public/sessions/`.
    """
    if not video_path:
        yield "Upload a clip first.", None, None
        return

    eng = engine()
    eng.reset()

    rows: list[list] = []
    name = Path(video_path).stem or "session"

    progress(0, desc="sampling")
    for d in eng.watch_iter(
        video_path,
        interval_s=float(interval),
        triggers=list(triggers or []),
        max_segments=int(max_segments) if max_segments else None,
        name=name,
    ):
        rows.append([
            f"{int((d.video_time or 0) // 60):02d}:{int((d.video_time or 0) % 60):02d}",
            "+".join(d.reasons) or "interval",
            d.scene.get("setting") or "",
            d.chosen.get("title") or "—",
            d.chosen.get("artist") or "",
            "cut in" if d.mode == "interrupt" else "queued",
            d.chosen.get("strategy") or "",
        ])
        yield f"{len(rows)} decisions so far…", rows, None

    session = eng.last_session or {}
    out = Path(tempfile.gettempdir()) / f"{name}.json"
    out.write_text(json.dumps(session, indent=2))

    triggered = sum(1 for r in rows if r[1] != "interval")
    yield (f"**{len(rows)} decisions** — {triggered} sampled because something "
           f"happened, the rest on the {interval:g}s cadence. "
           f"Download the session below and drop it into "
           f"`frontend/public/sessions/` to replay it on the site.",
           rows, str(out))


# --------------------------------------------------------------------- ui --


def build_ui() -> gr.Blocks:
    # Gradio 6 moved `theme` from the Blocks constructor to launch().
    with gr.Blocks(title="bad spotify") as demo:
        gr.Markdown(
            "# bad spotify\n"
            "**An agent that reads the room and plays the worst possible thing "
            "for it.** It will not take requests.\n\n"
            "Nothing plays out loud here — it names the song and shows its "
            "reasoning, which is the part worth looking at."
        )

        # 1 --------------------------------------------------------------
        with gr.Tab("Describe a scene"):
            gr.Markdown(
                "Type a situation. Active perception infers its semantics; "
                "the offline fallback keeps the pipeline available."
            )
            with gr.Row():
                scene_in = gr.Textbox(
                    label="the situation",
                    placeholder="a hospital waiting room at 3am",
                    scale=4,
                )
                scene_go = gr.Button("Ruin it", variant="primary", scale=1)
            gr.Examples(EXAMPLE_SCENES, inputs=scene_in, label="or try one of these")
            scene_out = gr.Markdown()
            with gr.Accordion("the full decision, as JSON", open=False):
                scene_json = gr.JSON()

            scene_go.click(on_describe, [scene_in], [scene_out, scene_json])
            scene_in.submit(on_describe, [scene_in], [scene_out, scene_json])

        # 2 --------------------------------------------------------------
        with gr.Tab("A photo"):
            gr.Markdown(
                "One frame in, one decision out. This is exactly the call a "
                "Ray-Ban companion app makes — `Engine.look(frame, audio)` — "
                "so the glasses version is this tab with the camera somewhere "
                "else.\n\n"
                "*With perception on `mock` the scene read is canned, so every "
                "photo gives the same answer. Set `GOOGLE_API_KEY` and flip "
                "`perceive.backend` to `gemini` for it to actually look.*"
            )
            with gr.Row():
                photo_in = gr.Image(sources=["upload", "webcam", "clipboard"],
                                    type="numpy", label="a moment")
                with gr.Column():
                    photo_go = gr.Button("Ruin it", variant="primary")
                    photo_out = gr.Markdown()
            with gr.Accordion("the full decision, as JSON", open=False):
                photo_json = gr.JSON()

            photo_go.click(on_photo, [photo_in], [photo_out, photo_json])

        # 3 --------------------------------------------------------------
        with gr.Tab("A video"):
            gr.Markdown(
                "Feed it a recording as though it were live. Frames are sampled "
                "on a fixed cadence **and** whenever something happens — a cut, "
                "a bang, movement — so a decision can land on the moment rather "
                "than on the next tick.\n\n"
                "What comes out is the same session file `run.py --record` "
                "writes, so it replays on the site with no backend."
            )
            with gr.Row():
                #"webcam" records straight from the camera, which is the
                #closest thing in this app to the live loop: a sequence of
                #decisions over time rather than the photo tab's single frame.
                #Screen recordings work here too -- upload the mp4.
                video_in = gr.Video(label="a clip", sources=["upload", "webcam"])
                with gr.Column():
                    interval = gr.Slider(0, 15, value=5, step=1,
                                         label="cadence (seconds, 0 = triggers only)")
                    triggers = gr.CheckboxGroup(
                        TRIGGER_CHOICES,
                        value=["scene-cut", "audio-onset"],
                        label="also sample when…",
                    )
                    max_segments = gr.Number(value=30, precision=0,
                                             label="stop after N decisions (0 = no limit)")
                    video_go = gr.Button("Watch it", variant="primary")

            video_status = gr.Markdown()
            video_table = gr.Dataframe(
                headers=["at", "why sampled", "it sees", "song", "artist",
                         "queued/cut", "strategy"],
                label="decisions",
                wrap=True,
            )
            video_file = gr.File(label="session JSON — drop into frontend/public/sessions/")

            video_go.click(
                on_video,
                [video_in, interval, triggers, max_segments],
                [video_status, video_table, video_file],
            )

        # 4 --------------------------------------------------------------
        with gr.Tab("What's actually running"):
            gr.Markdown("### Backends")
            backends = gr.Markdown(backends_markdown())
            refresh = gr.Button("re-check")
            refresh.click(lambda: backends_markdown(), None, backends)
            gr.Markdown(
                "### On the glasses\n"
                "The whole agent is hardware-agnostic above the capture layer. "
                "A Ray-Ban companion app owns the SDK session and posts frames; "
                "everything it needs is `Engine.look(frame, audio)`, which is "
                "the same call the photo tab makes. Nothing else changes.\n\n"
                "### On honesty\n"
                "Anything on `mock` above is a stand-in, and the page says so "
                "rather than pretending. The one unacceptable failure in this "
                "project is silence, so every backend degrades to a stand-in "
                "instead of crashing — see `STATUS.md`."
            )

    return demo


def main() -> int:
    ap = argparse.ArgumentParser(description="host the agent in a browser")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=7860)
    ap.add_argument("--share", action="store_true",
                    help="public Gradio tunnel — fine for a demo, not for keys")
    ap.add_argument("--play", action="store_true",
                    help="let the agent actually drive the player backend in "
                         "config.yaml (Spotify). Off by default: a hosted page "
                         "should not seize the host machine's speakers")
    args = ap.parse_args()

    global ENGINE
    #`--play` is the "in so many words" that Engine asks for. Passing None
    #here used to mean the same thing, but None is also what every casual
    #caller passes, so it now means mock.
    ENGINE = Engine(player=FROM_CONFIG if args.play else "mock")
    print("[app] backends: " +
          "  ".join(f"{k}={v}" for k, v in ENGINE.backends().items()))

    build_ui().launch(server_name=args.host, server_port=args.port,
                      share=args.share, theme=gr.themes.Base())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
