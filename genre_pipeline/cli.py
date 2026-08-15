"""
Single runnable entry point for every stage of YOUR part of the pipeline:
    (text blurb OR explicit params) -> moment vector -> nearest genre -> opposite genre

Usage:
    python3 cli.py --blurb "a quiet, somber funeral"
    python3 cli.py --valence 0.05 --energy 0.15 --speed 0.10 --chaos 0.10
    python3 cli.py --blurb "a wild party" --show-candidates   # also prints the top-5 nearest genres, not just #1

This exists so you can sanity-check any stage without writing a throwaway
script each time -- run it directly during development, and pytest (tests/)
for regression checks once behavior is locked in.
"""

import argparse
from genre_taxonomy import GENRES
from distance import combined_distance, MATCH_AXIS_WEIGHTS, MATCH_TERM_WEIGHTS
from pipeline import build_moment, nearest_genre, opposite_genre
from sentiment import blurb_to_valence_arousal


def main():
    parser = argparse.ArgumentParser(description="Run the description->sentiment->genre pipeline stage by stage.")
    parser.add_argument("--blurb", type=str, help="Text description of the moment (goes through sentiment.py)")
    parser.add_argument("--valence", type=float, help="Override/skip sentiment extraction with an explicit value [0,1]")
    parser.add_argument("--energy", type=float, default=0.5)
    parser.add_argument("--speed", type=float, default=0.5)
    parser.add_argument("--chaos", type=float, default=0.5)
    parser.add_argument("--colour-warmth", type=float, default=0.5)
    parser.add_argument("--show-candidates", action="store_true", help="Print top-5 nearest genres, not just the winner")
    args = parser.parse_args()

    print("=" * 60)
    print("STAGE 1: mood extraction")
    print("=" * 60)
    if args.blurb:
        valence, arousal = blurb_to_valence_arousal(args.blurb)
        print(f"  blurb: {args.blurb!r}")
        print(f"  -> valence={valence:.3f} arousal={arousal:.3f}  (via sentiment.py)")
    elif args.valence is not None:
        valence, arousal = args.valence, args.energy
        print(f"  explicit override: valence={valence:.3f} arousal={arousal:.3f}")
    else:
        parser.error("Provide either --blurb or --valence")

    print()
    print("=" * 60)
    print("STAGE 2: build moment vector")
    print("=" * 60)
    moment = build_moment(
        valence=valence, arousal=arousal, speed=args.speed, chaos=args.chaos,
        colour_warmth=args.colour_warmth,
    )
    print(f"  valence={moment.valence:.3f} energy={moment.energy:.3f} speed={moment.speed:.3f} chaos={moment.chaos:.3f}")

    print()
    print("=" * 60)
    print("STAGE 3: nearest genre")
    print("=" * 60)
    matched = nearest_genre(moment)
    print(f"  MATCHED: {matched.name}  (code={matched.code})")
    print(f"    valence={matched.valence:.2f} energy={matched.energy:.2f} speed={matched.speed:.2f} chaos={matched.chaos:.2f}")

    if args.show_candidates:
        ranked = sorted(GENRES, key=lambda g: combined_distance(moment, g, axis_weights=MATCH_AXIS_WEIGHTS, **MATCH_TERM_WEIGHTS))
        print("  top 5 candidates:")
        for g in ranked[:5]:
            d = combined_distance(moment, g, axis_weights=MATCH_AXIS_WEIGHTS, **MATCH_TERM_WEIGHTS)
            print(f"    {g.name:22s} distance={d:.4f}")

    print()
    print("=" * 60)
    print("STAGE 4: opposite genre (QUEUE THIS)")
    print("=" * 60)
    worst_choice = opposite_genre(matched)
    print(f"  OPPOSITE: {worst_choice.name}  (code={worst_choice.code})")
    print(f"    valence={worst_choice.valence:.2f} energy={worst_choice.energy:.2f} speed={worst_choice.speed:.2f} chaos={worst_choice.chaos:.2f}")
    print()


if __name__ == "__main__":
    main()
