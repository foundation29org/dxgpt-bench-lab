#!/usr/bin/env python3
"""
Review sheet for David: gene-free names of HPO v2 and T3 cause C
================================================================

Writes a Markdown sheet with a fixed sample of the decisions taken by
clinical_gold.py, so that a clinician can check them:

- 25 DDD cases where a name without the gene was added;
- 10 cases of the other datasets where the name lost a genetic subtype
  (not the ones that only reword the same name);
- 10 cases where no name was added because it would be a generic trait;
- 5 cases where no name was added because it is one of the HPO terms;
- the 9 cases of T3 cause C (HPO terms not enough for the diagnosis).

The sample is stable (fixed seed). The sheet holds the HPO lists of the
cases, so it is written under curated-datasets/ with a validacion_clinica*
name, which .gitignore keeps out of the public repo.

Usage:
    py review_sheet.py   # after clinical_gold.py build
"""

import json
import random
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
EVAL_ROOT = HERE.parents[2]
DATASETS_DIR = EVAL_ROOT / "bench" / "datasets"
REPORT_PATH = HERE / "work" / "build_report.txt"
OUTPUT_PATH = HERE.parent / "curated-datasets" / "hpo_v2" / "validacion_clinica_nombres_sin_gen.md"
SEED = 29
GENETIC_MARK = re.compile(r"\d|\btype\b|\bcbl|-related|autosomal|x-linked|complementation|nuclear", re.I)

T3_CAUSE_C = ["RAMEDIS_024", "RAMEDIS_116", "RAMEDIS_248", "DDD_G2P00164", "DDD_G2P00512",
              "DDD_G2P01363", "DDD_G2P01703", "DDD_G2P02376", "DDD_G2P02382"]


def load_cases():
    cases = {}
    for path in DATASETS_DIR.glob("*_hpo.json"):
        for case in json.loads(path.read_text(encoding="utf-8")):
            cases[case["id"]] = case
    return cases


def load_decisions():
    rows = []
    for line in REPORT_PATH.read_text(encoding="utf-8").splitlines():
        parts = line.split("\t")
        if len(parts) == 4:
            dataset, case_id, kind, detail = parts
            original, _, proposed = detail.partition(" -> ")
            rows.append({"dataset": dataset, "id": case_id, "kind": kind, "original": original, "proposed": proposed})
    return rows


def pick(rows, n, rng):
    rows = sorted(rows, key=lambda r: r["id"])
    return rng.sample(rows, min(n, len(rows)))


def block(number, case, row, question, options):
    return "\n".join([
        f"### {number}. {case['id']} ({row['dataset'].replace('_hpo', '').upper()})",
        "",
        f"- **Gold con gen (original):** {row['original']}",
        f"- **Nombre sin gen propuesto:** {row['proposed'] or '—'}",
        f"- **Términos HPO del caso:** {case.get('case_en') or case['case']}",
        "",
        f"{question} {'  '.join(f'`[ ] {o}`' for o in options)}",
        "",
    ])


def main():
    rng = random.Random(SEED)
    cases = load_cases()
    decisions = load_decisions()
    added = [r for r in decisions if r["kind"] == "clinical"]
    sections = [
        ("A. Nombre sin gen añadido en DDD",
         "¿El nombre sin gen es la misma enfermedad, sin el gen, y algo que un clínico pondría en un diferencial con estos síntomas?",
         ["correcto", "demasiado amplio", "otra enfermedad", "corregir:", "CONSULTAR MÉDICO"],
         pick([r for r in added if r["dataset"] == "ddd_hpo"], 25, rng)),
        ("B. Nombre sin gen añadido en otros datasets (se quita un subtipo genético)",
         "¿Se puede quitar ese subtipo sin cambiar de enfermedad?",
         ["correcto", "el subtipo es otra enfermedad: no quitarlo", "corregir:", "CONSULTAR MÉDICO"],
         pick([r for r in added if r["dataset"] != "ddd_hpo" and GENETIC_MARK.search(r["original"])], 10, rng)),
        ("C. No se añadió: quedaría un rasgo genérico",
         "¿Está bien no aceptar el nombre sin gen, o sí es una enfermedad con entidad propia?",
         ["bien así", "sí habría que aceptarlo", "aceptar este otro nombre:", "CONSULTAR MÉDICO"],
         pick([r for r in decisions if r["kind"] == "not_diagnosable"], 10, rng)),
        ("D. No se añadió: el nombre ya es un término HPO del caso",
         "¿Está bien no aceptarlo (regalaría el acierto) o el caso debería salir del benchmark?",
         ["bien así", "aceptarlo igualmente", "excluir el caso", "CONSULTAR MÉDICO"],
         pick([r for r in decisions if r["kind"] == "in_input"], 5, rng)),
    ]

    lines = [
        "# Revisión clínica — raras HPO v2: nombres sin gen",
        "",
        "**Responsable:** David · **Estado:** New · **Tarea:** `docs/tareas-david/03-nombres-sin-gen-raras.md`",
        "",
        "No se versiona (contiene las listas HPO de los casos). Se devuelve por canal privado.",
        "",
        "Marca una casilla por caso. Si dudas entre dos, marca CONSULTAR MÉDICO y explica la duda en una línea.",
        "Lo que no se marque se entiende como pendiente, no como aprobado.",
        "",
    ]
    number = 0
    for title, question, options, rows in sections:
        lines += [f"## {title}", ""]
        for row in rows:
            number += 1
            lines.append(block(number, cases[row["id"]], row, question, options))

    lines += ["## E. Casos de T3 con términos HPO insuficientes (causa C)", "",
              "En tu revisión T3 marcaste estos 9 casos como «los HPO no bastan para llegar al diagnóstico». "
              "Hoy siguen en el benchmark. ¿Qué hacemos con cada uno?", ""]
    for case_id in T3_CAUSE_C:
        number += 1
        case = cases[case_id]
        lines += [
            f"### {number}. {case_id}",
            "",
            f"- **Gold:** {'; '.join(d['name'] for d in case['diagnoses'])}",
            f"- **Términos HPO del caso:** {case.get('case_en') or case['case']}",
            "",
            "Decisión: `[ ] mantener` `[ ] excluir` `[ ] mantener, pero contar aparte (no diagnosticable sin genética o metabolitos)` `[ ] CONSULTAR MÉDICO`",
            "",
        ]
    lines += ["## Criterio general", "",
              "Si de la causa C sale una regla (por ejemplo, «menos de N términos HPO y ninguno específico»), escríbela aquí "
              "y la aplicamos a todo el dataset, no solo a estos 9 casos:", "", "> ", ""]

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {OUTPUT_PATH} ({number} items)")


if __name__ == "__main__":
    main()
