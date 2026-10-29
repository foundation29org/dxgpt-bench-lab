#!/usr/bin/env python3
"""
Arm C — verification with sources
=================================

Two calls to the production model around two tools:

1. The model extracts the case findings as HPO term labels and writes two
   PubMed queries from the most distinctive findings.
2. Tools, deterministic:
   - HPO (hpo_tools.py): the rare diseases whose annotations best match the
     findings, and the phenotype profile of each current hypothesis;
   - PubMed (pubmed_tools.py): titles and abstracts published up to
     30-jun-2026, excluding the case's own article.
3. The model revises its differential with that evidence.

With --base sol, gpt-6.1-sol does both steps on its own list.

Usage:
    py arm_c_sources.py [--base terra|sol] [--limit N] [--workers 8]
"""

import argparse
from typing import Dict, List

from hpo_tools import HPO
from poc_common import BASE_MODELS, Model, arm_id, clean_diagnoses, load_lists, ranked_names, run_arm, write_arm
from pubmed_tools import search

EXTRACT_PROMPT = """From the case below, extract:
- "findings": up to 20 clinical findings present in the patient, each written as a Human Phenotype Ontology term label in English (for example "Seizure", "Hepatomegaly", "Proteinuria"). Include symptoms, signs, and laboratory and imaging abnormalities. Do not include diagnoses.
- "queries": two PubMed search queries of 3 to 5 words, each combining the most distinctive findings in plain medical terms, to look for diseases with this presentation. Do not include diagnosis names, laboratory marker names or immunostains.

Return JSON only: {{"findings": ["..."], "queries": ["...", "..."]}}

Case:
{case}"""

REVISE_PROMPT = """You are an experienced diagnostician. Revise the differential diagnosis for this case with the evidence gathered below.

Case:
{case}

Current differential, most likely first, with the HPO rare-disease database profile when the disease is in it:
{differential}

Rare diseases whose HPO annotations best match the case findings (automated match, may be noisy):
{matches}

Literature retrieved with the case findings (PubMed titles and abstract excerpts):
{literature}

Instructions:
- Check each diagnosis against the findings. A typical finding that is not reported weighs against a diagnosis only if it would usually be reported.
- Add a diagnosis from the rare-disease matches or the literature only if it explains the key findings better than the current ones.
- Common diseases are often missing from the HPO database; that is not evidence against them.

Return the final differential with at most 5 diagnoses, most likely first, with standard medical names.
Return JSON only: {{"diagnoses": ["...", "..."]}}"""


MIN_MAPPED_FINDINGS = 3  # fewer mapped terms give near-random phenotype matches
MIN_MATCHED_PER_DISEASE = 2


def search_with_fallback(query: str, exclude: List[str]) -> List[Dict]:
    """Drop the last words of a query that finds nothing, down to 3 words."""
    words = query.split()
    while True:
        articles = search(" ".join(words), exclude_pmids=exclude, retmax=4)
        if articles or len(words) <= 3:
            return articles
        words = words[:-1]


def describe_differential(hpo: HPO, names: List[str], case_terms: List[str]) -> str:
    lines = []
    for i, name in enumerate(names, start=1):
        disease = hpo.find_disease(name)
        if disease is None:
            lines.append(f"{i}. {name} — not in the HPO database")
            continue
        profile = hpo.profile(disease, case_terms, top=8)
        explains = ", ".join(profile["case_findings_it_explains"]) or "none of the extracted findings"
        typical = ", ".join(profile["typical_findings_not_reported"]) or "—"
        lines.append(f"{i}. {name} — HPO: explains {explains}; typical findings not reported: {typical}")
    return "\n".join(lines) or "(empty)"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--base", default="terra", choices=list(BASE_MODELS),
                        help="Model whose list is revised; it also runs both steps")
    args = parser.parse_args()

    name = arm_id("arm_c_sources", args.base)
    base = list(load_lists(args.base).values())[: args.limit]
    print("   loading HPO...")
    hpo = HPO()
    model = Model(BASE_MODELS[args.base], "low")

    def worker(case: Dict) -> Dict:
        extracted = model.ask_json(EXTRACT_PROMPT.format(case=case["case"]))
        findings = [str(f) for f in extracted.get("findings") or []][:20]
        terms = [t for t in (hpo.to_term(f) for f in findings) if t]
        matches = []
        if len(set(terms)) >= MIN_MAPPED_FINDINGS:
            matches = [m for m in hpo.rank_diseases(terms, top=10)
                       if len(m["matched_findings"]) >= MIN_MATCHED_PER_DISEASE]

        own_pmid = (case.get("metadata") or {}).get("pmid")
        literature = []
        for query in [str(q) for q in extracted.get("queries") or []][:2]:
            literature += search_with_fallback(query, [own_pmid] if own_pmid else [])
        unique = {article["pmid"]: article for article in literature}.values()

        names = ranked_names(case)
        prompt = REVISE_PROMPT.format(
            case=case["case"],
            differential=describe_differential(hpo, names, terms),
            matches="\n".join(f"{i}. {m['disease']} (matched: {', '.join(m['matched_findings'])})"
                              for i, m in enumerate(matches, start=1)) or "(too few findings mapped to HPO for a reliable match)",
            literature="\n".join(f"- {a['title']} {a['abstract']}" for a in unique) or "(nothing found)",
        )
        answer = model.ask_json(prompt)
        return {
            "diagnoses": clean_diagnoses(answer.get("diagnoses")),
            "base": names,
            "findings": findings,
            "hpo_terms": [hpo.names[t] for t in terms],
            "phenotype_matches": [m["disease"] for m in matches],
            "queries": extracted.get("queries"),
            "literature": [{"pmid": a["pmid"], "title": a["title"]} for a in unique],
        }

    outputs = run_arm(name, base, worker, args.workers)
    write_arm(name, base, outputs, model.totals())


if __name__ == "__main__":
    main()
