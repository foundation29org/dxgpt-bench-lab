#!/usr/bin/env python3
"""
Turn harvested case reports into benchmark cases
================================================

For each article in raw/pmc_live/candidates.json an LLM decides whether it is
a diagnostic case, extracts the final diagnosis with its accepted names, and
copies the case presentation verbatim up to the point where the diagnosis is
revealed. A deterministic check (leakage.py) then rejects any case whose text
still names the diagnosis and flags softer hints for clinical review.

Output (not versioned): work/live_extracted.json

Usage:
    py extract_live_cases.py [--limit N] [--workers 8] [--model gemini-2.5-pro]
"""

import argparse
import json
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Dict

HERE = Path(__file__).resolve().parent
EVAL_ROOT = HERE.parents[2]
sys.path.insert(0, str(EVAL_ROOT))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(EVAL_ROOT / ".env")

from utils.llm import get_llm  # noqa: E402
from leakage import leak_check  # noqa: E402

CANDIDATES_PATH = HERE.parent / "raw" / "pmc_live" / "candidates.json"
OUTPUT_PATH = HERE / "work" / "live_extracted.json"
MAX_ARTICLE_CHARS = 30000
MIN_CASE_CHARS = 400

PROMPT = """You are a physician building a benchmark of diagnostic cases from published case reports.

Read the case report below and return a JSON object with these fields:

- "eligible": true only if ALL of these hold:
  1. it describes one index patient, who is a human;
  2. the patient presents without the final diagnosis being known, and the report reaches it;
  3. the final diagnosis is established in the report (pathology, genetics, imaging, laboratory or accepted clinical criteria), not only suspected;
  4. the final diagnosis is a disease, syndrome, poisoning, injury or adverse drug reaction, not a procedure, device problem or treatment outcome;
  5. the presentation before the diagnosis gives enough clinical information to build a differential diagnosis.
- "exclusion_reason": short reason when not eligible, else "".
- "final_diagnosis": the most specific final diagnosis the report establishes, in standard English medical terms.
- "accepted_names": other names that denote exactly the same entity (synonyms, abbreviations, eponyms). Do not include broader categories or related diseases.
- "secondary_diagnoses": other conditions diagnosed at the same time that are not the main point of the report (may be empty).
- "rare_disease": true if the final diagnosis is a rare disease (listed in Orphanet or prevalence below 1 in 2,000).
- "specialty": the main clinical specialty (one or two words).
- "case_text": the case presentation copied VERBATIM from the report, in its original order: demographics, history, symptoms, examination, and initial laboratory, imaging or other results. Rules:
  * stop before the sentence where the diagnosis is made or where a result names it (for example "biopsy confirmed ...", "genetic testing revealed a pathogenic variant in ...");
  * delete the final diagnosis, its accepted names, and any test whose name alone gives it away (a disease-specific antibody, a named mutation);
  * delete the authors' diagnostic reasoning: suspicions, differential diagnoses considered or excluded, and phrases such as "concerning for", "suggestive of" or "consistent with" followed by a diagnosis. Keep only what was observed or measured;
  * delete treatments aimed at the final diagnosis, references to figures or tables and citation markers;
  * keep negative findings and laboratory values;
  * you may replace a deleted phrase with neutral words so the sentence still reads well, but do not add information;
  * aim for 600 to 4,000 characters.
  If a presentation cannot be written without revealing the diagnosis, set "eligible" to false.
- "removed": one sentence listing what you deleted from the presentation to avoid revealing the diagnosis.

Return JSON only, without code fences.

Title: {title}

Abstract: {abstract}

Full text:
{body}
"""


def build_prompt(article: Dict) -> str:
    body = "\n\n".join(f"## {s['title']}\n{s['text']}" for s in article["sections"])
    return PROMPT.format(
        title=article["title"], abstract=article.get("abstract", ""), body=body[:MAX_ARTICLE_CHARS]
    )


def parse_json(text: str) -> Dict:
    text = text.strip()
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end < start:
        raise ValueError("no JSON object in response")
    return json.loads(text[start:end + 1])


def extract(llm, article: Dict, attempts: int = 3) -> Dict:
    prompt = build_prompt(article)
    error = None
    for attempt in range(1, attempts + 1):
        try:
            data = parse_json(str(llm.generate(prompt, max_tokens=16000, temperature=0.1)))
            break
        except Exception as exc:  # retry invalid or failed calls
            error = f"{type(exc).__name__}: {exc}"
            time.sleep(2 * attempt)
    else:
        return {"pmcid": article["pmcid"], "error": error}

    names = [data.get("final_diagnosis", "")] + list(data.get("accepted_names") or [])
    case_text = data.get("case_text") or ""
    hard_leaks, soft_leaks = leak_check(case_text, names)
    accepted = bool(data.get("eligible")) and not hard_leaks and len(case_text) >= MIN_CASE_CHARS
    return {
        "pmcid": article["pmcid"],
        "pmid": article["pmid"],
        "journal": article["journal"],
        "title": article["title"],
        "entrez_date": article["entrez_date"],
        "license": article["license"],
        "license_url": article["license_url"],
        **data,
        "leaked_terms": hard_leaks,
        "soft_leaked_terms": soft_leaks,
        "case_chars": len(case_text),
        "accepted": accepted,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--model", default="gemini-2.5-pro")
    args = parser.parse_args()

    articles = json.loads(CANDIDATES_PATH.read_text(encoding="utf-8"))[: args.limit]
    llm = get_llm(args.model)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    results = []
    lock = threading.Lock()
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {executor.submit(extract, llm, article): article for article in articles}
        for done, future in enumerate(as_completed(futures), start=1):
            result = future.result()
            with lock:
                results.append(result)
            if done % 10 == 0 or done == len(articles):
                accepted = sum(1 for r in results if r.get("accepted"))
                print(f"   {done}/{len(articles)} processed, {accepted} accepted")

    results.sort(key=lambda r: r["pmcid"])
    OUTPUT_PATH.write_text(json.dumps(results, ensure_ascii=False, indent=1), encoding="utf-8")
    summary = {
        "model": args.model,
        "processed": len(results),
        "errors": sum(1 for r in results if r.get("error")),
        "eligible": sum(1 for r in results if r.get("eligible")),
        "leaks": sum(1 for r in results if r.get("leaked_terms")),
        "accepted": sum(1 for r in results if r.get("accepted")),
        "rare_accepted": sum(1 for r in results if r.get("accepted") and r.get("rare_disease")),
    }
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
