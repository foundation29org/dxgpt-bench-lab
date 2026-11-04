#!/usr/bin/env python3
"""
Assemble narrative_v2
=====================

Selects accepted cases per block (live, urg, exam, synth) with these rules:
one case per principal diagnosis, at most MAX_SPECIALTY_SHARE of a block from
one specialty, and in `live` at least a third of rare diseases when available.

With --decisions (the clinical validation), excluded cases leave the pool,
kept ones take the corrected gold and text, and validated cases are picked
before any reserve case, so each exclusion is filled by the next reserve.

Writes:
- curated-datasets/narrative_v2/narrative_v2.json (and a copy in bench/datasets/)
- curated-datasets/narrative_v2/_metadata.yaml and _lineage.txt
- curated-datasets/narrative_v2/validacion_clinica.md (live and urg cases), or
  with --decisions validacion_clinica_reserva.md (only the reserve cases still to validate)

Usage:
    py build_dataset.py [--live 150] [--urg 60] [--exam 60] [--synth 30]
    py build_dataset.py --version 0.2 --decisions decisions_v0.2.yaml --text-edits work/text_edits_v0.2.json
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
# Signs and broad categories the clinical validation of v0.1 excluded as gold ("Bronchospasm",
# "Respiratory infection"): the same rule keeps them out of the reserve.
NOT_A_DIAGNOSIS = re.compile(
    r"\b(bronchospasm|bronchial (spasm|hyperreactivity)|respiratory failure|(lower |upper )?respiratory (tract )?infection)\b",
    re.IGNORECASE,
)
# Emergency reports may carry the lab printout header (patient name, ID numbers, birth date),
# the name of a consulted specialist or a signature. The patterns hold no personal data.
ANONYMIZE = [
    (re.compile(r"Paciente:.*?P[áa]gina:\s*\d+\s*de\s*\d+\s*", re.DOTALL), ""),
    (re.compile(r"(I/C A [A-ZÁÉÍÓÚÑ ]+?)\s*:\s*[A-ZÁÉÍÓÚÑ ]+\(\d{1,2}/\d{1,2}/\d{4}\s+[\d:]+\)"), r"\1"),
    (re.compile(r"\s*\bDra?\.\s+[^\n]+\s*$"), ""),
    (re.compile(r"\n?Dr/a:[^\n]*(\n\d+ de \d+(?=\n|$))?"), ""),
]
# Export leftovers: an empty field written as "nan", the lab's note on a change of
# technique and stray backticks.
ARTIFACTS = [
    (re.compile(r"\n-Complementarias:\n+nan\b"), ""),
    (re.compile(r"Nueva t[ée]cnica[^\n]*\nNuevos valores de referencia\n[^\n]*\nDebido al cambio de t[ée]cnica\n.*?hist[óo]rico\.\n", re.DOTALL), ""),
    (re.compile(r"`"), ""),
]


def anonymize(text: str) -> str:
    for pattern, replacement in ANONYMIZE + ARTIFACTS:
        text = pattern.sub(replacement, text)
    return text


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


def case_id(row: Dict) -> str:
    return f"{BLOCK_PREFIX[row['block']]}-{row['pmcid'] if row['block'] == 'live' else row['source_id']}"


def apply_text_edits(text: str, edits: List[Dict]) -> str:
    """Exact replacements must match once; regex edits (anonymization) must match the expected number of times."""
    for edit in edits:
        if "regex" in edit:
            text, count = re.subn(edit["regex"], edit["new"], text, flags=re.DOTALL)
            if count != edit["count"]:
                raise ValueError(f"text edit matched {count} times, expected {edit['count']}: {edit['regex']}")
        else:
            if text.count(edit["old"]) != 1:
                raise ValueError(f"text edit does not match exactly once: {edit['old'][:60]}")
            text = text.replace(edit["old"], edit["new"])
    return text


def apply_decision(row: Dict, decision: Dict, edits: List[Dict], reviewed: str) -> Dict:
    """A kept, validated case with the reviewer's gold, names, rare label, secondaries and text."""
    changes = [key for key in ("principal", "accepted_names", "rare", "secondary") if key in decision] + decision.get("text", [])
    row = {**row, "validated": True, "validation": {"status": "validated", "reviewed": reviewed, "changes": changes}}
    if "principal" in decision:
        row["diagnosis"] = decision["principal"]
    if "accepted_names" in decision:
        row["accepted_names"] = decision["accepted_names"]
    if "rare" in decision:
        row["rare_disease"] = decision["rare"]
    if "secondary" in decision:
        row["secondary_diagnoses"] = decision["secondary"]
    if edits:
        row["case_text"] = apply_text_edits(row["case_text"], edits)
    return row


def select(rows: List[Dict], target: int, seed: int, min_rare: int = 0) -> List[Dict]:
    """Seeded pick with unique diagnoses, a specialty cap and a rare-disease floor; validated cases go first."""
    rows = sorted(rows, key=lambda row: (not row.get("validated"), stable_rank(row, seed)))
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
    if "validation" in row:
        metadata["validation"] = row["validation"]
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


RESERVE_INTRO = [
    "# Validación clínica — narrative_v2 v0.2, casos de reserva",
    "",
    "**Responsable:** David Isla · **Estado:** New",
    "",
    "Con tu revisión salió la v0.2. Los casos que se excluyeron, y los que quedaron",
    "repetidos al corregir el gold, se sustituyen por estos casos de reserva, que hay",
    "que validar igual. La hoja y los criterios son los mismos, con cuatro",
    "aclaraciones que salen de tu revisión:",
    "",
    "- **Fuga:** solo si el texto nombra el diagnóstico o da un resultado que por sí",
    "  solo lo establece: biopsia, citología, cultivo, serología, prueba confirmatoria",
    "  o mutación. Un dato de laboratorio o de imagen que hay que interpretar (una",
    "  gasometría, unos ácidos biliares, una RM) no es fuga, aunque sea el dato clave.",
    "- **No diagnosticable → excluir**, aunque no haya fuga.",
    "- **Rara:** las intoxicaciones, las reacciones a fármacos, las lesiones y las",
    "  complicaciones de procedimientos cuentan como no raras, salvo que Orphanet las",
    "  recoja.",
    "- **Decisión:** marca una sola casilla. Si se arregla quitando una frase, marca",
    "  «mantener» y copia la frase exacta.",
    "",
    "En los casos de urgencias, «Diagnóstico de alta original» es el juicio clínico",
    "del informe, no una referencia.",
    "",
]


def validation_sheet(cases: List[Dict], not_disease: Dict[str, str], reserve: bool = False) -> str:
    live = sum(1 for c in cases if c["metadata"]["block"] == "live")
    urg = len(cases) - live
    if reserve:
        lines = RESERVE_INTRO + [
            f"**Alcance:** {len(cases)} casos: {live} `L-` y {urg} `U-`; a 1–2 min por caso, ≈ "
            + (f"{round(len(cases) * 1.5 / 60)} h." if len(cases) >= 30 else f"{max(5, round(len(cases) * 1.5 / 5) * 5)} min."),
            "",
        ]
    else:
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
        "- **Rara:** si el diagnóstico principal es una enfermedad rara (en Orphanet o",
        "  con prevalencia menor de 1 por 2.000). La etiqueta la puso el LLM y decide en",
        "  qué cifra principal cuenta el caso (raras o no raras); corrígela si está mal.",
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
        others = ", ".join(meta.get("other_conditions") or []) or "—"
        source = meta.get("url") or meta.get("original_diagnosis") or ""
        source_label = "Diagnóstico de alta original" if reserve and meta["block"] == "urg" else "Fuente"
        lines += [f"## {case['id']}", ""]
        if case["id"] in not_disease:
            lines += ["⚠ **El juez cree que esta referencia no es una enfermedad.**", ""]
        lines += [
            f"- **Diagnóstico principal:** {principal['name']}",
            f"- **Nombres aceptados:** {', '.join(principal['accepted_names']) or '—'}",
            f"- **Secundarios:** {', '.join(secondaries) or '—'}" if meta["block"] == "urg" else
            f"- **Otros diagnósticos del caso (no puntúan):** {others}",
            f"- **Especialidad:** {meta.get('specialty') or '—'} · **Rara:** {'sí' if meta['rare_disease'] else 'no'}",
            f"- **Pistas a revisar:** {', '.join(meta['soft_leaked_terms']) or '—'}",
            f"- **{source_label}:** {source}",
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
            "- Rara: `[ ] correcto` `[ ] cambiar`",
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
    parser.add_argument("--version", default="0.1")
    parser.add_argument("--decisions", type=Path, default=None,
                        help="clinical validation decisions (decisions_v0.2.yaml): exclusions and corrected gold")
    parser.add_argument("--text-edits", type=Path, default=None,
                        help="text cuts for kept cases (work/text_edits_v0.2.json, not versioned)")
    args = parser.parse_args()
    review = yaml.safe_load(args.decisions.read_text(encoding="utf-8")) if args.decisions else {}
    decisions = review.get("cases", {})
    text_edits = json.loads(args.text_edits.read_text(encoding="utf-8")) if args.text_edits else {}

    live = json.loads((WORK_DIR / "live_extracted.json").read_text(encoding="utf-8"))
    internal = json.loads((WORK_DIR / "internal_triaged.json").read_text(encoding="utf-8"))
    pools = {
        "live": [{**r, "block": "live", "diagnosis": r["final_diagnosis"]} for r in live
                 if r.get("accepted") and is_human_case(r)],
        **{
            block: [{**r, "diagnosis": r["principal_diagnosis"],
                     "case_text": anonymize(r["case_text"]) if block == "urg" else r["case_text"]}
                    for r in internal if r["block"] == block and r.get("accepted")]
            for block in ("urg", "exam", "synth")
        },
    }
    if decisions:
        excluded = {block: sum(1 for r in rows if decisions.get(case_id(r), {}).get("decision") == "exclude") for block, rows in pools.items()}
        pools = {
            block: [apply_decision(r, decisions[case_id(r)], text_edits.get(case_id(r), []), review["reviewed"])
                    if case_id(r) in decisions else
                    {**r, "validation": {"status": "pending" if block in ("live", "urg") else "not_reviewed"}}
                    for r in rows if decisions.get(case_id(r), {}).get("decision") != "exclude"]
            for block, rows in pools.items()
        }
    def unusable(row: Dict) -> bool:
        if row.get("validated"):
            return False
        return bool(NONSPECIFIC.search(row["diagnosis"]) or (decisions and NOT_A_DIAGNOSIS.search(row["diagnosis"])))

    nonspecific = {block: [r for r in rows if unusable(r)] for block, rows in pools.items()}
    pools = {block: [r for r in rows if not unusable(r)] for block, rows in pools.items()}
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
    if decisions:
        for block in targets:
            composition[block].update({
                "excluded_by_validation": excluded[block],
                "validated": sum(1 for r in selected[block] if r.get("validated")),
                "pending_validation": sum(1 for r in selected[block] if r["validation"]["status"] == "pending"),
            })
    validated = sum(composition[b].get("validated", 0) for b in targets)
    pending = sum(composition[b].get("pending_validation", 0) for b in targets)
    live_dates = sorted(r["entrez_date"] for r in selected["live"])
    metadata = {
        "dataset": "narrative_v2",
        "version": args.version,
        "created": date.today().isoformat(),
        "status": (f"VALIDADOS {validated} casos live y urg; PENDIENTES {pending} casos de reserva" if decisions
                   else "PENDIENTE DE VALIDACION CLINICA"),
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
    if decisions:
        metadata["validation"] = {
            "decisions": f"data29/data-repos/narrative-v2/{args.decisions.name}",
            "reviewer": review.get("reviewer"),
            "reviewed": review.get("reviewed"),
            "decided_cases": len(decisions),
            "excluded": dict(Counter(d.get("reason") for d in decisions.values() if d["decision"] == "exclude")),
            "rules": review.get("rules"),
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
    if decisions:
        lineage[2] += f"; v{args.version} aplica {args.decisions.name}"
        lineage[-2] = "CASOS (id, bloque, diagnóstico principal, validación)"
        lineage[-1] = "-" * len(lineage[-2])
    lineage += [f"{c['id']}\t{c['metadata']['block']}\t{c['diagnoses'][0]['name']}"
                + (f"\t{c['metadata']['validation']['status']}" if decisions else "") for c in cases]
    (CURATED_DIR / "_lineage.txt").write_text("\n".join(lineage) + "\n", encoding="utf-8")

    if decisions:
        to_validate = [c for c in cases if c["metadata"]["validation"]["status"] == "pending"]
        (CURATED_DIR / "validacion_clinica_reserva.md").write_text(validation_sheet(to_validate, {}, reserve=True), encoding="utf-8")
    else:
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
