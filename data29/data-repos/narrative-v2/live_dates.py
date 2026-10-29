#!/usr/bin/env python3
"""
Which live cases each model could have seen in training
=======================================================

The live block is selected by entrez_date (first appearance in PubMed), but
most journals publish the article online days or weeks before. This script
fetches the PubMed dates of every live case and takes the first public one:
electronic publication (ArticleDate), entrez, pubmed or PMC release. A date
earlier than the acceptance date is an issue date or a placeholder and is
ignored.

A case is unseen by a model when its first public date is after the last day
of the model's cutoff month (model_cutoffs.yaml).

Output (not versioned): work/live_dates.json, one entry per live case with
its dates and the models that may have seen it.

Usage:
    py live_dates.py [--dataset bench/datasets/narrative_v2.json]
"""

import argparse
import calendar
import json
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, Optional

import yaml

HERE = Path(__file__).resolve().parent
EVAL_ROOT = HERE.parents[2]
CUTOFFS_PATH = HERE / "model_cutoffs.yaml"
OUTPUT_PATH = HERE / "work" / "live_dates.json"
EFETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
PUBLIC_DATES = ("article_date", "entrez", "pubmed", "pmc-release")


def ymd(node) -> Optional[str]:
    try:
        return f"{int(node.findtext('Year')):04d}-{int(node.findtext('Month')):02d}-{int(node.findtext('Day')):02d}"
    except (TypeError, ValueError):
        return None


def fetch_dates(pmids) -> Dict[str, Dict[str, str]]:
    data = urllib.parse.urlencode({"db": "pubmed", "id": ",".join(pmids), "retmode": "xml",
                                   "tool": "dxgpt-eval"}).encode()
    root = ET.fromstring(urllib.request.urlopen(EFETCH_URL, data=data, timeout=120).read())
    dates = {}
    for article in root.findall(".//PubmedArticle"):
        pmid = article.findtext(".//MedlineCitation/PMID")
        found = {}
        for node in article.findall(".//Article/ArticleDate[@DateType='Electronic']"):
            found["article_date"] = ymd(node)
        for node in article.findall(".//PubmedData/History/PubMedPubDate"):
            found[node.get("PubStatus")] = ymd(node)
        dates[pmid] = {k: v for k, v in found.items() if v}
    return dates


def cutoff_end(month: str) -> str:
    year, mon = (int(x) for x in str(month).split("-"))
    return f"{year:04d}-{mon:02d}-{calendar.monthrange(year, mon)[1]:02d}"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", default="bench/datasets/narrative_v2.json")
    args = parser.parse_args()

    cases = json.loads((EVAL_ROOT / args.dataset).read_text(encoding="utf-8"))
    live = [c for c in cases if c["metadata"]["block"] == "live"]
    models = yaml.safe_load(CUTOFFS_PATH.read_text(encoding="utf-8"))["models"]
    ends = {name: cutoff_end(info["cutoff"]) for name, info in models.items()}
    dates = fetch_dates([c["metadata"]["pmid"] for c in live])

    rows = {}
    for case in live:
        found = dates.get(case["metadata"]["pmid"], {})
        accepted = found.get("accepted", "")
        public = [found[k] for k in PUBLIC_DATES if found.get(k, "") >= accepted and found.get(k)]
        public = public or [case["metadata"]["entrez_date"]]
        first_public = min(public)
        rows[case["id"]] = {
            "entrez_date": case["metadata"]["entrez_date"],
            "first_public_date": first_public,
            "dates": found,
            "maybe_seen_by": [name for name, end in ends.items() if first_public <= end],
        }

    OUTPUT_PATH.parent.mkdir(exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(rows, indent=1), encoding="utf-8")

    print(f"{len(live)} live cases, PubMed dates for {len(dates)}")
    print("| Modelo | Corte | live sin ver (entrez_date) | live sin ver (primera publicación) |")
    print("|---|---|---:|---:|")
    for name, end in ends.items():
        by_entrez = sum(r["entrez_date"] > end for r in rows.values())
        by_public = sum(r["first_public_date"] > end for r in rows.values())
        print(f"| {name} | {models[name]['cutoff']} | {by_entrez} de {len(rows)} | {by_public} de {len(rows)} |")
    print(f"Saved {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
