#!/usr/bin/env python3
"""
Harvest recent open-access case reports from PubMed Central
==========================================================

1. PubMed search: "Case Reports"[pt], PMC open access, English, Entrez date
   (first appearance in PubMed) within the window. One query per month so each
   stays under the 10,000-result limit.
2. Seeded random sample of PMIDs, PubMed metadata, a cap per journal.
3. PMC full text (JATS). Keeps CC licenses without "ND" and articles with a
   body; drops figure and table captions, which often name the diagnosis.

Output (not versioned): data-repos/raw/pmc_live/candidates.json and
search_log.json.

Usage:
    py harvest_pmc.py --start 2026-07-01 --end 2026-10-27 --sample 1600 --candidates 450
"""

import argparse
import json
import random
import re
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from collections import Counter
from datetime import date, timedelta
from pathlib import Path
from typing import Dict, List, Optional

EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
TOOL = "dxgpt-eval-narrative-v2"
REQUEST_DELAY_SECONDS = 0.4  # NCBI allows 3 requests/s without an API key
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "raw" / "pmc_live"
EXCLUDED_PUBLICATION_TYPES = {
    "Retracted Publication", "Retraction of Publication", "Erratum", "Comment",
    "Published Erratum", "Editorial", "Letter",
}
XLINK = "{http://www.w3.org/1999/xlink}"


def eutils(endpoint: str, params: Dict[str, str], retries: int = 4) -> bytes:
    query = urllib.parse.urlencode({**params, "tool": TOOL})
    url = f"{EUTILS}{endpoint}?{query}"
    for attempt in range(1, retries + 1):
        try:
            time.sleep(REQUEST_DELAY_SECONDS)
            with urllib.request.urlopen(url, timeout=60) as response:
                return response.read()
        except Exception as error:
            if attempt == retries:
                raise
            print(f"   retry {attempt}/{retries} after {type(error).__name__}: {error}")
            time.sleep(2 * attempt)
    raise RuntimeError("unreachable")


def month_windows(start: date, end: date) -> List[tuple]:
    windows = []
    current = start
    while current <= end:
        next_month = (current.replace(day=1) + timedelta(days=32)).replace(day=1)
        window_end = min(next_month - timedelta(days=1), end)
        windows.append((current, window_end))
        current = next_month
    return windows


def search_pmids(start: date, end: date) -> Dict[str, List[str]]:
    """All case-report PMIDs per month window."""
    by_window = {}
    for window_start, window_end in month_windows(start, end):
        term = (
            '"Case Reports"[pt] AND "pubmed pmc open access"[filter] AND english[lang] AND '
            f'{window_start:%Y/%m/%d}:{window_end:%Y/%m/%d}[edat]'
        )
        result = json.loads(eutils("esearch.fcgi", {
            "db": "pubmed", "term": term, "retmax": "9999", "retmode": "json",
        }))["esearchresult"]
        key = f"{window_start:%Y-%m-%d}..{window_end:%Y-%m-%d}"
        by_window[key] = result["idlist"]
        print(f"   {key}: {result['count']} case reports, {len(result['idlist'])} ids")
    return by_window


def text_of(element: Optional[ET.Element]) -> str:
    return re.sub(r"\s+", " ", "".join(element.itertext())).strip() if element is not None else ""


def fetch_pubmed_metadata(pmids: List[str]) -> List[Dict]:
    records = []
    for i in range(0, len(pmids), 200):
        root = ET.fromstring(eutils("efetch.fcgi", {
            "db": "pubmed", "id": ",".join(pmids[i:i + 200]), "retmode": "xml",
        }))
        for article in root.findall("PubmedArticle"):
            citation = article.find("MedlineCitation")
            pmc = article.find(".//ArticleIdList/ArticleId[@IdType='pmc']")
            types = [text_of(t) for t in citation.findall(".//PublicationTypeList/PublicationType")]
            entrez = article.find(".//PubmedData/History/PubMedPubDate[@PubStatus='entrez']")
            records.append({
                "pmid": text_of(citation.find("PMID")),
                "pmcid": text_of(pmc) if pmc is not None else None,
                "journal": text_of(citation.find(".//Journal/Title")),
                "title": text_of(citation.find(".//ArticleTitle")),
                "publication_types": types,
                "entrez_date": (
                    f"{text_of(entrez.find('Year'))}-{int(text_of(entrez.find('Month'))):02d}-"
                    f"{int(text_of(entrez.find('Day'))):02d}" if entrez is not None else None
                ),
            })
        print(f"   PubMed metadata {min(i + 200, len(pmids))}/{len(pmids)}")
    return records


def license_of(article: ET.Element) -> Dict[str, str]:
    license_element = article.find(".//permissions/license")
    if license_element is None:
        return {"license": "", "license_url": ""}
    url = license_element.get(f"{XLINK}href") or ""
    ref = license_element.find("{http://www.niso.org/schemas/ali/1.0/}license_ref")
    if not url and ref is not None:
        url = text_of(ref)
    match = re.search(r"creativecommons\.org/licenses/([a-z-]+)/([\d.]+)", url)
    name = f"CC {match.group(1).upper()} {match.group(2)}" if match else text_of(license_element)[:120]
    return {"license": name, "license_url": url}


def body_sections(body: ET.Element) -> List[Dict[str, str]]:
    """Section titles and paragraphs; captions of figures and tables are skipped."""
    for tag in ("fig", "table-wrap", "fig-group", "supplementary-material"):
        for parent in body.iter():
            for child in list(parent):
                if child.tag == tag:
                    parent.remove(child)
    sections = []
    for sec in body.iter("sec"):
        title = text_of(sec.find("title"))
        paragraphs = [text_of(p) for p in sec.findall("p")]
        if paragraphs:
            sections.append({"title": title, "text": "\n".join(p for p in paragraphs if p)})
    if not sections:
        paragraphs = [text_of(p) for p in body.findall("p")]
        if paragraphs:
            sections.append({"title": "", "text": "\n".join(paragraphs)})
    return sections


def fetch_pmc_full_text(records: List[Dict]) -> List[Dict]:
    by_pmcid = {r["pmcid"].replace("PMC", ""): r for r in records}
    ids = list(by_pmcid)
    kept = []
    for i in range(0, len(ids), 20):
        root = ET.fromstring(eutils("efetch.fcgi", {"db": "pmc", "id": ",".join(ids[i:i + 20])}))
        for article in root.iter("article"):
            pmc_id = article.find(".//article-meta/article-id[@pub-id-type='pmcid']")
            if pmc_id is None:
                pmc_id = article.find(".//article-meta/article-id[@pub-id-type='pmc']")
            key = text_of(pmc_id).replace("PMC", "") if pmc_id is not None else ""
            record = by_pmcid.get(key)
            body = article.find("body")
            if record is None or body is None:
                continue
            record = {
                **record,
                "article_type": article.get("article-type", ""),
                "abstract": text_of(article.find(".//article-meta/abstract")),
                "sections": body_sections(body),
                **license_of(article),
            }
            if record["sections"]:
                kept.append(record)
        print(f"   PMC full text {min(i + 20, len(ids))}/{len(ids)} (kept {len(kept)})")
    return kept


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", default="2026-07-01")
    parser.add_argument("--end", default="2026-10-27")
    parser.add_argument("--sample", type=int, default=1600, help="PMIDs sampled before filtering")
    parser.add_argument("--candidates", type=int, default=450, help="Articles to download in full")
    parser.add_argument("--max-per-journal", type=int, default=6)
    parser.add_argument("--seed", type=int, default=29)
    args = parser.parse_args()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    rng = random.Random(args.seed)

    print("1. PubMed search")
    by_window = search_pmids(date.fromisoformat(args.start), date.fromisoformat(args.end))
    all_pmids = sorted({pmid for ids in by_window.values() for pmid in ids})
    sampled = rng.sample(all_pmids, min(args.sample, len(all_pmids)))

    print("2. Metadata and journal cap")
    metadata = fetch_pubmed_metadata(sampled)
    eligible = [
        r for r in metadata
        if r["pmcid"] and "Case Reports" in r["publication_types"]
        and not EXCLUDED_PUBLICATION_TYPES & set(r["publication_types"])
        and r["entrez_date"] and r["entrez_date"] >= args.start
    ]
    rng.shuffle(eligible)
    per_journal = Counter()
    selected = []
    for record in eligible:
        if per_journal[record["journal"]] >= args.max_per_journal:
            continue
        per_journal[record["journal"]] += 1
        selected.append(record)
        if len(selected) == args.candidates:
            break
    print(f"   {len(eligible)} eligible, {len(selected)} selected from {len(per_journal)} journals")

    print("3. PMC full text")
    articles = fetch_pmc_full_text(selected)
    no_derivatives = [a for a in articles if "-ND" in a["license"].upper() or "NODERIVATIVES" in a["license"].upper()]
    unknown_license = [a for a in articles if not a["license"].startswith("CC ")]
    candidates = [a for a in articles if a not in no_derivatives and a not in unknown_license]

    (OUTPUT_DIR / "candidates.json").write_text(json.dumps(candidates, ensure_ascii=False, indent=1), encoding="utf-8")
    log = {
        "run_date": date.today().isoformat(),
        "window": [args.start, args.end],
        "seed": args.seed,
        "case_reports_by_month": {k: len(v) for k, v in by_window.items()},
        "sampled": len(sampled),
        "eligible_after_metadata": len(eligible),
        "selected_with_journal_cap": len(selected),
        "with_full_text": len(articles),
        "dropped_no_derivatives": len(no_derivatives),
        "dropped_unknown_license": len(unknown_license),
        "candidates": len(candidates),
        "licenses": Counter(a["license"] for a in candidates),
    }
    (OUTPUT_DIR / "search_log.json").write_text(json.dumps(log, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(log, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
