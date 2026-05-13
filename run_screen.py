from __future__ import annotations

import argparse
from pathlib import Path

from fusion_material_ai import screen_candidates, write_outputs


def main() -> None:
    parser = argparse.ArgumentParser(description="Screen fusion-relevant refractory alloy candidates.")
    parser.add_argument(
        "--prompt",
        default=(
            "W-rich low activation ductile BCC alloy for plasma-facing fusion reactor components; "
            "prefer W Ti V Zr Ta Nb; density < 15"
        ),
        help="Natural-language screening request.",
    )
    parser.add_argument("--samples", type=int, default=2500, help="Number of accepted candidate compositions to retain.")
    parser.add_argument("--top", type=int, default=25, help="Number of top candidates to report.")
    parser.add_argument("--seed", type=int, default=42, help="Deterministic random seed.")
    parser.add_argument("--out", default="outputs", help="Output directory.")
    args = parser.parse_args()

    result = screen_candidates(args.prompt, samples=args.samples, top_n=args.top, seed=args.seed)
    paths = write_outputs(result, Path(args.out))

    print(f"Generated candidates: {result['generated_count']}")
    for index, candidate in enumerate(result["top"][: min(args.top, 10)], start=1):
        risks = "; ".join(candidate["risk_flags"]) if candidate["risk_flags"] else "no major flags"
        print(
            f"{index:02d}. {candidate['formula']} | score={candidate['rank_score']:.2f} "
            f"| uncertainty={candidate['uncertainty']:.2f} | {candidate['recommendation']} | {risks}"
        )
    print(f"CSV: {paths['csv']}")
    print(f"Report: {paths['markdown']}")
    print(f"JSON: {paths['json']}")


if __name__ == "__main__":
    main()
