# Worst-Possible-DJ: blurb -> opposite genre pipeline

## Files
- `genre_taxonomy.py` — genre tree (p-adic taxonomy codes) + hand-anchored
  (valence, energy) profiles. **Swap this for real Essentia-aggregated
  profiles when ready** — same shape, `{genre: (valence, energy)}`.
- `distance.py` — p-adic taxonomy distance, Euclidean/Mahalanobis feature
  distance, and the combined weighted metric.
- `sentiment.py` — blurb -> (valence, arousal) via the HF emotion classifier
  (`j-hartmann/emotion-english-distilroberta-base`). Has an offline fallback
  lexicon that ONLY activates if huggingface.co is unreachable — delete
  `_FALLBACK_LEXICON` and the try/except once you've confirmed the real
  model downloads on your machine (it will — this sandbox just blocks
  huggingface.co, your machine won't).
- `pipeline.py` — wires it all together. Run `python3 pipeline.py` for a demo.

## Next steps
1. Confirm `sentiment.py` hits the real HF model locally (should just work,
   no code changes needed — the fallback only triggered here due to sandbox
   network restrictions).
2. Swap `genre_taxonomy.py`'s hand-anchored (valence, energy) pairs for
   Essentia-aggregated values once you've got a per-genre track corpus.
3. Tune `alpha`/`beta` in `combined_distance` — currently 0.5/0.5, i.e.
   taxonomy distance and acoustic distance weighted equally.
4. Wire `pipeline.run()`'s `worst_choice.name` into your Spotify queue call.
