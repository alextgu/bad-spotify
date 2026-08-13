# Pipeline

Anything marked **TEMPORARY** is not decided. Don't build against it without saying so in the channel.

## Stack

| Layer | Choice | Status |
|---|---|---|
| Orchestration | LangGraph | locked — `agents/graph.py` |
| Perception + judge | Gemini Flash, 2 calls per cycle | locked |
| Voice | ElevenLabs, `eleven_flash_v2_5` | locked — quips only, not narration |
| Playback | Spotify Web API (playback control only) | locked |
| Music intelligence | our own corpus + vibe space | locked |
| Twelve Labs | post-session recap, **not** the live loop | **TEMPORARY** — cut it if the recap screen doesn't get built |
| Training / fine-tuning | none | cut. Few-shot prompting + the curated corpus is the whole "training" budget |

## Capture

- Regular video input now (webcam / phone). Glasses are a later port behind `CaptureSource`.
- 1 frame / 5s, plus a rolling 3s audio window.
- **The 5s cadence is not the trigger.** A local change gate (frame diff + audio RMS + onset spike, ~1ms, no model call) decides whether a frame is worth an opinion. Your "capture when the audio spikes" instinct is in there as `onset_spike_ratio`, alongside visual change. Forced escalation after 45s so it never goes blind.

## Input analysis

One Gemini call returns all of it as one object. Not one agent per field.

| Field | Where it lands | Status |
|---|---|---|
| Mood | `valence`, `arousal` | live |
| Speed (drums/pace) | `tempo_feel` + local librosa onset rate & BPM | live |
| Consistent/inconsistent | `meter` (steady / swung / irregular) + `pulse_regularity` | live |
| Colour (synesthesia) | `dominant_colors` | live in the schema, **TEMPORARY** — captured and shown in the HUD but not yet used in selection. Needs a colour→vibe mapping or drop it |
| Instruments/sounds per genre | — | **TEMPORARY** — not implemented. Cheapest version: tags on corpus tracks, not audio analysis |
| Weather | — | **TEMPORARY** — not implemented. Would be an API call keyed on location, not perception |

Also returned: `setting`, `activity`, `social_context`, `confidence`. `confidence` gates whether the DJ acts at all.

## Agent topology

```
gate → perceive → antagonize (3-way fan-out) → judge → dj → play
```

- **Split agents by failure mode, not by output field.** Four agents for mood/speed/meter/colour would be 4× cost and 4× failure surface for data one structured call already returns.
- The fan-out is three *competing theories of wrongness*: `genre_antipode` (wrong on every axis), `tempo_clash` (wrong about energy/pulse), `lyrical_irony` (wrong in meaning). They return different shortlists on purpose. Judge picks.
- Big → 2 → many is the wrong shape here. It's a pipeline with one deliberate fan-out.

## Bounds and fallbacks

- Cooldown 8s, commitment 25s, hysteresis 2 agreeing scene reads before acting on a change. Without these it switches every 5s and reads as a shuffle button.
- Fallback ladder: vision fails → last scene; judge fails → chaos deck; Spotify fails → local mp3. **Silence is the only real bug.**
- All in `dj/controller.py`. 8 tests cover it.

## Music data

- Ship: 47 hand-curated tracks, hand-tagged vibe vectors. Curated because the joke needs *recognition* — 55k obscure tracks are worse than 47 famous ones.
- Opposites: reflection through the centre of a 5-dim vibe cube (valence, arousal, density, brightness, organicness), plus a hand-written taboo table keyed on setting keywords.
- everynoise: scraper written (`scripts/scrape_everynoise.py`) — ~6000 genres with 2D coords from the page's inline CSS. **TEMPORARY** — unverified against the live page, and nothing consumes the output yet.
- Scale-up options if we need them: MTG-Jamendo (mood/theme tags + CC audio), Deezer Mood Detection (valence/arousal). **TEMPORARY** — only if the seed corpus proves too thin.
- No music classifier. We are not analysing audio to label it; we label the corpus by hand once.

## UI

- Jarvis-style top-right cards = the reasoning trace, live over websocket. Built.
- Plus: onboarding flow, vibe-gap chart, cruelty dial, scene injection.
- **Scene injection is the demo-day button.** Type or click a situation, the real pipeline runs on it, no camera and no network luck.

## Open

- Session memory — it will repeat jokes on a long run. Not built.
- Latency — untested against real Gemini. Budget is ~2s scene→track.
- Glasses companion app — stubbed at `capture/glasses.py`.
- **TEMPORARY** — Jesse's read on the concept.
