"""PubMed search for arm C, without leakage from the narrative_v2 cases.

The live cases of narrative_v2 are case reports that entered PubMed from
1-jul-2026. Searches are limited to articles published up to MAX_DATE, and
the case's own PMID is excluded as well.
"""

import json
import re
import threading
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional

EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
TOOL = "dxgpt-eval-agentic-poc"
MAX_DATE = "2026/06/30"
MIN_INTERVAL_SECONDS = 0.4  # NCBI allows 3 requests/s without an API key
_lock = threading.Lock()
_last_call = [0.0]


def _get(endpoint: str, params: Dict[str, str], retries: int = 4) -> bytes:
    url = f"{EUTILS}{endpoint}?{urllib.parse.urlencode({**params, 'tool': TOOL})}"
    for attempt in range(1, retries + 1):
        with _lock:  # one request at a time across worker threads
            wait = MIN_INTERVAL_SECONDS - (time.time() - _last_call[0])
            if wait > 0:
                time.sleep(wait)
            _last_call[0] = time.time()
        try:
            with urllib.request.urlopen(url, timeout=60) as response:
                return response.read()
        except Exception:
            if attempt == retries:
                raise
            time.sleep(2 * attempt)
    raise RuntimeError("unreachable")


def _text(element: Optional[ET.Element]) -> str:
    return re.sub(r"\s+", " ", "".join(element.itertext())).strip() if element is not None else ""


def search(query: str, exclude_pmids: List[str] = (), retmax: int = 5) -> List[Dict]:
    """Title and abstract excerpt of the top PubMed hits published up to MAX_DATE."""
    result = json.loads(_get("esearch.fcgi", {
        "db": "pubmed", "term": query, "retmode": "json", "retmax": str(retmax + len(exclude_pmids)),
        "sort": "relevance", "datetype": "pdat", "mindate": "1900/01/01", "maxdate": MAX_DATE,
    }))["esearchresult"]
    pmids = [p for p in result.get("idlist", []) if p not in set(exclude_pmids)][:retmax]
    if not pmids:
        return []
    root = ET.fromstring(_get("efetch.fcgi", {"db": "pubmed", "id": ",".join(pmids), "retmode": "xml"}))
    articles = []
    for article in root.findall("PubmedArticle"):
        abstract = _text(article.find(".//Abstract"))
        articles.append({
            "pmid": _text(article.find(".//PMID")),
            "title": _text(article.find(".//ArticleTitle")),
            "abstract": abstract[:700] + ("…" if len(abstract) > 700 else ""),
        })
    return articles
