#!/usr/bin/env python3
"""
Clinical gold without gene for the HPO datasets (HPO v2)
========================================================

The model under test only sees a list of HPO terms, but many gold diagnoses
carry information that only genetic testing gives: a gene ("BBS9-related
BBS"), a gene-defined subtype ("MSUD type Ia", "Leber congenital amaurosis
2") or a complementation group. Under the V5 rubric an answer that names the
right syndrome without the gene gets a 1, so the case fails for a reason the
model cannot fix.

This script adds a second gold, role "clinical", with the name a clinician
could give from the phenotype alone ("Bardet-Biedl syndrome"). The V5
evaluator grades every gold and keeps the best (rule C3), so the original gold
still counts. The clinical gold is added only when:

- it differs from the original gold;
- it is still a disease or syndrome with its own clinical identity, not a
  generic phenotype ("intellectual disability", "epilepsy") or a list of
  features;
- it is not one of the HPO terms of the case, which would give the answer
  away ("Retinal dystrophy").

Codes, abbreviations and repeated synonyms in the gold name ("ORPHA:761",
"DA8") get a readable name in accepted_names, because V5 shows the judge the
gold as written.

It also drops the cases whose gold David marked as doubtful in his review of
Terra failures on rare diseases (T3, cause B), listed in T3_DOUBTFUL_GOLD.

Steps:
    py clinical_gold.py propose [--workers 6]   # LLM, cached in work/
    py clinical_gold.py build                   # writes bench/datasets/*_v2.json
"""

import argparse
import json
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from pathlib import Path
from typing import Dict, List

HERE = Path(__file__).resolve().parent
EVAL_ROOT = HERE.parents[2]
sys.path.insert(0, str(EVAL_ROOT))

from utils.llm import get_llm  # noqa: E402

DATASETS_DIR = EVAL_ROOT / "bench" / "datasets"
DATASETS = ["ddd_hpo", "ramedis_hpo", "lirical_hpo", "mygene2_hpo", "hms_hpo", "mme_hpo"]
PROPOSALS_PATH = HERE / "work" / "clinical_gold_proposals.json"
REPORT_PATH = HERE / "work" / "build_report.txt"
VERSION = "v2"
BATCH_SIZE = 25

# T3 (General/portfolio/DxGPT/research/tarea_finetuning_DxGPT.md), cause B:
# the HPO terms contradict the gold, so the case cannot be scored.
T3_DOUBTFUL_GOLD = {
    "RAMEDIS_029": "Phenylketonuria with hypertyrosinemia",
    "RAMEDIS_031": "Phenylketonuria with hypertyrosinemia",
    "RAMEDIS_123": "Phenylketonuria with hypertyrosinemia",
    "RAMEDIS_256": "Phenylketonuria with hypertyrosinemia",
    "RAMEDIS_270": "Phenylketonuria with hypertyrosinemia",
    "RAMEDIS_313": "Phenylketonuria with hypertyrosinemia",
    "RAMEDIS_610": "Phenylketonuria with abnormal tyrosine",
    "RAMEDIS_132": "Alkaptonuria with seizures and death in childhood",
    "DDD_G2P00467": "HPO terms do not match the gold",
    "DDD_G2P00757": "HPO terms do not match the gold",
    "DDD_G2P00780": "Inheritance contradicts the gold",
}

# Codes the LLM does not resolve reliably (it named ORPHA:761 "Phenylketonuria").
# Checked against ORDO (EBI OLS) and OMIM.
MANUAL_READABLE = {
    "ORPHA:761": "Immunoglobulin A vasculitis",  # ORDO Orphanet_761
    "CFM1": "Cystic fibrosis modifier 1",  # OMIM 603855, not craniofacial microsomia
}

PROMPT = """You curate the reference diagnoses of a rare-disease benchmark. The model under test only sees a list of HPO phenotype terms: no genes, no variants, no molecular or enzyme tests unless an HPO term states them.

For each reference below, return:

1. "clinical_name": the disease as a clinician would name it from the phenotype alone.
   - Remove gene symbols and "<GENE>-related", subtypes defined only by the gene or the complementation group (numbers or letters such as "Bardet-Biedl syndrome 9", "MSUD type Ia", "Leber congenital amaurosis 2", "complementation group B"), and inheritance qualifiers that only separate genetic subtypes ("autosomal recessive", "X-linked").
   - Keep subtypes that are distinct clinical or biochemical diseases with their own features: mucopolysaccharidosis types, tyrosinemia types, glycogen storage disease types, Usher syndrome type 1 vs 2, Ehlers-Danlos types. Keep onset and clinical qualifiers ("neonatal", "infantile", "with deafness").
   - For long descriptive titles, use the syndrome name if there is one (acronym or eponym), otherwise the descriptive title without the gene.
   - If the reference is an abbreviation, apply these rules to its full name ("DA8" -> "Distal arthrogryposis").
   - If the reference has no gene or genetic subtype to remove, return it unchanged.
2. "diagnosable": true if "clinical_name" is a disease or syndrome with its own clinical identity that a clinician could put in a differential from the phenotype (named syndromes, eponyms, metabolic diseases named by the enzyme or metabolite, clinically defined groups such as Bardet-Biedl syndrome, retinitis pigmentosa, hereditary spastic paraplegia, Charcot-Marie-Tooth disease, neuronal ceroid lipofuscinosis, cutis laxa). false if it is a generic phenotype or broad descriptive category (intellectual disability, developmental delay, epilepsy, developmental and epileptic encephalopathy, neurodevelopmental disorder, microcephaly, hearing loss, retinal dystrophy, short stature, congenital heart defect, "disorder") or a list of features with no syndrome name.
3. "readable_name": only when the reference is an abbreviation or a list of repeated synonyms ("DA8", "Neurofibromatosis, Type 2,Neurofibromatosis type 2"): the same entity written out in full. If you are not sure what an abbreviation means, return null. For bare codes ("ORPHA:761") return null: they are resolved by hand. Otherwise null.

References:
{items}

Return JSON only, one entry per reference, in order:
{{"items": [{{"i": 1, "clinical_name": "...", "diagnosable": true, "readable_name": null}}]}}"""


def parse_json(text: str) -> Dict:
    text = text.strip()
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end < start:
        raise ValueError("no JSON object in response")
    return json.loads(text[start:end + 1])


def load(name: str) -> List[Dict]:
    return json.loads((DATASETS_DIR / f"{name}.json").read_text(encoding="utf-8"))


def gold_codes(diag: Dict) -> str:
    codes = []
    if diag.get("omim"):
        codes.append(f"OMIM:{diag['omim']}")
    if diag.get("mondo"):
        codes.append(diag["mondo"])
    for kind in ("omim", "orpha"):
        for code in (diag.get("medical_codes") or {}).get(kind) or []:
            codes.append(f"{kind.upper()}:{code}")
    return ", ".join(dict.fromkeys(codes))


def unique_golds() -> Dict[str, str]:
    """Unique gold name -> codes, across all HPO datasets."""
    golds = {}
    for name in DATASETS:
        for case in load(name):
            for diag in case["diagnoses"]:
                golds.setdefault(diag["name"], gold_codes(diag))
    return golds


def propose_batch(llm, batch: List[tuple], attempts: int = 3) -> List[Dict]:
    items = "\n".join(
        f"{i}. {name}" + (f" [{codes}]" if codes else "") for i, (name, codes) in enumerate(batch, 1)
    )
    error = None
    for _ in range(attempts):
        try:
            data = parse_json(str(llm.generate(PROMPT.format(items=items), max_tokens=16000, temperature=0.1)))
            rows = data["items"]
            if len(rows) != len(batch) or [r.get("i") for r in rows] != list(range(1, len(batch) + 1)):
                raise ValueError(f"expected {len(batch)} items in order")
            return [dict(row, name=name) for row, (name, _) in zip(rows, batch)]
        except Exception as exc:  # retry invalid or failed calls
            error = exc
    return [{"name": name, "error": str(error)} for name, _ in batch]


def propose(args) -> None:
    proposals = {}
    if PROPOSALS_PATH.exists():
        proposals = json.loads(PROPOSALS_PATH.read_text(encoding="utf-8"))
        proposals = {k: v for k, v in proposals.items() if "error" not in v}
    golds = unique_golds()
    pending = [(name, codes) for name, codes in golds.items() if name not in proposals]
    print(f"{len(golds)} unique gold names, {len(pending)} pending")

    llm = get_llm(args.model)
    batches = [pending[i:i + BATCH_SIZE] for i in range(0, len(pending), BATCH_SIZE)]
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        for rows in executor.map(lambda b: propose_batch(llm, b), batches):
            for row in rows:
                proposals[row["name"]] = {k: v for k, v in row.items() if k not in ("name", "i")}
            PROPOSALS_PATH.parent.mkdir(exist_ok=True)
            PROPOSALS_PATH.write_text(json.dumps(proposals, indent=1, ensure_ascii=False), encoding="utf-8")

    errors = [name for name, row in proposals.items() if "error" in row]
    print(f"Saved {len(proposals)} proposals to {PROPOSALS_PATH} ({len(errors)} errors)")


def norm(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def input_terms(case: Dict) -> set:
    text = case.get("case_en") or case.get("case") or ""
    return {norm(re.sub(r"^obsolete\s+", "", term)) for term in text.split(",")}


def build(args) -> None:
    proposals = json.loads(PROPOSALS_PATH.read_text(encoding="utf-8"))
    report = [f"HPO {VERSION} build, {date.today().isoformat()}", ""]
    totals = {}
    for name in DATASETS:
        cases = load(name)
        out, stats = [], dict(cases=len(cases), excluded=0, clinical=0, same=0, not_diagnosable=0,
                              in_input=0, readable=0, missing=0)
        for case in cases:
            if case["id"] in T3_DOUBTFUL_GOLD:
                stats["excluded"] += 1
                report.append(f"{name}\t{case['id']}\texcluded\tT3 cause B: {T3_DOUBTFUL_GOLD[case['id']]}")
                continue
            case = json.loads(json.dumps(case))
            clinical = []
            for diag in case["diagnoses"]:
                proposal = proposals.get(diag["name"])
                if not proposal or "error" in proposal:
                    stats["missing"] += 1
                    continue
                readable = (MANUAL_READABLE.get(diag["name"]) or proposal.get("readable_name") or "").strip()
                if readable and norm(readable) != norm(diag["name"]):
                    diag["accepted_names"] = list(dict.fromkeys((diag.get("accepted_names") or []) + [readable]))
                    stats["readable"] += 1
                clinical_name = (proposal.get("clinical_name") or "").strip()
                if diag["name"] in MANUAL_READABLE:
                    clinical_name = ""
                if not clinical_name or norm(clinical_name) in (norm(diag["name"]), norm(readable)):
                    stats["same"] += 1
                elif not proposal.get("diagnosable"):
                    stats["not_diagnosable"] += 1
                    report.append(f"{name}\t{case['id']}\tnot_diagnosable\t{diag['name']} -> {clinical_name}")
                elif norm(clinical_name) in input_terms(case):
                    stats["in_input"] += 1
                    report.append(f"{name}\t{case['id']}\tin_input\t{diag['name']} -> {clinical_name}")
                else:
                    clinical.append({"name": clinical_name, "role": "clinical", "derived_from": diag["name"]})
            if clinical:
                stats["clinical"] += 1
                for entry in clinical:
                    report.append(f"{name}\t{case['id']}\tclinical\t{entry['derived_from']} -> {entry['name']}")
            case["diagnoses"] += clinical
            case.setdefault("metadata", {})["gold_version"] = f"hpo_{VERSION}"
            out.append(case)
        path = DATASETS_DIR / f"{name}_{VERSION}.json"
        path.write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
        totals[name] = stats
        print(f"{path.name}: {json.dumps(stats)}")

    REPORT_PATH.write_text("\n".join(report) + "\n", encoding="utf-8")
    print(f"Report: {REPORT_PATH}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("step", choices=["propose", "build"])
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--model", default="gemini-2.5-pro")
    args = parser.parse_args()
    propose(args) if args.step == "propose" else build(args)


if __name__ == "__main__":
    main()
