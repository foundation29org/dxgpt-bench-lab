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
- the 9 cases of T3 cause C (HPO terms not enough for the diagnosis);
- 10 options whose Gemini 2.5 Pro verdict («2 or not») changes when the gold
  carries its MONDO exact synonyms (gold_synonyms.py), 6 that become a hit and
  4 that stop being one, to check those synonyms before they go into the gold.

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

# Same Terra and Sol lists scored by Gemini 2.5 Pro against HPO v2 and against HPO v2 + MONDO synonyms
PIPELINE_OUTPUT = EVAL_ROOT / "bench" / "pipelines" / "pipeline_v5" / "main" / "output"
SYN_DATASETS = ["ramedis_hpo", "lirical_hpo", "mygene2_hpo", "hms_hpo", "mme_hpo"]
SYN_LISTS = ["gpt_5_6_terra_low", "gpt_6_1_sol_low"]
# The case that started the test: OMIM 108145 is distal arthrogryposis type 5
SYN_ANCHOR = ("Arthrogryposis with oculomotor limitation and electroretinal anomalies", "distal arthrogryposis type 5")


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


def latest_details(folder):
    runs = sorted(p for p in folder.glob("2*") if (p / "evaluation_details.txt").exists())
    if not runs:
        return {}
    text = (runs[-1] / "evaluation_details.txt").read_text(encoding="utf-8")
    return {str(c["case_id"]): c for c in (json.loads(b) for b in text.split("\n---\n") if b.strip())}


def norm(text):
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def synonym_changes():
    """Options whose «2 or not» verdict changes when the gold carries its MONDO synonyms, one per gold and option."""
    changes = {}
    for dataset in SYN_DATASETS:
        for lists in SYN_LISTS:
            before = latest_details(PIPELINE_OUTPUT / f"{dataset}_v2" / "juanjo_classic_v2" / lists)
            after = latest_details(PIPELINE_OUTPUT / f"{dataset}_v2_syn" / "juanjo_classic_v2" / lists)
            for case_id in sorted(set(before) & set(after)):
                names = {g["name"]: g["details"].get("accepted_names") or [] for g in after[case_id]["gdx_details"]}
                old = {g["name"]: g["details"].get("accepted_names") or [] for g in before[case_id]["gdx_details"]}
                traces = zip(before[case_id]["eval_details"]["graded_trace"], after[case_id]["eval_details"]["graded_trace"])
                for t_before, t_after in traces:
                    for o_before, o_after in zip(t_before["options"], t_after["options"]):
                        if (o_before["grade"] == 2) == (o_after["grade"] == 2):
                            continue
                        key = (norm(t_after["gdx"]), norm(o_after["name"]))
                        added = list(dict.fromkeys(n for n in names.get(t_after["gdx"], []) if n not in old.get(t_after["gdx"], [])))
                        if not added:  # same gold: the change is the judge's own variation, not the synonyms
                            continue
                        changes.setdefault(key, {"dataset": dataset, "id": case_id, "gold": t_after["gdx"],
                                                 "synonyms": added, "option": o_after["name"],
                                                 "hit": o_after["grade"] == 2})
    return [changes[k] for k in sorted(changes)]


def synonym_rows(rng):
    rows = synonym_changes()
    anchor = [r for r in rows if r["hit"] and r["gold"] == SYN_ANCHOR[0] and norm(r["option"]) == norm(SYN_ANCHOR[1])]
    gained = [r for r in rows if r["hit"] and r not in anchor]
    lost = [r for r in rows if not r["hit"]]
    return anchor[:1] + rng.sample(gained, min(6 - len(anchor[:1]), len(gained))) + rng.sample(lost, min(4, len(lost)))


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
    lines += ["## F. Sinónimos de MONDO en el gold", "",
              "El juez solo ve el nombre del gold. Para que reconozca sinónimos poco usados, se prueba a añadirle los sinónimos "
              "exactos que da MONDO para su código OMIM. En estas parejas, añadir los sinónimos cambia si la respuesta cuenta "
              "como acierto. No se dice en qué sentido, para no condicionarte.", ""]
    for row in synonym_rows(random.Random(SEED)):
        number += 1
        case = cases[row["id"]]
        lines += [
            f"### {number}. {row['id']} ({row['dataset'].replace('_hpo', '').upper()})",
            "",
            f"- **Gold:** {row['gold']}",
            f"- **Sinónimos de MONDO añadidos:** {'; '.join(row['synonyms']) or '—'}",
            f"- **Diagnóstico del modelo:** {row['option']}",
            f"- **Términos HPO del caso:** {case.get('case_en') or case['case']}",
            "",
            "¿El diagnóstico del modelo es la misma enfermedad que el gold? "
            "`[ ] sí, la misma`  `[ ] relacionada, no la misma`  `[ ] otra enfermedad`  "
            "`[ ] algún sinónimo de MONDO está mal:`  `[ ] CONSULTAR MÉDICO`",
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
