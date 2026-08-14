# Prompt for a teammate's agent

Paste everything below the line into Claude Code (or whatever you're using),
from the repo root, before you start your part.

---

I'm adding a piece to this repo. Before writing any code:

1. Read `INTEGRATION.md` — it lists the five seams, the two contracts that
   cross boundaries, and six traps that have already cost people hours here.
2. Read `AGENTS.md` — the rules. The governing one: every claim you make must
   be verifiable by a command you can quote.
3. Read `STATUS.md` — what's actually finished versus only built.

Then tell me, before you change anything:

- **Which seam am I working in?** One of the five in `INTEGRATION.md`. If my
  work doesn't fit one, say so — that's a design conversation, not a coding one.
- **What contract must I honour?** Quote the type or function signature.
- **What could I break?** Name the specific thing downstream that depends on me.

## While you work

- **Everything must still run with no API keys.** Every backend has a mock. If
  mine doesn't, build one first — a teammate has to be able to clone this and
  run the whole pipeline with nothing configured.
- **Never `print()` in library code.** Use `from ..log import notice`. stdout
  carries JSON between the scripts in `scripts/io/`, and one stray line of
  status output breaks the chain.
- **If you add anything to the pipeline state**, declare it on the
  `PipelineState` TypedDict in `agents/graph.py`. LangGraph silently discards
  keys that aren't declared — no error, the value just vanishes between nodes.
- **Never let it go silent.** The one unacceptable failure is no music. If you
  touch anything in the decision or playback path, confirm the fallback still
  fires.
- **Ask before deleting.** Move to `_review/` instead. Several things that look
  like dead code are load-bearing — the mocks especially.

## Before you tell me you're done

Run these and show me the output:

```bash
pytest tests/ -q                      # all of them, not just yours
python run.py --ticks 6 --no-hud      # the loop still runs on mocks
python scripts/io/describe.py --text "a sunlit park" \
  | python scripts/io/invert.py | python scripts/io/choose.py
```

Then update the docs **in the same commit as the code**:

- **`STATUS.md`** — your row, and *how you proved it*. "Works" is not a proof.
  "Ran it on 5 real photos, descriptions matched, confidence dropped on the
  blurry one" is a proof. If it only runs on mocks, it is **Built, unproven** —
  say so honestly, that's what the state is for.
- **`PIPELINE.md`** — only if the *behaviour* changed. This file explains how
  the thing works in plain language, with no code and no status. If someone
  reading it would now be misled, fix it. If nothing about how it works changed,
  leave it alone.
- **`INTEGRATION.md`** — if you hit a trap that isn't listed there yet, add it.
  That section is the most valuable part of the file and it only grows from
  people getting caught.

Do not update `README.md` unless you added a new command or a new folder.

## Two things to protect

If you're choosing between options, pick the one that protects these:

1. **The judges have to recognise the song.** An obscure track that's
   technically the perfect opposite is a worse pick than a famous one that's
   merely very wrong.
2. **The reasoning has to stay visible on screen.** Seeing *why* it chose
   funeral doom is the difference between an agent and a shuffle button.

If your change quietly costs one of these to gain something else, say so out
loud rather than deciding alone.
