# Adding your part

For anyone — person or agent — plugging work into this repo.

`AGENTS.md` has the rules. `PIPELINE.md` explains how it works. **This file is
about how to attach your piece without breaking anyone else's.**

---

## 1. Find your seam

There are five, and they're deliberately narrow. Work inside one and nothing
else needs to know you exist.

| You're building | Your seam | Contract |
|---|---|---|
| Anything that turns the world into a description | `perceive/scene.py` → `build_perceiver(cfg)` | returns an object with `.read(frame, audio_features, meta) -> SceneRead` |
| A new theory of what makes music wrong | `music/strategies.py` → `REGISTRY` | `fn(scene, anti, corpus, exclude, n) -> list[Candidate]` |
| A new way to pick the winner | `agents/judge.py` → `build_judge(cfg)` | returns an object with `.judge(scene, anti, candidates) -> Verdict` |
| A new way to get sound out | `players/base.py` → `build_player(cfg)` | `.play(track, mode)`, `.stop()`, `.set_volume(level)` |
| A new source of frames | `capture/base.py` → `build_capture(cfg)` | `.open()`, `.close()`, `.stream() -> Iterator[Observation]` |

Every one of these already has a **mock** implementation. Read the mock first —
it is the shortest correct answer to "what shape must I return".

---

## 2. The two contracts that actually matter

Everything else is internal. These two cross boundaries, so changing them
breaks other people.

### `SceneRead` — what the world looks like

Defined in `src/badspotify/schemas.py`. Produced by perception, consumed by
everything downstream.

| Field | Why anyone else cares |
|---|---|
| `setting`, `activity` | **The specificity lives here.** "toddler's birthday party, cake being cut" produces a joke; "indoor event" produces nothing. If your approach can't produce this, it isn't good enough, however clever it is. |
| `vibe` — 5 floats, 0–1 | Gets flipped to find the opposite. Must actually span the range; if everything comes back near 0.5 the inversion is meaningless. |
| `confidence` | Below 0.35 the system does nothing. **Be honest here.** Overconfidence on a blurry frame is worse than admitting you don't know. |
| `mood_label`, `tempo_feel`, `meter` | Feed the strategies. |

### The session file — what the site replays

Written by `session.py`, read by `frontend/lib/types.ts`. If you change the
shape, change both, in the same commit.

The one that bites: use **`played.at_video_time`** for anything on a timeline,
not `video_time`. The scene is usually read a few seconds before the song
actually lands.

---

## 3. Before you say you're done

```bash
pytest tests/ -q                      # 79 tests. All of them, not just yours.
python run.py --ticks 6 --no-hud      # the loop still runs on mocks
python scripts/io/describe.py --text "a sunlit park" \
  | python scripts/io/invert.py | python scripts/io/choose.py
```

Then update `STATUS.md` — your row, and **how you proved it**. "Works" is not a
proof. "Ran it against 5 real photos, descriptions matched, confidence dropped
on the blurry one" is.

---

## 4. Traps in this specific repo

Every one of these has already cost someone hours here. They are not
hypothetical.

**LangGraph silently drops state keys you didn't declare.** If you add
something to the pipeline state, add it to the `PipelineState` TypedDict in
`agents/graph.py` too. Otherwise it vanishes between nodes with no error — a
`force` flag was being set and discarded for exactly this reason, and the
symptom was "the button does nothing sometimes".

**stdout is reserved for data.** The scripts in `scripts/io/` pipe JSON to each
other. Never `print()` in library code — use `from ..log import notice`. A
single stray line of status output corrupts the stream and the next script dies
on a parse error.

**Don't add `from __future__ import annotations` to `hud/server.py`.** FastAPI
resolves handler annotations against module globals, and `WebSocket` is
imported lazily inside the function. Under postponed annotations it isn't
found, FastAPI treats the parameter as an unknown query field, and the browser
gets a bare HTTP 403 with nothing in the server log. There's a comment there
saying so; leave it.

**The mocks are not dead code.** Every backend has one, and to a cleanup pass
they look like cruft. They are why someone can clone this with no API keys and
still run the whole pipeline. Deleting them blocks the whole team.

**Cheap checks can starve the thing that depends on them.** The change gate
suppresses repeated reads to save model calls; the DJ needs two agreeing reads
before it acts. Together they deadlocked on calm footage — nothing ever played.
A quiet tick now counts as positive evidence that the scene is *stable*. If you
add another optimisation that skips work, ask what downstream was counting on
that work happening.

**There is no dial for how wrong to be.** `Verdict.mismatch` is measured after
the fact, never set. Don't add a parameter for it — that was removed on purpose
and there's a test asserting its absence.

---

## 5. Worked example: adding a fourth theory of wrongness

The whole change is one function and one line.

```python
# src/badspotify/music/strategies.py

def era_clash(scene, anti, corpus, exclude, n):
    """Wrong in TIME. A 1950s crooner at a rave is not sonically opposite --
    it's from the wrong century, and that reads as funnier than distance."""
    scored = []
    for t in corpus.filter(exclude, anti.banned_genres):
        # ... your scoring ...
        scored.append(Candidate(track=t, strategy="era_clash",
                                raw_distance=score, notes="why this one"))
    scored.sort(key=lambda c: c.raw_distance, reverse=True)
    return scored[:n]


REGISTRY["era_clash"] = era_clash
```

Then add `era_clash` to `antagonize.strategies` in `config.yaml`, and check it:

```bash
python scripts/io/describe.py --text "a rave at 2am" \
  | python scripts/io/choose.py --show-all
```

`--show-all` prints every candidate with the strategy that proposed it, so you
can see whether yours is contributing anything the others weren't.

**A new strategy earns its place by disagreeing.** If it keeps proposing what
`genre_antipode` already proposed, it's costing time and adding nothing. Three
strategies that argue beat five that agree.

---

## 6. What to optimise for when you're unsure

Two things, in this order:

1. **The judges have to recognise the song.** An obscure track that is
   technically the perfect opposite is a worse pick than a famous one that is
   merely very wrong.
2. **The reasoning has to stay visible.** Seeing *why* it chose funeral doom is
   the difference between an agent and a shuffle button, and it's most of why
   the technical work reads as serious.

If a change helps one of those, it's probably right. If it quietly costs one of
them to gain something else, say so out loud rather than deciding alone.
