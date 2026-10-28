#!/usr/bin/env python3
"""
Triage the internal sources for narrative_v2
============================================

Blocks:
- urg:   raw/urgtorre.json, real emergency cases in Spanish.
- exam:  raw/medqausmle4op.json and raw/medbulltes5op.json, only vignettes whose
         final question asks for the diagnosis.
- synth: raw/rare_synthetic.json, synthetic rare-disease narratives.

A seeded sample of each block goes to an LLM, which keeps the case only if its
principal diagnosis is a disease, separates symptoms and prior conditions from
the gold, and returns the case text without the exam question or anything that
reveals the diagnosis. leakage.py then rejects texts that still name it.

Output (not versioned): work/internal_triaged.json

Usage:
    py select_internal_cases.py [--urg 200] [--exam 150] [--synth 60] [--workers 8]
"""

import argparse
import json
import random
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List

from extract_live_cases import HERE, MIN_CASE_CHARS, parse_json
from leakage import leak_check
from utils.llm import get_llm

RAW_DIR = HERE.parent / "raw"
OUTPUT_PATH = HERE / "work" / "internal_triaged.json"
DIAGNOSIS_QUESTION = re.compile(r"diagnos", re.IGNORECASE)

PROMPT = """You are a physician curating a benchmark of diagnostic cases. A case and the diagnoses that a previous process attached to it are below.

Return a JSON object with these fields:

- "eligible": true only if the case describes a patient whose main diagnosis is a disease, syndrome, poisoning, injury or adverse drug reaction that can be reasoned from the text. Set false if the gold is only a symptom, sign, laboratory finding, mechanism, gene, stage or normal state; if the case is a follow-up of an already known condition; or if the text asks about something other than this patient's diagnosis.
- "exclusion_reason": short reason when not eligible, else "".
- "principal_diagnosis": the main diagnosis for this visit, in standard English medical terms. Take it from the attached diagnoses or the original discharge diagnosis; do not add a diagnosis of your own.
- "accepted_names": other names for exactly the same entity (synonyms, abbreviations, eponyms). No broader categories.
- "secondary_diagnoses": other diseases diagnosed at the same visit, taken only from the attached diagnoses or the original discharge diagnosis. Leave out symptoms, findings and previously known conditions.
- "dropped_golds": attached diagnoses you did not keep, each with a short reason.
- "rare_disease": true if the principal diagnosis is a rare disease (Orphanet-listed or prevalence below 1 in 2,000).
- "specialty": main clinical specialty (one or two words).
- "case_text": the case text copied VERBATIM and in its original language, except that you must delete: any exam question and answer options; any sentence or phrase that names the principal diagnosis, its accepted names, or a result that gives it away. Do not add information.

Return JSON only, without code fences.

{source_note}

Attached diagnoses: {golds}

Case:
{case}
"""


def final_question(text: str) -> str:
    sentences = re.split(r"(?<=[.?!])\s+", text.strip())
    return sentences[-1] if sentences and sentences[-1].endswith("?") else ""


def load_pools() -> Dict[str, List[Dict]]:
    """Seeded candidates per block, before the LLM triage."""
    def load(name):
        return json.loads((RAW_DIR / name).read_text(encoding="utf-8"))

    exam_pool = [
        case for name in ("medqausmle4op.json", "medbulltes5op.json") for case in load(name)
        if DIAGNOSIS_QUESTION.search(final_question(case["case"]))
    ]
    return {
        "urg": load("urgtorre.json"),
        "exam": exam_pool,
        "synth": load("rare_synthetic.json"),
    }


def triage(llm, block: str, case: Dict, attempts: int = 3) -> Dict:
    golds = "; ".join(d["name"] for d in case.get("diagnoses", []))
    source_note = ""
    if block == "urg":
        original = (case.get("metadata") or {}).get("original_diagnosis", "")
        source_note = f"Original discharge diagnosis written by the emergency physician (Spanish): {original}"
    prompt = PROMPT.format(source_note=source_note, golds=golds, case=case["case"])
    error = None
    for attempt in range(1, attempts + 1):
        try:
            data = parse_json(str(llm.generate(prompt, max_tokens=12000, temperature=0.1)))
            break
        except Exception as exc:  # retry invalid or failed calls
            error = f"{type(exc).__name__}: {exc}"
            time.sleep(2 * attempt)
    else:
        return {"block": block, "source_id": case["id"], "error": error}

    names = [data.get("principal_diagnosis", "")] + list(data.get("accepted_names") or [])
    case_text = data.get("case_text") or ""
    hard_leaks, soft_leaks = leak_check(case_text, names)
    return {
        "block": block,
        "source_id": case["id"],
        "complexity": case.get("complexity"),
        "original_golds": [d["name"] for d in case.get("diagnoses", [])],
        "source_metadata": case.get("metadata"),
        **data,
        "leaked_terms": hard_leaks,
        "soft_leaked_terms": soft_leaks,
        "case_chars": len(case_text),
        "accepted": bool(data.get("eligible")) and not hard_leaks and len(case_text) >= MIN_CASE_CHARS,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--urg", type=int, default=200)
    parser.add_argument("--exam", type=int, default=150)
    parser.add_argument("--synth", type=int, default=60)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--model", default="gemini-2.5-pro")
    parser.add_argument("--seed", type=int, default=29)
    args = parser.parse_args()

    rng = random.Random(args.seed)
    pools = load_pools()
    jobs = []
    for block, size in (("urg", args.urg), ("exam", args.exam), ("synth", args.synth)):
        chosen = rng.sample(pools[block], min(size, len(pools[block])))
        jobs += [(block, case) for case in chosen]
        print(f"   {block}: {len(pools[block])} in pool, {len(chosen)} sampled")

    llm = get_llm(args.model)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    results = []
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = [executor.submit(triage, llm, block, case) for block, case in jobs]
        for done, future in enumerate(as_completed(futures), start=1):
            results.append(future.result())
            if done % 20 == 0 or done == len(jobs):
                print(f"   {done}/{len(jobs)} triaged, {sum(1 for r in results if r.get('accepted'))} accepted")

    results.sort(key=lambda r: (r["block"], r["source_id"]))
    OUTPUT_PATH.write_text(json.dumps(results, ensure_ascii=False, indent=1), encoding="utf-8")
    for block in ("urg", "exam", "synth"):
        rows = [r for r in results if r["block"] == block]
        print(f"   {block}: {sum(1 for r in rows if r.get('accepted'))}/{len(rows)} accepted, "
              f"{sum(1 for r in rows if r.get('error'))} errors, "
              f"{sum(1 for r in rows if r.get('leaked_terms'))} leaks")


if __name__ == "__main__":
    main()
