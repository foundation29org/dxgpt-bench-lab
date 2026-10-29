#!/usr/bin/env python3
"""
Arm B — panel of models
=======================

Three models answered each case independently with the production prompt
(gpt-5.6-terra, gpt-6.1-sol and claude-opus-5; frozen Pipeline V5 lists). The
production model acts as moderator: it sees the case and the three anonymous
lists, merges synonyms and returns a consolidated top 5. This is the offline
version of a MAI-DxO-style panel.

--panel chooses the members and --moderator the model that consolidates.

Usage:
    py arm_b_panel.py [--panel terra sol opus] [--moderator terra|sol] [--limit N] [--workers 8]
"""

import argparse
from typing import Dict

from poc_common import BASE_MODELS, Model, arm_id, clean_diagnoses, load_lists, ranked_names, run_arm, write_arm

PANEL = ("terra", "sol", "opus")

PROMPT = """You moderate a panel of three physicians who reviewed the same case independently. Each proposed a differential diagnosis, most likely first.

Case:
{case}

{lists}

Build the panel's final differential:
- merge diagnoses that name the same entity;
- weigh agreement between physicians, but put first the diagnosis that best explains all the findings, even if only one physician proposed it;
- keep at most 5 diagnoses, most likely first, with standard medical names.

Return JSON only: {{"diagnoses": ["...", "..."]}}"""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--panel", nargs="+", default=list(PANEL), choices=list(PANEL),
                        help="Models on the panel; a smaller panel is written as arm_b_panel_<names>")
    parser.add_argument("--moderator", default="terra", choices=list(BASE_MODELS),
                        help="Model that consolidates the lists (the arm's base)")
    args = parser.parse_args()

    members = args.panel
    arm = "arm_b_panel" if members == list(PANEL) else "arm_b_panel_" + "_".join(members)
    arm = arm_id(arm, args.moderator)
    panel = {name: load_lists(name) for name in members}
    base = list(load_lists(args.moderator).values())[: args.limit]
    model = Model(BASE_MODELS[args.moderator], "low")
    count_word = {2: "two", 3: "three"}.get(len(members), str(len(members)))

    def worker(case: Dict) -> Dict:
        lists = []
        for letter, name in zip("ABC", members):
            names = ranked_names(panel[name].get(case["id"], {}), 5)
            items = "\n".join(f"{i}. {dx}" for i, dx in enumerate(names, start=1)) or "(no answer)"
            lists.append(f"Physician {letter}:\n{items}")
        prompt = PROMPT.replace("three physicians", f"{count_word} physicians")
        answer = model.ask_json(prompt.format(case=case["case"], lists="\n\n".join(lists)))
        return {"diagnoses": clean_diagnoses(answer.get("diagnoses")),
                "panel": {name: ranked_names(panel[name].get(case["id"], {}), 5) for name in members}}

    outputs = run_arm(arm, base, worker, args.workers)
    write_arm(arm, base, outputs, model.totals())


if __name__ == "__main__":
    main()
