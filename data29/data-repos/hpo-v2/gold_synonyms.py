#!/usr/bin/env python3
"""
MONDO synonyms for the HPO v2 gold (test, not yet a dataset version)
====================================================================

V5 shows the judge the gold as written, plus its accepted_names. The judge
only sees names, so it can miss a synonym: in MyGene2, Gemini 2.5 Pro did not
accept «distal arthrogryposis type 5» for «Arthrogryposis with oculomotor
limitation and electroretinal anomalies» (both OMIM 108145) and accepted
«distal arthrogryposis type 5D», another disease (ECEL1, OMIM 615065).

This script adds to accepted_names the MONDO label and the MONDO exact
synonyms of each gold with an OMIM code (DDD: its MONDO id). Related, broad
and narrow synonyms are left out, and so are Orphanet codes, which are often
groups of several OMIM diseases. A synonym that is one of the HPO terms of the
case is left out too, as in clinical_gold.py. The gene-free gold (role
"clinical") has no code and does not change.

The dataset code can be wrong: in HMS, «Reactive arthritis» carries OMIM
270150, which is Sjögren syndrome. So synonyms are added only when the gold
name shares at least one meaningful word with the MONDO entry, and never from
an obsolete MONDO term. The golds left out are listed in
work/synonyms_skipped.txt for review.

Steps:
    py gold_synonyms.py fetch   # Monarch API, cached in work/mondo_synonyms.json
    py gold_synonyms.py build   # writes bench/datasets/<dataset>_v2_syn.json
"""

import argparse
import json
import re
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor

from clinical_gold import DATASETS, DATASETS_DIR, HERE, input_terms, load, norm

MONARCH = "https://api-v3.monarchinitiative.org/v3/api"
CACHE_PATH = HERE / "work" / "mondo_synonyms.json"
SKIPPED_PATH = HERE / "work" / "synonyms_skipped.txt"
VERSION = "v2_syn"
# Words that do not tell two diseases apart, ignored when matching the gold name with its MONDO entry
GENERIC_WORDS = {"syndrome", "disease", "disorder", "type", "with", "and", "the", "due", "for", "related", "autosomal",
                 "dominant", "recessive", "linked", "form", "familial", "congenital", "hereditary", "primary"}


def words(text):
    return {w for w in re.findall(r"[a-z0-9]+", text.lower()) if len(w) >= 3 and w not in GENERIC_WORDS}


def gold_code(diag):
    """MONDO id for DDD, else the OMIM code; None for the gene-free gold or without OMIM."""
    if diag.get("role") == "clinical":
        return None
    if diag.get("mondo"):
        return diag["mondo"]
    omim = diag.get("omim") or (diag.get("medical_codes") or {}).get("omim") or []
    omim = [omim] if isinstance(omim, str) else omim
    return f"OMIM:{omim[0]}" if len(omim) == 1 else None


def get_json(url, attempts=4):
    for attempt in range(attempts):
        try:
            with urllib.request.urlopen(url, timeout=30) as response:
                return json.load(response)
        except Exception:
            if attempt == attempts - 1:
                raise
            time.sleep(2 * (attempt + 1))


def resolve(code):
    """MONDO id, label and exact synonyms for a MONDO or OMIM code."""
    try:
        mondo = code
        if not code.startswith("MONDO:"):
            items = get_json(f"{MONARCH}/search?q={urllib.parse.quote(code)}&limit=10")["items"]
            matches = [i["id"] for i in items if i["id"].startswith("MONDO:") and code in (i.get("xref") or [])]
            if len(matches) != 1:
                return {"error": f"{len(matches)} MONDO matches"}
            mondo = matches[0]
        entity = get_json(f"{MONARCH}/entity/{mondo}")
        return {"mondo": mondo, "label": entity.get("name"), "exact": entity.get("exact_synonym") or []}
    except Exception as exc:
        return {"error": f"{type(exc).__name__}: {exc}"}


def fetch(args):
    cache = json.loads(CACHE_PATH.read_text(encoding="utf-8")) if CACHE_PATH.exists() else {}
    cache = {k: v for k, v in cache.items() if "error" not in v}
    codes = {gold_code(d) for name in DATASETS for c in load(f"{name}_v2") for d in c["diagnoses"]} - {None}
    pending = sorted(codes - set(cache))
    print(f"{len(codes)} codes, {len(pending)} pending")
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        for code, row in zip(pending, executor.map(resolve, pending)):
            cache[code] = row
    CACHE_PATH.write_text(json.dumps(cache, indent=1, ensure_ascii=False), encoding="utf-8")
    errors = [code for code, row in cache.items() if "error" in row]
    print(f"Saved {len(cache)} codes to {CACHE_PATH} ({len(errors)} without a single MONDO match)")


def build(args):
    cache = json.loads(CACHE_PATH.read_text(encoding="utf-8"))
    skipped = []
    for name in DATASETS:
        cases = load(f"{name}_v2")
        stats = dict(cases=len(cases), changed=0, golds_with_code=0, golds_changed=0, names_added=0, in_input=0,
                     no_match=0)
        for case in cases:
            changed = False
            terms = input_terms(case)
            for diag in case["diagnoses"]:
                code = gold_code(diag)
                row = cache.get(code or "")
                if not row or "error" in row:
                    continue
                stats["golds_with_code"] += 1
                gold_words = words(diag["name"]) | {w for n in diag.get("accepted_names") or [] for w in words(n)}
                mondo_words = words(row["label"] or "") | {w for s in row["exact"] for w in words(s)}
                if (row["label"] or "").startswith("obsolete") or not gold_words & mondo_words:
                    stats["no_match"] += 1
                    skipped.append(f"{name}\t{case['id']}\t{diag['name']}\t{code} {row['mondo']}\t{row['label']}")
                    continue
                known = {norm(diag["name"])} | {norm(n) for n in diag.get("accepted_names") or []}
                added = []
                for synonym in [row["label"]] + row["exact"]:
                    if not synonym or norm(synonym) in known:
                        continue
                    known.add(norm(synonym))
                    if norm(synonym) in terms:
                        stats["in_input"] += 1
                        continue
                    added.append(synonym)
                if added:
                    diag["accepted_names"] = (diag.get("accepted_names") or []) + added
                    stats["golds_changed"] += 1
                    stats["names_added"] += len(added)
                    changed = True
            stats["changed"] += changed
            case.setdefault("metadata", {})["gold_version"] = f"hpo_{VERSION}"
        path = DATASETS_DIR / f"{name}_{VERSION}.json"
        path.write_text(json.dumps(cases, indent=1, ensure_ascii=False), encoding="utf-8")
        print(f"{path.name}: {json.dumps(stats)}")
    SKIPPED_PATH.write_text("\n".join(sorted(set(skipped))) + "\n", encoding="utf-8")
    print(f"Golds without synonyms because the name does not match the MONDO entry: {SKIPPED_PATH}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("step", choices=["fetch", "build"])
    parser.add_argument("--workers", type=int, default=6)
    args = parser.parse_args()
    fetch(args) if args.step == "fetch" else build(args)


if __name__ == "__main__":
    main()
