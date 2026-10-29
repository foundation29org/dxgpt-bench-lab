#!/usr/bin/env python3
"""
Second leakage check for accepted cases with soft hints
=======================================================

leakage.py only rejects a case when the text names the diagnosis or a word
that clearly denotes it. Words such as an enzyme or a histological pattern are
left as soft hints ("phosphofructokinase" in glycogen storage disease type
VII). This script asks an LLM whether each of those texts reveals the
diagnosis, and rejects the cases that do.

Updates in place: work/live_extracted.json and work/internal_triaged.json
(fields llm_leak and accepted).

Usage:
    py audit_leakage.py [--workers 8]
"""

import argparse
import json
from concurrent.futures import ThreadPoolExecutor
from typing import Dict

from extract_live_cases import HERE, parse_json
from utils.llm import get_llm

FILES = {"final_diagnosis": HERE / "work" / "live_extracted.json",
         "principal_diagnosis": HERE / "work" / "internal_triaged.json"}

PROMPT = """You check diagnostic benchmark cases for label leakage.

Final diagnosis: {diagnosis}
Also known as: {names}
Words of the diagnosis found in the text: {hints}

Case text:
{case}

Does the case text reveal the final diagnosis? It does if it names the diagnosis or an accepted name, or reports a result that by itself establishes it (a named mutation, a deficient enzyme that defines the disease, a pathology report naming the entity). It does not if the words only describe anatomy, symptoms, a causative drug or exposure, or findings that a clinician still has to interpret.

Return JSON only: {{"leak": true or false, "evidence": "the phrase that reveals it, or empty"}}"""


def audit(llm, row: Dict, diagnosis_field: str) -> Dict:
    prompt = PROMPT.format(
        diagnosis=row[diagnosis_field],
        names=", ".join(row.get("accepted_names") or []) or "—",
        hints=", ".join(row["soft_leaked_terms"]),
        case=row["case_text"],
    )
    try:
        verdict = parse_json(str(llm.generate(prompt, max_tokens=8000, temperature=0.1)))
    except Exception as exc:  # keep the case flagged for clinical review
        verdict = {"leak": None, "evidence": f"{type(exc).__name__}: {exc}"}
    return verdict


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--model", default="gemini-2.5-pro")
    args = parser.parse_args()
    llm = get_llm(args.model)

    for diagnosis_field, path in FILES.items():
        rows = json.loads(path.read_text(encoding="utf-8"))
        targets = [r for r in rows if r.get("accepted") and r.get("soft_leaked_terms") and "llm_leak" not in r]
        with ThreadPoolExecutor(max_workers=args.workers) as executor:
            verdicts = list(executor.map(lambda r: audit(llm, r, diagnosis_field), targets))
        for row, verdict in zip(targets, verdicts):
            row["llm_leak"] = verdict
            if verdict.get("leak") is True:
                row["accepted"] = False
        path.write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
        leaks = [(r.get("pmcid") or r.get("source_id"), r[diagnosis_field], r["llm_leak"]["evidence"])
                 for r in targets if r["llm_leak"].get("leak")]
        print(f"{path.name}: {len(targets)} audited, {len(leaks)} rejected")
        for leak in leaks:
            print("   ", " | ".join(str(part) for part in leak))


if __name__ == "__main__":
    main()
