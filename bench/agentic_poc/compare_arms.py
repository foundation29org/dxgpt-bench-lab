#!/usr/bin/env python3
"""
Compare the PoC arms with the single-model runs on narrative_v2
===============================================================

Strict R@1 and R@5 by block, median list length, extra cost of the second
stage, and exact McNemar on the real cases (live + urg) against
gpt-5.6-terra alone (production) and against gpt-6.1-sol alone. Arms named
*_on_sol start from Sol's list; the rest from Terra's.

Usage:
    py compare_arms.py [arm ...]   (default: every arm)
"""

import json
import statistics
import sys
from math import comb
from typing import Dict, List, Optional

from poc_common import BASE_LISTS, EVAL_ROOT, RUN_FOLDERS, RUNS_DIR, WORK_DIR, base_of

SINGLE = {
    "gpt-5.6-terra (base)": RUN_FOLDERS["terra"],
    "gpt-6.1-sol": RUN_FOLDERS["sol"],
    "claude-opus-5": RUN_FOLDERS["opus"],
}
REFERENCES = {"terra": "gpt-5.6-terra (base)", "sol": "gpt-6.1-sol"}
ARMS = ["arm_a_self_critique", "arm_b_panel", "arm_b_panel_terra_sol", "arm_c_sources",
        "arm_a_self_critique_on_sol", "arm_b_panel_terra_sol_on_sol", "arm_c_sources_on_sol"]
GROUPS = [("live", {"live"}), ("urg", {"urg"}), ("live+urg", {"live", "urg"}),
          ("exam", {"exam"}), ("synth", {"synth"}), ("total", {"live", "urg", "exam", "synth"})]


def latest_details(folder: str) -> Optional[Dict[str, Optional[int]]]:
    runs = sorted(p for p in (RUNS_DIR / folder).glob("2026*") if (p / "evaluation_details.txt").exists())
    if not runs:
        return None
    positions = {}
    for block in (runs[-1] / "evaluation_details.txt").read_text(encoding="utf-8").split("\n---\n"):
        if block.strip():
            row = json.loads(block)
            resolution = row["eval_details"].get("final_resolution")
            positions[row["case_id"]] = int(resolution["position"][1:]) if resolution else None
    return positions


def mcnemar_exact(only_a: int, only_b: int) -> float:
    """Two-sided exact McNemar (binomial, p=0.5) on the discordant pairs."""
    n = only_a + only_b
    if n == 0:
        return 1.0
    tail = sum(comb(n, k) for k in range(min(only_a, only_b) + 1)) / 2 ** n
    return min(1.0, 2 * tail)


def hit(position: Optional[int], k: int) -> bool:
    return position is not None and position <= k


def main():
    arms = sys.argv[1:] or ARMS
    dataset = json.loads((EVAL_ROOT / "bench" / "datasets" / "narrative_v2.json").read_text(encoding="utf-8"))
    block = {case["id"]: case["metadata"]["block"] for case in dataset}
    runs = {label: latest_details(folder) for label, folder in SINGLE.items()}
    for arm in arms:
        runs[arm] = latest_details(f"{RUN_FOLDERS[base_of(arm)]}__{arm}")
    runs = {label: positions for label, positions in runs.items() if positions}

    for k in (1, 5):
        print(f"\nR@{k} estricta\n")
        print("| Run | " + " | ".join(name for name, _ in GROUPS) + " |")
        print("|---|" + "---:|" * len(GROUPS))
        for label, positions in runs.items():
            cells = []
            for _, blocks in GROUPS:
                ids = [c for c in positions if block.get(c) in blocks]
                cells.append(f"{sum(hit(positions[c], k) for c in ids) / len(ids) * 100:.1f} %")
            print(f"| {label} | " + " | ".join(cells) + " |")

    real = [c for c in block if block[c] in ("live", "urg")]
    for reference in ("gpt-5.6-terra (base)", "gpt-6.1-sol"):
        if reference not in runs:
            continue
        print(f"\nCasos reales (live+urg, {len(real)}) frente a {reference}\n")
        print("| Run | R@1 gana / pierde | p | R@5 gana / pierde | p |")
        print("|---|---:|---:|---:|---:|")
        ref = runs[reference]
        for label, positions in runs.items():
            if label == reference:
                continue
            cells = []
            for k in (1, 5):
                gains = sum(hit(positions.get(c), k) and not hit(ref.get(c), k) for c in real)
                losses = sum(hit(ref.get(c), k) and not hit(positions.get(c), k) for c in real)
                cells.append(f"{gains} / {losses} ({(gains - losses) / len(real) * 100:+.1f} pp) | {mcnemar_exact(gains, losses):.3f}")
            print(f"| {label} | " + " | ".join(cells) + " |")

    # Each arm against the model whose list it revised.
    rare_flag = {case["id"]: case["metadata"]["rare_disease"] for case in dataset}
    for base, label_ref in REFERENCES.items():
        reference = runs.get(label_ref)
        family = [label for label in runs if label == label_ref or (label in arms and base_of(label) == base)]
        if not reference or len(family) < 2:
            continue
        for rare in (True, False):
            ids = [c for c in real if rare_flag[c] == rare]
            print(f"\nR@1 en casos reales {'de raras' if rare else 'no raras'} ({len(ids)}) frente a {label_ref}\n")
            print("| Run | R@1 | Gana / pierde | p |")
            print("|---|---:|---:|---:|")
            for label in family:
                positions = runs[label]
                gains = sum(hit(positions.get(c), 1) and not hit(reference.get(c), 1) for c in ids)
                losses = sum(hit(reference.get(c), 1) and not hit(positions.get(c), 1) for c in ids)
                rate = sum(hit(positions.get(c), 1) for c in ids) / len(ids) * 100
                print(f"| {label} | {rate:.1f} % | {gains} / {losses} | {mcnemar_exact(gains, losses):.3f} |")

        # The arms return 5 options (median), sometimes more than their base:
        # R@5 could improve only because the lists are longer. Here a hit counts
        # only within the number of options the base model gave in that case.
        base_lists = json.loads(BASE_LISTS[base].read_text(encoding="utf-8"))
        base_length = {case["id"]: min(5, len(case.get("ddx_details", {}))) for case in base_lists}
        print(f"\nControl de longitud: acierto dentro de las opciones que dio {label_ref} en cada caso "
              f"(live+urg, mediana {statistics.median(base_length[c] for c in real)})\n")
        print("| Run | Acierto | Gana / pierde frente a la base | p |")
        print("|---|---:|---:|---:|")
        for label in family:
            positions = runs[label]
            hits = [c for c in real if hit(positions.get(c), base_length[c])]
            gains = sum(1 for c in real if hit(positions.get(c), base_length[c]) and not hit(reference.get(c), base_length[c]))
            losses = sum(1 for c in real if hit(reference.get(c), base_length[c]) and not hit(positions.get(c), base_length[c]))
            print(f"| {label} | {len(hits) / len(real) * 100:.1f} % | {gains} / {losses} | {mcnemar_exact(gains, losses):.3f} |")

    print("\nCoste y latencia de la segunda etapa (solo las llamadas del brazo)\n")
    print("| Brazo | Llamadas | Coste | Coste por caso | Mediana por llamada | Opciones (mediana) |")
    print("|---|---:|---:|---:|---:|---:|")
    for arm in arms:
        traces_path = WORK_DIR / f"{arm}_traces.json"
        if not traces_path.exists():
            continue
        traces = json.loads(traces_path.read_text(encoding="utf-8"))
        totals = traces["totals"]
        lengths = [len(c["diagnoses"]) for c in traces["cases"]]
        per_case = totals["cost_usd"] / len(traces["cases"])
        print(f"| {arm} | {totals['calls']} | {totals['cost_usd']:.2f} $ | {per_case * 1000:.1f} m$ | "
              f"{totals['p50_seconds']} s | {statistics.median(lengths)} |")


if __name__ == "__main__":
    main()
