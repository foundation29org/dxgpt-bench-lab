#!/usr/bin/env python3
"""
Bring live gold diagnoses to the level a differential diagnosis names
======================================================================

Case reports state very detailed diagnoses ("Low-grade mucoepidermoid
carcinoma of the palatine tonsil", "Rhabdoid variant of pancreatic
neuroendocrine neoplasm, G2"). Under the V5 rubric an answer that omits grade,
stage or exact site gets a 1, so the gold would ask for more than a
differential is meant to give. This step keeps the detailed diagnosis in
final_diagnosis_detailed and sets final_diagnosis to the diagnostic entity,
then re-runs the leakage check with the new names.

Updates in place: work/live_extracted.json

Usage:
    py set_entity_level.py [--workers 8]
"""

import argparse
import json
from concurrent.futures import ThreadPoolExecutor
from typing import Dict

from extract_live_cases import HERE, parse_json
from leakage import leak_check
from utils.llm import get_llm

PATH = HERE / "work" / "live_extracted.json"

PROMPT = """A case report established this final diagnosis: {diagnosis}
Accepted names: {names}

Return the diagnostic entity a clinician would write in a differential diagnosis list for this patient. Remove grade, stage, size, laterality, the exact anatomical sub-site, and histological or molecular variants, unless they define a distinct disease with its own name (keep "Glycogen storage disease type VII", "Juvenile granulosa cell tumor"; reduce "Low-grade mucoepidermoid carcinoma of the palatine tonsil" to "Mucoepidermoid carcinoma of the tonsil"). If the diagnosis is already at that level, return it unchanged.

Return JSON only: {{"entity": "...", "accepted_names": ["other names for exactly that entity"]}}"""


def entity_level(llm, row: Dict) -> Dict:
    prompt = PROMPT.format(diagnosis=row["final_diagnosis"], names=", ".join(row.get("accepted_names") or []) or "—")
    try:
        return parse_json(str(llm.generate(prompt, max_tokens=4000, temperature=0.1)))
    except Exception as exc:  # keep the detailed diagnosis
        return {"entity": row["final_diagnosis"], "accepted_names": row.get("accepted_names") or [], "error": str(exc)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--model", default="gemini-2.5-pro")
    args = parser.parse_args()
    llm = get_llm(args.model)

    rows = json.loads(PATH.read_text(encoding="utf-8"))
    targets = [r for r in rows if r.get("accepted") and "final_diagnosis_detailed" not in r]
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        results = list(executor.map(lambda r: entity_level(llm, r), targets))

    changed, rejected = 0, []
    for row, result in zip(targets, results):
        row["final_diagnosis_detailed"] = row["final_diagnosis"]
        row["accepted_names_detailed"] = row.get("accepted_names") or []
        row["final_diagnosis"] = result.get("entity") or row["final_diagnosis"]
        row["accepted_names"] = result.get("accepted_names") or []
        changed += row["final_diagnosis"] != row["final_diagnosis_detailed"]
        hard, soft = leak_check(row["case_text"], [row["final_diagnosis"], *row["accepted_names"]])
        if hard:
            row["leaked_terms"] = hard
            row["accepted"] = False
            rejected.append((row["pmcid"], row["final_diagnosis"], hard))
        row["soft_leaked_terms"] = sorted(set(row.get("soft_leaked_terms") or []) | set(soft))

    PATH.write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(targets)} processed, {changed} brought to entity level, {len(rejected)} rejected for leakage")
    for item in rejected:
        print("   ", item)


if __name__ == "__main__":
    main()
