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

v3 (10-nov-2026): David reviewed a random sample of the v2 names (task 3) and
about half of the decisions were wrong or improvable. His criteria are now in
the prompt, his answers override the LLM for those golds (REVIEWED_CLINICAL),
and the names come from Gemini 3.8 Flash: Google retires Gemini 2.5 Pro on
1-dec-2026.

Steps:
    py clinical_gold.py check                   # prompt vs David's answers (cents)
    py clinical_gold.py propose [--workers 6]   # LLM, cached in work/
    py clinical_gold.py build                   # writes bench/datasets/*_v3.json
"""

import argparse
import json
import re
import sys
import threading
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
PROPOSALS_PATH = HERE / "work" / "clinical_gold_proposals_v3.json"  # v2: clinical_gold_proposals.json
REPORT_PATH = HERE / "work" / "build_report_v3.txt"
VERSION = "v3"
BATCH_SIZE = 25
# USD per million tokens (input, output including reasoning), as in pipeline_v5/main/evaluator.py
PRICES_PER_MILLION = {"gemini-3.8-flash": (0.75, 3.75), "gemini-2.5-pro": (1.25, 10.0)}

# T3 (General/portfolio/DxGPT/research/tarea_finetuning_DxGPT.md), cause B:
# the HPO terms contradict the gold, so the case cannot be scored. The 7
# phenylketonurias with hypertyrosinemia came back in v3: in task 3 (block G)
# David ruled that the pattern is coding noise and all 115 such cases stay.
T3_DOUBTFUL_GOLD = {
    "RAMEDIS_132": "Alkaptonuria with seizures and death in childhood",
    "DDD_G2P00467": "HPO terms do not match the gold",
    "DDD_G2P00757": "HPO terms do not match the gold",
    "DDD_G2P00780": "Inheritance contradicts the gold",
}

# Codes the LLM does not resolve reliably (it named ORPHA:761 "Phenylketonuria").
# Checked against ORDO (EBI OLS) and OMIM. Also typos in the gold name.
MANUAL_READABLE = {
    "ORPHA:761": "Immunoglobulin A vasculitis",  # ORDO Orphanet_761
    "CFM1": "Cystic fibrosis modifier 1",  # OMIM 603855, not craniofacial microsomia
    "HIBCH-related 3-hydroxyisobutryl-CoA hydrolase deficiency":
        "HIBCH-related 3-hydroxyisobutyryl-CoA hydrolase deficiency",  # David, task 3
}

# David's answers on the random sample of task 3 (blocks A-C, 10-nov-2026): the
# gene-free name for each gold, or None when there is none to add (what is left
# is a generic trait, or the subtype is a disease of its own). They override the
# LLM for every case with that gold, and `check` measures the prompt against
# them. Left out: COX15 Leigh (he asks a clinician) and IFT43 cranioectodermal
# dysplasia (his comment there belongs to the DOCK8 case).
REVIEWED_CLINICAL = {
    # A. DDD
    "CYFIP2-related epileptic encephalopathy, early infantile": "Epileptic encephalopathy, early infantile",
    "PRRX1-related agnathia-otocephaly complex": "Agnathia-otocephaly complex",
    "KLF1-related anemia, dyserythropoietic congenital": "Congenital dyserythropoietic anemia type IV",
    "KIF7-related acrocallosal syndrome": "Acrocallosal syndrome",
    "FKRP-related congenital alpha-dystroglycanopathy with brain and eye anomalies":
        "Congenital alpha-dystroglycanopathy with brain and eye anomalies",
    "SLC52A2-related Brown-Vialetto-Van Laere syndrome": "Brown-Vialetto-Van Laere syndrome",
    "PLOD2-related Bruck syndrome": "Bruck syndrome",
    "MAOA-related Brunner syndrome": "Brunner syndrome",
    "NAGA-related Kanzaki disease": "Kanzaki disease",
    "DOCK8-related hyper-IgE syndrome with recurrent infections": "Autosomal recessive hyper-IgE syndrome",
    "TP63-related limb-mammary syndrome": "Limb-mammary syndrome",
    "ATRX-related alpha-thalassemia intellectual developmental disorder syndrome non-deletion type":
        "Alpha-thalassemia intellectual developmental disorder syndrome, non-deletion type",
    "HIBCH-related 3-hydroxyisobutryl-CoA hydrolase deficiency": "3-hydroxyisobutyryl-CoA hydrolase deficiency",
    "ASAH1-related Farber lipogranulomatosis": "Farber lipogranulomatosis",
    "INPP5K-related muscular dystrophy, congenital, with cataracts, and intellectual disability":
        "Muscular dystrophy, congenital, with cataracts, and intellectual disability",
    "GNAI3-related auriculocondylar syndrome": "Auriculocondylar syndrome",
    "SUZ12-related Weaver-like overgrowth syndrome": "Imagawa-Matsumoto syndrome",
    "PEX7-related peroxisome biogenesis disorder complementation group 11": "Rhizomelic chondrodysplasia punctata",
    "TAT-related tyrosinemia": "Tyrosinemia type II",
    "SOX9-related campomelic dysplasia": "Campomelic dysplasia",
    "GNS-related mucopolysaccharidosis": "Mucopolysaccharidosis type IIID",
    "MMP13-related spondyloepimetaphyseal dysplasia, Missouri type": "Spondyloepimetaphyseal dysplasia, Missouri type",
    "EZH2-related Weaver syndrome": "Weaver syndrome",
    # B. Other datasets, a genetic subtype removed
    "Arthrogryposis, Distal, Type 1A": "Distal arthrogryposis type 1",
    "Autosomal recessive Robinow syndrome": None,
    "Tyrosinemia, Type Iii": None,
    "Autosomal dominant dopa-responsive dystonia": None,
    "PMM2-CDG": "Congenital disorder of glycosylation type Ia",
    "Perrault Syndrome 1": "Perrault syndrome",
    "UMOD-related autosomal dominant tubulointerstitial kidney disease": "Autosomal dominant tubulointerstitial kidney disease",
    "Marfan syndrome type 1": "Marfan syndrome",
    # C. Not added in v2 because a generic trait would be left
    "ZMYND11-related intellectual disability": None,
    "CLCN4-related infantile epileptic encephalopathy and/or intellectual disability": "Raynaud-Claes syndrome",
    "TET3-related DNA demethylation disorder": "Beck-Fahrner syndrome",
    "FTSJ1-related intellectual developmental disorder": None,
    "CWC27-related retinitis pigmentosa, short stature, skeletal anomalies and intellectual disability with or without ectodermal features":
        "Retinitis pigmentosa, short stature, skeletal anomalies and intellectual disability with or without ectodermal features",
    "SMARCC2-related syndromic intellectual disability and developmental delay": "Coffin-Siris syndrome",
    "SOX6-related neurodevelopmental syndrome": "Tolchin-Le Caignec syndrome",
    "CRYBA1-related cataract": None,
    "RTN4IP1-related optic atrophy with or without ataxia, intellectual developmental disorder, and seizures": None,
    "HACE1-related disorder": "Spastic paraplegia and psychomotor retardation with or without seizures",
}

# Synonyms David gave for some of those names
REVIEWED_SYNONYMS = {
    "Alpha-thalassemia intellectual developmental disorder syndrome, non-deletion type": ["ATR-X syndrome"],
    "Tyrosinemia type II": ["Richner-Hanhart syndrome"],
}

# Rule for T3 cause C that David wrote in task 3, not applied yet: the term
# lists wait for his OK. A case is excluded when no specific term is left after
# removing the terms that do not describe the patient and the generic
# neurodevelopmental ones. In RAMEDIS, deaths and the analytes that are not the
# gold's marker are coding noise (task 3, block G).
NOT_PATIENT_TERMS = [r"inheritance$", r"^phenotypic variability$", r"^obsolete "]
GENERIC_NEURO_TERMS = [
    r"intellectual disability", r"developmental delay", r"^motor delay$",
    r"^delayed (speech and language|gross motor|fine motor|social) development$", r"language delay$",
    r"^speech delay$", r"^seizures?$", r"hypotonia$", r"^autism$", r"^autistic behavior$", r"^eeg abnormality$",
    r"^abnormality of ", r"^abnormality$",
]
RAMEDIS_NOISE_TERMS = [r"^death in ", r"^neonatal death$", r"^hypertyrosinemia$", r"^hyperphenylalaninemia$",
                       r"^abnormal circulating porphyrin concentration$"]
RAMEDIS_MARKERS = {"phenylketonuria": "hyperphenylalaninemia", "tyrosinemia": "hypertyrosinemia"}


def specific_terms(case: Dict, dataset: str) -> List[str]:
    """The HPO terms of a case that count for the cause C rule."""
    golds = [norm(d["name"]) for d in case["diagnoses"] if d.get("role") != "clinical"]
    kept = []
    for raw in (case.get("case_en") or case.get("case") or "").split(","):
        term = raw.strip().lower()
        if not term or any(re.search(p, term) for p in NOT_PATIENT_TERMS + GENERIC_NEURO_TERMS):
            continue
        if any(norm(term) in gold or gold in norm(term) for gold in golds):
            continue
        if dataset == "ramedis_hpo" and any(re.search(p, term) for p in RAMEDIS_NOISE_TERMS) and not any(
                disease in gold and term == marker for disease, marker in RAMEDIS_MARKERS.items() for gold in golds):
            continue
        kept.append(raw.strip())
    return kept

PROMPT = """You curate the reference diagnoses of a rare-disease benchmark. The model under test only sees a list of HPO phenotype terms: no genes, no variants, no molecular or enzyme tests unless an HPO term states them.

For each reference below, return:

1. "clinical_name": the specific disease a clinician could name from the phenotype alone, without the gene.
   - Remove gene symbols and "<GENE>-related", and subtypes that only the gene or the complementation group defines: numbers or letters such as "Bardet-Biedl syndrome 9", "Joubert syndrome 5", "Leber congenital amaurosis 2", "MSUD type Ia", "complementation group B". When the types of a named disease are numbered by gene, use the name without the number.
   - Do not end with an umbrella term that covers several distinct diseases. If removing the gene leaves one, give the name of this gene's disease that does not need the gene: a clinical or biochemical subtype named before the gene was known, or its eponym or syndrome name ("GALNS-related mucopolysaccharidosis" -> "Mucopolysaccharidosis type IVA"; "NSD1-related overgrowth syndrome" -> "Sotos syndrome"). Only give such a name if you are sure it is this gene's disease.
   - Keep subtypes that are distinct clinical or biochemical diseases (mucopolysaccharidosis, tyrosinemia, glycogen storage disease and Ehlers-Danlos types; Usher syndrome type 1 vs 2), qualifiers that do not depend on the gene ("non-deletion type", "with deafness", "neonatal", "infantile"), and inheritance qualifiers when the dominant and recessive forms are clinically distinct diseases ("Polycystic kidney disease, autosomal recessive"). Remove inheritance qualifiers that only separate genetic subtypes of the same disease.
   - For long descriptive titles, use the syndrome name if there is one (acronym or eponym), otherwise the descriptive title without the gene.
   - If the reference is an abbreviation, apply these rules to its full name ("DA8" -> "Distal arthrogryposis").
   - Correct obvious misspellings of the disease name.
   - If the reference has no gene or genetic subtype to remove, return it unchanged.
2. "diagnosable": true if "clinical_name" is a disease or syndrome with its own clinical identity that a clinician could put in a differential from the phenotype: named syndromes and eponyms, metabolic diseases named by the enzyme or metabolite, clinically defined groups (Bardet-Biedl syndrome, retinitis pigmentosa, hereditary spastic paraplegia, Charcot-Marie-Tooth disease, neuronal ceroid lipofuscinosis, cutis laxa), and descriptive titles with two or more required features ("Intellectual developmental disorder with cardiac defects and dysmorphic facies"). false if it is a generic phenotype or broad descriptive category (intellectual disability, developmental delay, epilepsy, developmental and epileptic encephalopathy, neurodevelopmental disorder, microcephaly, hearing loss, retinal dystrophy, cataract, short stature, congenital heart defect, "disorder"), a mechanism rather than a disease ("chromatin remodeling disorder"), one required feature with optional ones ("hearing loss with or without vestibular dysfunction"), or features joined by "and/or". Before answering false, check whether this gene's disease has an eponym or syndrome name that does not mention the gene: if it does, return that name as "clinical_name" and true.
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


USAGE = {"input": 0, "output": 0}
USAGE_LOCK = threading.Lock()


def add_usage(llm) -> None:
    usage = llm.get_last_usage() or {}
    with USAGE_LOCK:
        USAGE["input"] += usage.get("input_tokens", 0)
        USAGE["output"] += usage.get("output_tokens", 0) + usage.get("reasoning_tokens", 0)


def usage_cost(model: str) -> str:
    price_in, price_out = PRICES_PER_MILLION.get(model, (0, 0))
    cost = (USAGE["input"] * price_in + USAGE["output"] * price_out) / 1e6
    return f"{USAGE['input']} input and {USAGE['output']} output tokens, about {cost:.2f} $"


def propose_batch(llm, batch: List[tuple], attempts: int = 3, thinking: str = None) -> List[Dict]:
    items = "\n".join(
        f"{i}. {name}" + (f" [{codes}]" if codes else "") for i, (name, codes) in enumerate(batch, 1)
    )
    options = {"thinking_level": thinking} if thinking else {}
    error = None
    for _ in range(attempts):
        try:
            text = llm.generate(PROMPT.format(items=items), max_tokens=16000, temperature=0.1, **options)
            add_usage(llm)
            data = parse_json(str(text))
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
        for rows in executor.map(lambda b: propose_batch(llm, b, thinking=args.thinking), batches):
            for row in rows:
                proposals[row["name"]] = {k: v for k, v in row.items() if k not in ("name", "i")}
            PROPOSALS_PATH.parent.mkdir(exist_ok=True)
            PROPOSALS_PATH.write_text(json.dumps(proposals, indent=1, ensure_ascii=False), encoding="utf-8")

    errors = [name for name, row in proposals.items() if "error" in row]
    print(f"Saved {len(proposals)} proposals to {PROPOSALS_PATH} ({len(errors)} errors)")
    print(f"{args.model}: {usage_cost(args.model)}")


def check(args) -> None:
    """The prompt on the golds David reviewed, without his overrides, against his answers."""
    golds = unique_golds()
    names = [name for name in REVIEWED_CLINICAL if name in golds]
    llm = get_llm(args.model)
    batches = [[(name, golds[name]) for name in names[i:i + BATCH_SIZE]] for i in range(0, len(names), BATCH_SIZE)]
    agree = 0
    for batch in batches:
        for row in propose_batch(llm, batch, thinking=args.thinking):
            expected = REVIEWED_CLINICAL[row["name"]]
            got = (row.get("clinical_name") or "").strip() if row.get("diagnosable") else ""
            if norm(got) == norm(row["name"]):
                got = ""  # unchanged: there is no gene-free gold to add
            same = norm(got) == norm(expected or "")
            agree += same
            print(f"{'  ' if same else 'XX'} {row['name']}\n     David: {expected}\n     LLM:   {got or None}"
                  + (f"  ({row['error']})" if "error" in row else ""))
    print(f"\n{agree}/{len(names)} identical. Read the XX lines: another wording of the same name is a match.")
    print(f"{args.model}: {usage_cost(args.model)}")


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
                proposal = proposals.get(diag["name"]) or {}
                if (not proposal or "error" in proposal) and diag["name"] not in REVIEWED_CLINICAL:
                    stats["missing"] += 1
                    continue
                readable = (MANUAL_READABLE.get(diag["name"]) or proposal.get("readable_name") or "").strip()
                if readable and norm(readable) != norm(diag["name"]):
                    diag["accepted_names"] = list(dict.fromkeys((diag.get("accepted_names") or []) + [readable]))
                    stats["readable"] += 1
                clinical_name = (proposal.get("clinical_name") or "").strip()
                diagnosable = proposal.get("diagnosable")
                if diag["name"] in MANUAL_READABLE:
                    clinical_name = ""
                if diag["name"] in REVIEWED_CLINICAL:  # David's answer wins over the LLM
                    clinical_name, diagnosable = REVIEWED_CLINICAL[diag["name"]] or "", True
                if not clinical_name or norm(clinical_name) in (norm(diag["name"]), norm(readable)):
                    stats["same"] += 1
                elif not diagnosable:
                    stats["not_diagnosable"] += 1
                    report.append(f"{name}\t{case['id']}\tnot_diagnosable\t{diag['name']} -> {clinical_name}")
                elif norm(clinical_name) in input_terms(case):
                    stats["in_input"] += 1
                    report.append(f"{name}\t{case['id']}\tin_input\t{diag['name']} -> {clinical_name}")
                else:
                    entry = {"name": clinical_name, "role": "clinical", "derived_from": diag["name"]}
                    if clinical_name in REVIEWED_SYNONYMS:
                        entry["accepted_names"] = REVIEWED_SYNONYMS[clinical_name]
                    clinical.append(entry)
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
    parser.add_argument("step", choices=["check", "propose", "build"])
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--model", default="gemini-3.8-flash")
    parser.add_argument("--thinking", default="low", help="Gemini thinking_level; empty to leave it to the model")
    args = parser.parse_args()
    {"check": check, "propose": propose, "build": build}[args.step](args)


if __name__ == "__main__":
    main()
