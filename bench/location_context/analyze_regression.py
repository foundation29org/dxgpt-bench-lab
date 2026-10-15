"""Paired comparison of the regression arms scored by evaluate_v4.py.

Reads ``outputs/regression/<arm>/evaluation_v4_primary_strict/evaluation_details.txt``
for every arm and prints R@1/R@3/R@5 per arm plus, for each arm against the
baseline, the discordant cases and an exact two-sided McNemar p-value.

    py bench\\location_context\\analyze_regression.py
    py bench\\location_context\\analyze_regression.py --arms none IN NG --baseline none
    py bench\\location_context\\analyze_regression.py --baseline none --arms none=<dir> ES=<dir>

A `label=<dir>` arm points at any folder holding `evaluation_v4_primary_strict/`.
"""

from __future__ import annotations

import argparse
import json
from math import comb
from pathlib import Path

OUTPUTS = Path(__file__).resolve().parent / "outputs" / "regression"
DETAILS = "evaluation_v4_primary_strict/evaluation_details.txt"
CUTOFFS = (1, 3, 5)


def split_arm(arm: str) -> tuple[str, Path]:
    """`IN` -> (IN, outputs/regression/IN); `label=some\\dir` -> (label, some\\dir)."""
    label, separator, folder = arm.partition("=")
    return (label, Path(folder)) if separator else (arm, OUTPUTS / arm)


def read_ranks(folder: Path) -> dict[str, int | None]:
    """case_id -> 1-based rank of the judged match (None when not matched)."""
    text = (folder / DETAILS).read_text(encoding="utf-8")
    decoder = json.JSONDecoder()
    ranks: dict[str, int | None] = {}
    position = text.find("{")
    while position != -1:
        record, end = decoder.raw_decode(text, position)
        resolution = (record.get("eval_details") or {}).get("final_resolution")
        ranks[str(record["case_id"])] = (
            int(resolution["position"].lstrip("P")) if resolution else None
        )
        position = text.find("{", end)
    return ranks


def hit(rank: int | None, cutoff: int) -> bool:
    return rank is not None and rank <= cutoff


def mcnemar_exact(only_a: int, only_b: int) -> float:
    """Two-sided exact McNemar (binomial, p=0.5) on the discordant pairs."""
    n = only_a + only_b
    if n == 0:
        return 1.0
    tail = sum(comb(n, k) for k in range(min(only_a, only_b) + 1)) / 2**n
    return min(1.0, 2 * tail)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--arms", nargs="+", default=["none", "IN", "NG"])
    parser.add_argument("--baseline", default="none")
    args = parser.parse_args()

    folders = dict(split_arm(arm) for arm in args.arms)
    args.arms = list(folders)
    ranks = {label: read_ranks(folder) for label, folder in folders.items()}
    common = sorted(set.intersection(*(set(r) for r in ranks.values())))
    print(f"Cases scored in every arm: {len(common)}\n")

    print("| Arm | R@1 | R@3 | R@5 | Not matched |")
    print("|---|---|---|---|---|")
    for arm in args.arms:
        cells = [f"{sum(hit(ranks[arm][c], k) for c in common)}" for k in CUTOFFS]
        missed = sum(ranks[arm][c] is None for c in common)
        print(f"| {arm} | " + " | ".join(cells) + f" | {missed} |")

    base = ranks[args.baseline]
    for arm in args.arms:
        if arm == args.baseline:
            continue
        print(f"\n### {arm} vs {args.baseline}")
        for k in CUTOFFS:
            gained = [c for c in common if hit(ranks[arm][c], k) and not hit(base[c], k)]
            lost = [c for c in common if hit(base[c], k) and not hit(ranks[arm][c], k)]
            print(
                f"R@{k}: +{len(gained)} / -{len(lost)}  "
                f"(McNemar exact p = {mcnemar_exact(len(gained), len(lost)):.3f})"
            )
        moved = [c for c in common if ranks[arm][c] != base[c]]
        print(f"Cases whose judged rank changed at all: {len(moved)}/{len(common)}")


if __name__ == "__main__":
    main()
