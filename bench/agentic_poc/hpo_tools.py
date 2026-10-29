"""Local HPO tools for arm C: findings to HPO terms, phenotype matching, disease profiles.

Data: hp.obo and phenotype.hpoa (HPO release 2026-02-16) in
data29/data-repos/raw/ddd_g2p/. Only phenotypic-abnormality annotations
(aspect P) without the NOT qualifier are used.

Phenotype matching is a simple information-content score, in the spirit of
Phenomizer: a disease scores the information content of every case term that
it carries (the term or a more specific one in its annotations).
"""

import math
import re
from collections import defaultdict
from difflib import SequenceMatcher
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from poc_common import EVAL_ROOT

HPO_DIR = EVAL_ROOT / "data29" / "data-repos" / "raw" / "ddd_g2p"
STOPWORDS = {"of", "the", "and", "with", "in", "to", "a", "an", "or", "due", "type"}
# Diseases are written as "Wilson disease", "WILSON DISEASE" or "Wilson's disease".
FREQUENCY_WORDS = {
    "HP:0040280": "obligate", "HP:0040281": "very frequent", "HP:0040282": "frequent",
    "HP:0040283": "occasional", "HP:0040284": "very rare", "HP:0040285": "excluded",
}


def is_frequent(frequency: str) -> bool:
    """Obligate or very frequent, or at least half of the patients ("4/5", "60%")."""
    if FREQUENCY_WORDS.get(frequency) in ("obligate", "very frequent"):
        return True
    fraction = re.fullmatch(r"(\d+)/(\d+)", frequency or "")
    if fraction and int(fraction.group(2)):
        return int(fraction.group(1)) / int(fraction.group(2)) >= 0.5
    percent = re.fullmatch(r"([\d.]+)%", frequency or "")
    return bool(percent) and float(percent.group(1)) >= 50


def normalize(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", text.lower().replace("'s", "")).strip()


def tokens(text: str) -> Set[str]:
    return {t for t in normalize(text).split() if len(t) >= 4 and t not in STOPWORDS}


class HPO:
    def __init__(self, directory: Path = HPO_DIR):
        self.names: Dict[str, str] = {}
        self.parents: Dict[str, List[str]] = defaultdict(list)
        self.label_to_id: Dict[str, str] = {}
        self._load_obo(directory / "hp.obo")
        self.disease_names: Dict[str, str] = {}
        self.annotations: Dict[str, List[Tuple[str, str]]] = defaultdict(list)
        self._load_hpoa(directory / "phenotype.hpoa")

        self.disease_closure = {d: self._closure_of(t for t, _ in terms) for d, terms in self.annotations.items()}
        self.term_diseases: Dict[str, Set[str]] = defaultdict(set)
        for disease, closure in self.disease_closure.items():
            for term in closure:
                self.term_diseases[term].add(disease)
        total = len(self.disease_closure)
        self.ic = {term: -math.log(len(ds) / total) for term, ds in self.term_diseases.items()}

        self.label_tokens: Dict[str, Set[str]] = defaultdict(set)
        for label in self.label_to_id:
            for token in tokens(label):
                self.label_tokens[token].add(label)
        self.disease_by_name: Dict[str, List[str]] = defaultdict(list)
        self.disease_tokens: Dict[str, Set[str]] = defaultdict(set)
        for disease, name in self.disease_names.items():
            self.disease_by_name[normalize(name)].append(disease)
            for token in tokens(name):
                self.disease_tokens[token].add(normalize(name))

    def _load_obo(self, path: Path) -> None:
        term: Dict = {}

        def flush():
            if term.get("id", "").startswith("HP:") and not term.get("obsolete"):
                self.names[term["id"]] = term["name"]
                self.parents[term["id"]] = term.get("is_a", [])
                for label in [term["name"], *term.get("synonyms", [])]:
                    self.label_to_id.setdefault(normalize(label), term["id"])

        for line in path.read_text(encoding="utf-8").splitlines():
            if line == "[Term]" or line.startswith("[Typedef]"):
                flush()
                term = {}
            elif line.startswith("id: "):
                term["id"] = line[4:].strip()
            elif line.startswith("name: "):
                term["name"] = line[6:].strip()
            elif line.startswith("synonym: "):
                match = re.match(r'synonym: "(.*)" (EXACT|RELATED|NARROW|BROAD)', line)
                if match and match.group(2) == "EXACT":
                    term.setdefault("synonyms", []).append(match.group(1))
            elif line.startswith("is_a: "):
                term.setdefault("is_a", []).append(line[6:].split("!")[0].strip())
            elif line.startswith("is_obsolete: true"):
                term["obsolete"] = True
        flush()

    def _load_hpoa(self, path: Path) -> None:
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.startswith("#") or line.startswith("database_id"):
                continue
            parts = line.split("\t")
            if len(parts) < 11 or parts[10] != "P" or parts[2] == "NOT" or parts[3] not in self.names:
                continue
            self.disease_names[parts[0]] = parts[1]
            self.annotations[parts[0]].append((parts[3], parts[7]))

    @lru_cache(maxsize=None)
    def ancestors(self, term: str) -> frozenset:
        result = {term}
        for parent in self.parents.get(term, []):
            result |= self.ancestors(parent)
        return frozenset(result)

    def _closure_of(self, terms) -> Set[str]:
        closure: Set[str] = set()
        for term in terms:
            closure |= self.ancestors(term)
        return closure

    def to_term(self, finding: str, threshold: float = 0.86) -> Optional[str]:
        """HPO id for a finding written as an HPO label, with a fuzzy fallback."""
        key = normalize(finding)
        if key in self.label_to_id:
            return self.label_to_id[key]
        candidates: Set[str] = set()
        for token in tokens(finding):
            candidates |= self.label_tokens.get(token, set())
        best, best_score = None, threshold
        for label in candidates:
            score = SequenceMatcher(None, key, label).ratio()
            if score > best_score:
                best, best_score = label, score
        return self.label_to_id[best] if best else None

    def rank_diseases(self, case_terms: List[str], top: int = 10) -> List[Dict]:
        """Diseases ranked by the information content of the case terms they carry."""
        scores: Dict[str, float] = defaultdict(float)
        matched: Dict[str, List[str]] = defaultdict(list)
        for term in set(case_terms):
            for disease in self.term_diseases.get(term, ()):
                scores[disease] += self.ic.get(term, 0.0)
                matched[disease].append(self.names[term])
        ranked, seen = [], set()
        for disease in sorted(scores, key=lambda d: (-scores[d], self.disease_names[d])):
            name = normalize(self.disease_names[disease])
            if name in seen:  # the same disease in OMIM and Orphanet
                continue
            seen.add(name)
            ranked.append({"disease": self.disease_names[disease], "id": disease,
                           "score": round(scores[disease], 1), "matched_findings": sorted(matched[disease])})
            if len(ranked) == top:
                break
        return ranked

    def find_disease(self, name: str, threshold: float = 0.86) -> Optional[str]:
        """Annotated disease for a diagnosis name, if HPO covers it."""
        key = normalize(re.sub(r"\(.*?\)", "", name))
        if key in self.disease_by_name:
            return self.disease_by_name[key][0]
        candidates: Set[str] = set()
        for token in tokens(key):
            candidates |= self.disease_tokens.get(token, set())
        best, best_score = None, threshold
        for label in candidates:
            score = SequenceMatcher(None, key, label).ratio()
            if score > best_score:
                best, best_score = label, score
        return self.disease_by_name[best][0] if best else None

    def profile(self, disease: str, case_terms: List[str], top: int = 12) -> Dict:
        """Typical features of a disease and which of them the case shows."""
        case_closure = self._closure_of(case_terms)
        closure = self.disease_closure.get(disease, set())
        shown = sorted({self.names[t] for t in case_terms if t in closure})
        frequent = sorted(self.annotations[disease], key=lambda item: (0 if is_frequent(item[1]) else 1, item[0]))
        typical = []
        for term, frequency in frequent:
            label = self.names[term]
            if term in case_closure or label in typical:
                continue
            typical.append(f"{label} ({FREQUENCY_WORDS.get(frequency, frequency) or 'frequency not stated'})")
            if len(typical) == top:
                break
        return {"disease": self.disease_names[disease], "case_findings_it_explains": shown,
                "typical_findings_not_reported": typical}
