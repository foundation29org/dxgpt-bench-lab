"""Label-leakage check shared by the narrative_v2 scripts.

A case leaks when its text names the gold diagnosis or one of its accepted
names, or contains a distinctive word of them, rather than only generic words
such as "syndrome" or "acute". See leak_check for hard and soft leaks.
"""

import re
import unicodedata
from typing import Iterable, List, Tuple

GENERIC_WORDS = {
    "acute", "chronic", "primary", "secondary", "syndrome", "disease", "disorder",
    "deficiency", "infection", "type", "with", "without", "due", "and", "the", "of",
    "left", "right", "bilateral", "severe", "mild", "benign", "malignant", "tumor",
    "tumour", "cancer", "carcinoma", "neoplasm", "lesion", "injury", "failure",
    "associated", "related", "induced", "congenital", "acquired", "hereditary",
    "familial", "idiopathic", "multiple", "isolated", "atypical", "variant",
    "cell", "cells", "fever", "pain", "abscess", "cyst", "mass", "rupture",
    "fracture", "artery", "arterial", "vein", "venous", "muscle", "nerve", "bone",
    "skin", "liver", "kidney", "renal", "lung", "pulmonary", "heart", "cardiac",
    "brain", "spinal", "blood", "chest", "abdominal", "upper", "lower", "posterior",
    "anterior", "lateral", "medial", "inflammatory", "infectious", "toxic",
    "systemic", "local", "focal", "diffuse", "stage", "grade", "high", "low",
    "patient", "presentation", "case", "after", "post", "from", "caused", "causing",
    "complicated", "complication", "pediatric", "adult", "neonatal",
    "infantile", "juvenile", "recurrent", "persistent", "spontaneous", "traumatic",
}


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def distinctive_words(name: str) -> List[str]:
    words = normalize(name).split()
    return [w for w in words if len(w) >= 5 and w not in GENERIC_WORDS and not w.isdigit()]


DISEASE_SUFFIXES = ("osis", "itis", "oma", "emia", "aemia", "pathy", "iasis", "ism", "uria", "plasia", "trophy")


def eponyms_in_text(name: str, case_text: str) -> List[str]:
    """Capitalised words of the name (Erdheim, Kikuchi) written capitalised mid-sentence in the text."""
    words = {w for w in re.findall(r"[A-Za-z']+", name) if len(w) >= 4 and w[0].isupper()}
    return [
        w for w in words
        if normalize(w) not in GENERIC_WORDS
        and re.search(rf"[a-z,;:(] {re.escape(w)}(?![A-Za-z])", case_text)
    ]


def leak_check(case_text: str, names: Iterable[str]) -> Tuple[List[str], List[str]]:
    """
    Return (hard, soft) leaks of the gold names in the case text.

    Hard: a full name, an abbreviation, an eponym, or a distinctive word that
    names a disease ("amyloidosis", "vasculitis"). Soft: other distinctive
    words, such as the causative drug or an anatomical site, which may belong
    to the presentation; they are kept for clinical review.
    """
    haystack = f" {normalize(case_text)} "
    hard, soft = [], []
    for name in names:
        normalized = normalize(name)
        if not normalized:
            continue
        # Abbreviations ("SLE", "PMM2-CDG") are matched as written.
        if re.fullmatch(r"[A-Z0-9-]{2,10}", name.strip()):
            if re.search(rf"(?<![A-Za-z0-9]){re.escape(name.strip())}(?![A-Za-z0-9])", case_text):
                hard.append(name)
            continue
        if len(normalized) >= 4 and f" {normalized} " in haystack:
            hard.append(name)
            continue
        hard += [normalize(w) for w in eponyms_in_text(name, case_text)]
        for word in distinctive_words(name):
            if f" {word} " in haystack:
                (hard if word.endswith(DISEASE_SUFFIXES) else soft).append(word)
    return sorted(set(hard)), sorted(set(soft) - set(hard))
