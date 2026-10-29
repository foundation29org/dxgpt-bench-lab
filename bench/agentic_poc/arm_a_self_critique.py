#!/usr/bin/env python3
"""
Arm A — self-critique
=====================

The production model re-reads the case and its own differential, weighs the
findings for and against each diagnosis, and returns a revised top 5. No new
information enters: this is the control for "thinking it over twice".
With --base sol, gpt-6.1-sol revises its own list instead.

Usage:
    py arm_a_self_critique.py [--base terra|sol] [--limit N] [--workers 8]
"""

import argparse
from typing import Dict

from poc_common import BASE_MODELS, Model, arm_id, clean_diagnoses, load_lists, ranked_names, run_arm, write_arm

PROMPT = """You are an experienced diagnostician reviewing a differential diagnosis before it is shown to a clinician.

Case:
{case}

Current differential, most likely first:
{differential}

Review it critically:
- for each diagnosis, weigh the findings that support it and those that argue against it, including expected findings that are absent;
- consider whether a diagnosis that explains the findings better is missing, including rare diseases and serious conditions that must not be missed.

Return the final differential with at most 5 diagnoses, most likely first. You may keep, reorder, remove or add diagnoses. Use standard medical names.

Return JSON only: {{"diagnoses": ["...", "..."]}}"""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--base", default="terra", choices=list(BASE_MODELS),
                        help="Model whose list is revised; it also does the revision")
    args = parser.parse_args()

    name = arm_id("arm_a_self_critique", args.base)
    base = list(load_lists(args.base).values())[: args.limit]
    model = Model(BASE_MODELS[args.base], "low")

    def worker(case: Dict) -> Dict:
        differential = "\n".join(f"{i}. {dx}" for i, dx in enumerate(ranked_names(case), start=1))
        answer = model.ask_json(PROMPT.format(case=case["case"], differential=differential or "(empty)"))
        return {"diagnoses": clean_diagnoses(answer.get("diagnoses")), "base": ranked_names(case)}

    outputs = run_arm(name, base, worker, args.workers)
    write_arm(name, base, outputs, model.totals())


if __name__ == "__main__":
    main()
