#!/usr/bin/env python3
"""
Compare a Pipeline V4 evaluation with a Pipeline V5 evaluation of the same DDX
==============================================================================

Reads two evaluation_details.txt files and writes a Markdown report with the
metrics of both and every case whose strict result changes, grouped by the
V4 layer that had decided it.

Usage:
    py compare_runs.py --baseline <v4 evaluation_details.txt> \
                       --candidate <v5 evaluation_details.txt> \
                       [--output comparison.md]
"""

import argparse
import json
import os
from typing import Dict, List, Optional


def load_details(path: str) -> Dict[str, Dict]:
    with open(path, 'r', encoding='utf-8') as f:
        blocks = f.read().split('\n---\n')
    cases = {}
    for block in blocks:
        if block.strip():
            case = json.loads(block)
            cases[str(case["case_id"])] = case
    return cases


def position(resolution: Optional[Dict]) -> Optional[int]:
    return int(resolution["position"][1:]) if resolution else None


def recall_row(label: str, positions: List[Optional[int]]) -> str:
    total = len(positions)

    def pct(k: Optional[int]) -> str:
        hits = sum(1 for p in positions if p is not None and (k is None or p <= k))
        return f"{hits / total * 100:.1f}% ({hits})"

    return f"| {label} | {pct(1)} | {pct(3)} | {pct(5)} | {pct(None)} |"


def option_grade(case: Dict, gdx_name: str, ddx_position: int) -> str:
    for gdx_trace in case["eval_details"].get("graded_trace", []):
        if gdx_trace["gdx"] != gdx_name:
            continue
        for option in gdx_trace["options"]:
            if option["position"] == ddx_position:
                return str(option["grade"])
    return "?"


def main():
    parser = argparse.ArgumentParser(description="Compare V4 and V5 evaluations of the same DDX lists")
    parser.add_argument('--baseline', required=True, help='V4 evaluation_details.txt')
    parser.add_argument('--candidate', required=True, help='V5 evaluation_details.txt')
    parser.add_argument('--output', default=None, help='Markdown report (default: comparison.md next to candidate)')
    args = parser.parse_args()

    baseline = load_details(args.baseline)
    candidate = load_details(args.candidate)
    case_ids = [case_id for case_id in candidate if case_id in baseline]

    v4_positions, v5_strict, v5_lax = [], [], []
    lost, gained, moved = [], [], []
    for case_id in case_ids:
        v4_resolution = baseline[case_id]["eval_details"].get("final_resolution")
        v5_resolution = candidate[case_id]["eval_details"].get("final_resolution")
        v5_lax_resolution = candidate[case_id]["eval_details"].get("lax_resolution")
        v4_pos, v5_pos = position(v4_resolution), position(v5_resolution)
        v4_positions.append(v4_pos)
        v5_strict.append(v5_pos)
        v5_lax.append(position(v5_lax_resolution))

        if v4_pos == v5_pos:
            continue
        gold = next(iter((v4_resolution or v5_resolution or {}).get("matched_gdx", {"?": None})))
        row = {
            "case_id": case_id,
            "gold": gold,
            "v4": f"P{v4_pos} {next(iter(v4_resolution['matched_ddx']))} ({v4_resolution['method']})" if v4_resolution else "—",
            "v5": f"P{v5_pos} {next(iter(v5_resolution['matched_ddx']))} ({v5_resolution['method']})" if v5_resolution else "—",
            "v4_method": v4_resolution["method"] if v4_resolution else "NO_MATCH",
        }
        if v4_resolution and not v5_resolution:
            row["v5_grade_of_v4_option"] = option_grade(candidate[case_id], gold, v4_pos)
            lost.append(row)
        elif v5_resolution and not v4_resolution:
            gained.append(row)
        else:
            moved.append(row)

    lines = [
        "# Pipeline V4 vs V5 — mismas listas DDX",
        "",
        f"- Baseline (V4): `{args.baseline}`",
        f"- Candidate (V5): `{args.candidate}`",
        f"- Casos comparados: {len(case_ids)}",
        "",
        "| Evaluación | R@1 | R@3 | R@5 | Cobertura |",
        "|---|---:|---:|---:|---:|",
        recall_row("V4 strict", v4_positions),
        recall_row("V5 estricta (grado 2)", v5_strict),
        recall_row("V5 laxa (grado ≥ 1)", v5_lax),
        "",
        f"## Aciertos de V4 que V5 no da por buenos ({len(lost)})",
        "",
        "Agrupados por la capa de V4 que los decidía. «Grado V5» es la nota que V5 da a la opción que V4 contaba.",
        "",
    ]
    for method in sorted({row["v4_method"] for row in lost}):
        group = [row for row in lost if row["v4_method"] == method]
        lines += [f"### {method} ({len(group)})", "", "| Caso | Gold | V4 | Grado V5 |", "|---|---|---|---:|"]
        lines += [f"| {r['case_id']} | {r['gold']} | {r['v4']} | {r['v5_grade_of_v4_option']} |" for r in group]
        lines.append("")

    lines += [f"## Aciertos nuevos en V5 ({len(gained)})", "", "| Caso | Gold | V5 |", "|---|---|---|"]
    lines += [f"| {r['case_id']} | {r['gold']} | {r['v5']} |" for r in gained]
    lines += ["", f"## Cambios de posición ({len(moved)})", "", "| Caso | Gold | V4 | V5 |", "|---|---|---|---|"]
    lines += [f"| {r['case_id']} | {r['gold']} | {r['v4']} | {r['v5']} |" for r in moved]

    output = args.output or os.path.join(os.path.dirname(os.path.abspath(args.candidate)), 'comparison.md')
    with open(output, 'w', encoding='utf-8') as f:
        f.write("\n".join(lines) + "\n")
    print(f"Comparison written to {output}")


if __name__ == "__main__":
    main()
