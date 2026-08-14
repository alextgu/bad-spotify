# One script per feature

Each script does **one step**, reads JSON in, writes JSON out. They pipe
together, and they each run alone. That means two people can work on two steps
at the same time without running each other's code, and you can swap how a step
works without anything else noticing.

```bash
python scripts/io/describe.py --image park.jpg \
  | python scripts/io/invert.py \
  | python scripts/io/choose.py \
  | python scripts/io/play.py
```

**stdout is the answer. stderr is the commentary.** Every script prints its
progress to stderr, so the pipe only ever carries data. Add `2>/dev/null` to
silence the chatter, or drop it to watch it think.

---

## The steps

| Script | In | Out |
|---|---|---|
| `gate.py` | two images | should we bother thinking? |
| `describe.py` | an image (+ audio), or `--text` | a description of the moment |
| `invert.py` | a description | the opposite, and which genres to hunt in |
| `choose.py` | the opposite | one specific song, and the line it says |
| `play.py` | a song | it comes out of a speaker |

### Try it without anything installed

```bash
# no camera, no API keys, no Spotify -- everything falls back to a mock
python scripts/io/describe.py --text "a toddler's birthday party" \
  | python scripts/io/invert.py | python scripts/io/choose.py
```

### Useful flags

```bash
python scripts/io/choose.py --show-all          # the whole shortlist, and why
python scripts/io/describe.py --backend gemini  # override config.yaml
python scripts/io/play.py --track sandstorm --backend spotify
python scripts/io/gate.py --before a.jpg --after b.jpg
```

---

## Where to plug your work in

**`describe.py` is the swappable one.** Everything downstream only cares about
the *shape* of what it returns, not how it got there. If you want to try a
HuggingFace model, or split audio and video into two separate models, this is
the only file that changes — and you can compare approaches by diffing the JSON
against the current one on the same input.

The shape it must return is `SceneRead` in `src/badspotify/schemas.py`. The
fields that matter downstream:

| Field | Why it matters |
|---|---|
| `setting`, `activity` | **The specificity lives here.** "toddler's birthday party, cake being cut" produces a much better joke than "indoor event". Don't lose this. |
| `vibe` (5 scores, 0–1) | What gets flipped to find the opposite. |
| `confidence` | If this is low, the system does nothing. Be honest or it acts on nonsense. |
| `mood_label`, `tempo_feel`, `meter` | Feed the strategies. |

**`invert.py` owns the sentiment→genre mapping.** The hand-written table of
what's tasteless where is `TABOO_RULES` in `src/badspotify/music/vibe.py`. Adding
a rule is three lines and it's the highest-leverage edit in the repo.

**`choose.py` owns the strategies.** Adding a fourth theory of wrongness means
one function in `src/badspotify/music/strategies.py` plus a line in `REGISTRY`.

---

## A note on comparing approaches

Because every step is a script with a fixed input and output, you don't have to
argue about which perception approach is better — run both on the same image and
look at the two JSON files side by side.

```bash
python scripts/io/describe.py --image test.jpg --backend gemini > a.json
python scripts/io/describe.py --image test.jpg --backend mock  > b.json
diff <(jq -S . a.json) <(jq -S . b.json)
```

The question to ask of any new approach: **does it still produce a specific
`setting`?** A sentiment score of "positive 0.87" is easy to get and produces a
generic opposite. "A christening, mid-ceremony" is harder to get and produces a
joke. That difference is most of the project.
