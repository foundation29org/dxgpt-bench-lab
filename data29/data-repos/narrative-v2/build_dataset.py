#!/usr/bin/env python3
"""
Assemble narrative_v2
=====================

Selects accepted cases per block (live, urg, exam, synth) with these rules:
one case per principal diagnosis, at most MAX_SPECIALTY_SHARE of a block from
one specialty, and in `live` at least a third of rare diseases when available.

Writes:
- curated-datasets/narrative_v2/narrative_v2.json (and a copy in bench/datasets/)
- curated-datasets/narrative_v2/_metadata.yaml and _lineage.txt
- curated-datasets/narrative_v2/validacion_clinica.md (live and urg cases)

Usage:
    py build_dataset.py [--live 150] [--urg 60] [--exam 60] [--synth 30]
"""

import argparse
import hashlib
import json
import re
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Dict, List

import yaml

from extract_live_cases import HERE
from leakage import normalize

WORK_DIR = HERE / "work"
CURATED_DIR = HERE.parent / "curated-datasets" / "narrative_v2"
BENCH_COPY = HERE.parents[2] / "bench" / "datasets" / "narrative_v2.json"
MAX_SPECIALTY_SHARE = 0.15
# Principal diagnoses that any related answer would match ("viriasis
# inespecífica", "mechanical low back pain"): they measure nothing.
NONSPECIFIC = re.compile(
    r"\b(viral (infection|illness|syndrome|process)|viriasis|unspecified|non-?specific|undifferentiated)\b|\bpain\b",
    re.IGNORECASE,
)
# PubMed "Case Reports" also indexes veterinary journals.
VETERINARY_JOURNAL = re.compile(r"veterinar|animals", re.IGNORECASE)
HUMAN_PATIENT = re.compile(r"\b(man|woman|boy|girl|infant|newborn|neonate|child|adolescent|gentleman|lady)\b", re.IGNORECASE)
ANIMAL_PATIENT = re.compile(
    r"\b(dog|canine|cat|feline|horse|equine|pony|mare|filly|foal|gelding|bovine|cow|heifer|calf|ferret|rabbit|parrot|sheep|goat)\b",
    re.IGNORECASE,
)


def is_human_case(row: Dict) -> bool:
    opening = row["case_text"][:200]
    if ANIMAL_PATIENT.search(opening):
        return False
    return not (VETERINARY_JOURNAL.search(row.get("journal") or "") and not HUMAN_PATIENT.search(opening))
EMPTY_CODES = {"icd10": [], "snomed": [], "omim": [], "orpha": []}
BLOCK_PREFIX = {"live": "L", "urg": "U", "exam": "E", "synth": "Y"}


def stable_rank(row: Dict, seed: int) -> str:
    """Fixed order per case: excluding one case only frees its own slot."""
    source_id = row.get("pmcid") or row.get("source_id")
    return hashlib.sha1(f"{seed}:{source_id}".encode()).hexdigest()


def select(rows: List[Dict], target: int, seed: int, min_rare: int = 0) -> List[Dict]:
    """Seeded pick with unique diagnoses, a specialty cap and a rare-disease floor."""
    rows = sorted(rows, key=lambda row: stable_rank(row, seed))
    cap = max(1, int(target * MAX_SPECIALTY_SHARE))
    chosen, seen, specialties = [], set(), Counter()
    rare_needed = min_rare
    for pass_rare in (True, False):
        for row in rows:
            if len(chosen) == target or (pass_rare and rare_needed <= 0):
                break
            if pass_rare and not row.get("rare_disease"):
                continue
            key = normalize(row["diagnosis"])
            specialty = normalize(row.get("specialty") or "unknown")
            if key in seen or specialties[specialty] >= cap or row in chosen:
                continue
            chosen.append(row)
            seen.add(key)
            specialties[specialty] += 1
            if row.get("rare_disease"):
                rare_needed -= 1
    return chosen


def gold(name: str, role: str, accepted: List[str]) -> Dict:
    return {"name": name, "role": role, "accepted_names": accepted, "medical_codes": dict(EMPTY_CODES)}


def to_case(row: Dict) -> Dict:
    block = row["block"]
    source_id = row["pmcid"] if block == "live" else row["source_id"]
    secondaries = [s for s in (row.get("secondary_diagnoses") or []) if isinstance(s, str) and s.strip()]
    diagnoses = [gold(row["diagnosis"], "principal", list(row.get("accepted_names") or []))]
    # Only emergency visits have simultaneous diagnoses that count (rubric C3).
    # Elsewhere they are comorbidities ("Hypertension") and are not scored.
    if block == "urg":
        diagnoses += [gold(s, "secondary", []) for s in secondaries]
    metadata = {
        "block": block,
        "source_id": source_id,
        "language": "es" if block == "urg" else "en",
        "rare_disease": bool(row.get("rare_disease")),
        "specialty": row.get("specialty"),
        "soft_leaked_terms": row.get("soft_leaked_terms") or [],
        "other_conditions": [] if block == "urg" else secondaries,
        "contamination_risk": {"live": "low", "urg": "low", "exam": "high", "synth": "medium"}[block],
    }
    if block == "live":
        metadata.update({
            "source": "pmc_oa", "pmid": row["pmid"], "pmcid": row["pmcid"], "journal": row["journal"],
            "title": row["title"], "entrez_date": row["entrez_date"],
            "license": row["license"], "license_url": row["license_url"],
            "url": f"https://pmc.ncbi.nlm.nih.gov/articles/{row['pmcid']}/",
        })
    else:
        metadata.update({
            "source": {"urg": "urgtorre", "exam": "medqa_medbullets", "synth": "rare_synthetic"}[block],
            "original_golds": row.get("original_golds"),
            "dropped_golds": row.get("dropped_golds"),
        })
        if block == "urg":
            metadata["original_diagnosis"] = (row.get("source_metadata") or {}).get("original_diagnosis")
    return {
        "id": f"{BLOCK_PREFIX[block]}-{source_id}",
        "case": row["case_text"],
        "complexity": row.get("complexity"),
        "diagnoses": diagnoses,
        "metadata": metadata,
    }


def validation_sheet(cases: List[Dict], not_disease: Dict[str, str]) -> str:
    live = sum(1 for c in cases if c["metadata"]["block"] == "live")
    urg = len(cases) - live
    lines = [
        "# Validación clínica — narrative_v2",
        "",
        "**Responsable:** David Isla · **Estado:** New",
        "",
        "`narrative_v2` sustituye a `all_256_clean` como banco narrativo (ver",
        "`data29/data-repos/narrative-v2/README.md`). Antes de usarlo como línea base hay",
        "que confirmar que cada caso sirve. Un LLM extrajo el diagnóstico y el texto; tú",
        "decides si se queda.",
        "",
        f"**Alcance:** {len(cases)} casos: {live} case reports publicados entre julio y octubre",
        f"de 2026 (`L-`, en inglés, con enlace al artículo) y {urg} casos de urgencias (`U-`,",
        "en español, con el diagnóstico de alta original).",
        "",
        f"**Tiempo orientativo:** 1–2 min por caso, unas {round(len(cases) * 1.5 / 60)} h. Se puede hacer por",
        "partes: primero los `L-` y después los `U-`. Los casos sin marcar se entienden",
        "como pendientes, no como aprobados.",
        "",
        "## Qué revisar en cada caso",
        "",
        "- **Diagnóstico principal:** el diagnóstico final del caso, al nivel que se",
        "  escribiría en un diagnóstico diferencial: sin grado, estadio, tamaño ni",
        "  sub-localización exacta, salvo que definan una enfermedad distinta. Si es",
        "  demasiado amplio, demasiado específico o no es una enfermedad, corrígelo.",
        "- **Nombres aceptados:** sinónimos de exactamente la misma entidad. Quita las",
        "  categorías amplias y las enfermedades relacionadas.",
        "- **Fuga:** hay fuga si el texto nombra el diagnóstico o da un resultado que por",
        "  sí solo lo establece (biopsia, mutación, enzima que lo define). No la hay si",
        "  solo describe hallazgos que un clínico aún tiene que interpretar. Las",
        "  «pistas a revisar» son palabras del diagnóstico que aparecen en el texto,",
        "  casi siempre anatomía o el fármaco causante.",
        "- **Diagnosticable:** con este texto, un clínico podría incluir el diagnóstico",
        "  en su diferencial.",
        "- **Decisión:** mantener o excluir.",
        "",
        f"⚠ El juez automático marcó {len(not_disease)} referencias como «no es una enfermedad»:",
        ", ".join(f"`{case_id}` ({name})" for case_id, name in not_disease.items()) or "ninguna",
        "",
    ]
    for case in cases:
        meta = case["metadata"]
        principal = case["diagnoses"][0]
        secondaries = [d["name"] for d in case["diagnoses"][1:]]
        source = meta.get("url") or meta.get("original_diagnosis") or ""
        lines += [f"## {case['id']}", ""]
        if case["id"] in not_disease:
            lines += ["⚠ **El juez cree que esta referencia no es una enfermedad.**", ""]
        lines += [
            f"- **Diagnóstico principal:** {principal['name']}",
            f"- **Nombres aceptados:** {', '.join(principal['accepted_names']) or '—'}",
            f"- **Secundarios:** {', '.join(secondaries) or '—'}",
            f"- **Especialidad:** {meta.get('specialty') or '—'} · **Rara:** {'sí' if meta['rare_disease'] else 'no'}",
            f"- **Pistas a revisar:** {', '.join(meta['soft_leaked_terms']) or '—'}",
            f"- **Fuente:** {source}",
            "",
            "<details><summary>Texto del caso</summary>",
            "",
            f"> {case['case'].replace(chr(10), ' ')}",
            "",
            "</details>",
            "",
            "- Diagnóstico principal: `[ ] correcto` `[ ] corregir:`",
            "- Nombres aceptados: `[ ] correctos` `[ ] corregir:`",
            "- Fuga: `[ ] no` `[ ] sí:`",
            "- Diagnosticable: `[ ] sí` `[ ] no`",
            "- Decisión: `[ ] mantener` `[ ] excluir`",
            "",
            "---",
            "",
        ]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", type=int, default=150)
    parser.add_argument("--urg", type=int, default=60)
    parser.add_argument("--exam", type=int, default=60)
    parser.add_argument("--synth", type=int, default=30)
    parser.add_argument("--seed", type=int, default=29)
    parser.add_argument("--judge-summary", type=Path, default=None,
                        help="summary.json of a Pipeline V5 run, to flag gold the judge says are not diseases")
    args = parser.parse_args()

    live = json.loads((WORK_DIR / "live_extracted.json").read_text(encoding="utf-8"))
    internal = json.loads((WORK_DIR / "internal_triaged.json").read_text(encoding="utf-8"))
    pools = {
        "live": [{**r, "block": "live", "diagnosis": r["final_diagnosis"]} for r in live
                 if r.get("accepted") and is_human_case(r)],
        **{
            block: [{**r, "diagnosis": r["principal_diagnosis"]} for r in internal
                    if r["block"] == block and r.get("accepted")]
            for block in ("urg", "exam", "synth")
        },
    }
    nonspecific = {block: [r for r in rows if NONSPECIFIC.search(r["diagnosis"])] for block, rows in pools.items()}
    pools = {block: [r for r in rows if not NONSPECIFIC.search(r["diagnosis"])] for block, rows in pools.items()}
    targets = {"live": args.live, "urg": args.urg, "exam": args.exam, "synth": args.synth}
    selected = {
        block: select(pools[block], targets[block], args.seed, min_rare=targets[block] // 3 if block == "live" else 0)
        for block in targets
    }
    cases = [to_case(row) for block in targets for row in selected[block]]

    CURATED_DIR.mkdir(parents=True, exist_ok=True)
    dataset_json = json.dumps(cases, ensure_ascii=False, indent=1)
    (CURATED_DIR / "narrative_v2.json").write_text(dataset_json, encoding="utf-8")
    BENCH_COPY.write_text(dataset_json, encoding="utf-8")

    composition = {
        block: {
            "target": targets[block],
            "accepted_pool": len(pools[block]),
            "excluded_nonspecific": len(nonspecific[block]),
            "selected": len(selected[block]),
            "rare": sum(1 for r in selected[block] if r.get("rare_disease")),
            "with_scored_secondary": sum(1 for r in selected[block] if block == "urg" and r.get("secondary_diagnoses")),
            "soft_leak_flags": sum(1 for r in selected[block] if r.get("soft_leaked_terms")),
        }
        for block in targets
    }
    live_dates = sorted(r["entrez_date"] for r in selected["live"])
    metadata = {
        "dataset": "narrative_v2",
        "version": "0.1",
        "created": date.today().isoformat(),
        "status": "PENDIENTE DE VALIDACION CLINICA",
        "summary": {
            "total_cases": len(cases),
            "composition": composition,
            "languages": dict(Counter(c["metadata"]["language"] for c in cases)),
            "rare_disease_cases": sum(1 for c in cases if c["metadata"]["rare_disease"]),
            "specialties": dict(Counter(c["metadata"]["specialty"] for c in cases).most_common()),
            "live_entrez_dates": [live_dates[0], live_dates[-1]] if live_dates else None,
        },
        "gold_format": {
            "principal": "diagnoses[0], role=principal, with accepted_names",
            "secondary": "role=secondary, only in urg (simultaneous diagnoses); counts as a hit under rubric rule C3.2 A",
            "other_conditions": "metadata.other_conditions in live/exam/synth: comorbidities, not scored",
            "normalized_text": "not used",
            "medical_codes": "empty: the V5 judge decides every case",
        },
        "build": {
            "scripts": "data29/data-repos/narrative-v2/",
            "curation_model": "gemini-2.5-pro",
            "seed": args.seed,
        },
    }
    (CURATED_DIR / "_metadata.yaml").write_text(
        "# Metadata — narrative_v2 (generado por build_dataset.py)\n"
        + yaml.safe_dump(metadata, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
    lineage = [
        "narrative_v2.json — Lineage Trace",
        "=================================",
        f"Creado: {date.today().isoformat()} con data29/data-repos/narrative-v2/build_dataset.py",
        "",
        "live : PubMed 'Case Reports'[pt] + PMC open access + English, Entrez date >= 2026-07-01",
        "       harvest_pmc.py -> raw/pmc_live/candidates.json (licencias CC sin ND)",
        "       extract_live_cases.py (gemini-2.5-pro) -> work/live_extracted.json + leakage.py",
        "urg  : raw/urgtorre.json -> select_internal_cases.py (muestra 200, seed 29)",
        "exam : raw/medqausmle4op.json + raw/medbulltes5op.json, pregunta final con 'diagnos'",
        "       -> select_internal_cases.py (muestra 150, seed 29), pregunta eliminada del texto",
        "synth: raw/rare_synthetic.json -> select_internal_cases.py (muestra 60, seed 29)",
        "",
        "CASOS",
        "-----",
    ]
    lineage += [f"{c['id']}\t{c['metadata']['block']}\t{c['diagnoses'][0]['name']}" for c in cases]
    (CURATED_DIR / "_lineage.txt").write_text("\n".join(lineage) + "\n", encoding="utf-8")

    to_validate = [c for c in cases if c["metadata"]["block"] in ("live", "urg")]
    not_disease = {}
    if args.judge_summary:
        flagged = json.loads(args.judge_summary.read_text(encoding="utf-8"))["global"]["reference_not_disease"]
        validated_ids = {c["id"] for c in to_validate}
        not_disease = {f["case_id"]: f["gdx"] for f in flagged if f["case_id"] in validated_ids}
    (CURATED_DIR / "validacion_clinica.md").write_text(validation_sheet(to_validate, not_disease), encoding="utf-8")
    print(json.dumps(metadata["summary"], ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
