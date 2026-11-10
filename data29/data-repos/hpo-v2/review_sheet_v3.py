#!/usr/bin/env python3
"""
Review sheet for David: gene-free names of HPO v3 (task 4)
==========================================================

Task 3 showed that about half of the v2 decisions were wrong or improvable, so
v3 rebuilt every gene-free name with David's criteria (clinical_gold.py). This
sheet checks v3 on a fresh random sample, without his task 3 golds and without
looking at any model result:

- 12 DDD cases where a name without the gene was added;
- 6 cases of the other datasets where the name lost a genetic subtype;
- 6 cases where no name was added because it would be a generic trait;

and asks the questions task 3 left open.

The sample is stable (fixed seed). The sheet holds the HPO lists of the cases,
so it is written under curated-datasets/ with a validacion_clinica* name, which
.gitignore keeps out of the public repo.

Usage:
    py review_sheet_v3.py   # after clinical_gold.py build
"""

import json
import random
from collections import Counter

import clinical_gold as cg
from review_sheet import GENETIC_MARK, block, load_cases, pick

OUTPUT_PATH = cg.HERE.parent / "curated-datasets" / "hpo_v2" / "validacion_clinica_nombres_sin_gen_v3.md"
SEED = 1110
# Golds David already answered in task 3, and the two he left open
TASK3_GOLDS = set(cg.REVIEWED_CLINICAL) | {"COX15-related Leigh syndrome", "IFT43-related cranioectodermal dysplasia"}


def load_decisions():
    rows = []
    for line in cg.REPORT_PATH.read_text(encoding="utf-8").splitlines():
        parts = line.split("\t")
        if len(parts) == 4:
            dataset, case_id, kind, detail = parts
            original, _, proposed = detail.partition(" -> ")
            if original not in TASK3_GOLDS:
                rows.append({"dataset": dataset, "id": case_id, "kind": kind, "original": original, "proposed": proposed})
    return rows


def cause_c_exclusions():
    """Cases the cause C rule would exclude, per dataset."""
    excluded = Counter()
    for name in cg.DATASETS:
        for case in cg.load(name):
            excluded[name] += not cg.specific_terms(case, name)
    return excluded


def pending_questions(number):
    excluded = cause_c_exclusions()
    in_input = sum(1 for line in cg.REPORT_PATH.read_text(encoding="utf-8").splitlines() if "	in_input	" in line)
    by_dataset = ", ".join(f"{n} de {name.replace('_hpo', '').upper()}" for name, n in excluded.most_common() if n)
    questions = [
        ("Casos 11 (DOCK8) y 12 (IFT43) de la tarea 3",
         "En la hoja, el 11 está marcado «corregir» sin texto y tu comentario del síndrome hiper-IgE está en el 12, que "
         "es la displasia craneoectodérmica. Para DOCK8 he puesto «Autosomal recessive hyper-IgE syndrome». ¿Bien? "
         "`[ ] sí`  `[ ] corregir:`\n\nY el 12, «IFT43-related cranioectodermal dysplasia» → «Cranioectodermal "
         "dysplasia»: `[ ] correcto`  `[ ] corregir:`  `[ ] CONSULTAR MÉDICO`"),
        ("Caso 51 (RAMEDIS_024)",
         "No tiene casilla marcada, pero en tus notas de G dices que se cuenta aparte. ¿Confirmas? "
         "`[ ] contar aparte`  `[ ] otra:`"),
        ("Casos 8 (COX15, Leigh) y 67 (Alzheimer 4), que marcaste CONSULTAR MÉDICO",
         "Mientras no se decidan, el 8 usa el nombre del LLM y el 67 no cambia nada (es un sinónimo de MONDO, que aún "
         "no están en el gold).\n\nLeigh: `[ ] Leigh syndrome`  `[ ] Leigh syndrome due to cytochrome c oxidase "
         "deficiency`  `[ ] lo consulto`\n\nAlzheimer 4 frente a «Alzheimer disease»: `[ ] la misma`  "
         "`[ ] relacionada`  `[ ] lo consulto`"),
        ("Bloque D: el criterio",
         "Excluiste el 46 (LGI4, artrogriposis múltiple congénita) y el 48 (DISP1, holoprosencefalia), y mantuviste el "
         "47 (cutis laxa), el 49 (aciduria metilmalónica) y el 50 (paraplejia espástica). En la v3 hay "
         f"{in_input} casos así y la decisión tiene que valer para todos. ¿Qué separa a los que salen de los que se quedan?\n\n> "),
        ("Regla de la causa C: la lista de términos",
         "Para aplicar tu regla quito: los de herencia, «Phenotypic variability», los obsoletos y los que repiten el "
         "gold; cualquier «intellectual disability»; los retrasos del desarrollo («Global developmental delay», "
         "«Motor delay», «Delayed speech and language development», «Delayed gross/fine motor development», "
         "«Speech delay», retrasos del lenguaje); «Seizure» sin tipo (las crisis con tipo se quedan); cualquier "
         "hipotonía; «Autism» y «Autistic behavior»; «EEG abnormality»; y «Abnormality» o «Abnormality of…». Los "
         "retrasos que no son del neurodesarrollo («Growth delay», «Delayed skeletal maturation», «Delayed eruption "
         "of teeth») se quedan. En RAMEDIS quito además los de muerte y los analitos que no son el marcador del "
         f"gold.\n\nCon esa lista la regla reproduce tus 9 decisiones y excluiría {sum(excluded.values())} casos "
         f"({by_dataset}). ¿Vale? `[ ] vale`  `[ ] cambiar:`"),
        ("RAMEDIS_132 (alcaptonuria)",
         "Salió en T3 por «convulsiones y muerte en la infancia». Si la muerte es ruido de codificación, ¿vuelve al "
         "benchmark? `[ ] vuelve`  `[ ] sigue fuera`  `[ ] CONSULTAR MÉDICO`"),
        ("Bloque G: la comprobación de la tirosina",
         "Los datos de RAMEDIS que tenemos (vía RareBench) solo traen códigos HPO, sin valores, así que no se puede "
         "mirar si la tirosina estaba alta. Lo que sí se ve: la hipertirosinemia sale solo en fenilcetonuria (78 %) y "
         "en tirosinemia I (93 %), no en otras metabolopatías donde también se mide la tirosina (MSUD, citrulinemia, "
         "OTC). Los términos de muerte están en el 82 % de los casos de RAMEDIS, el 100 % en MCAD. ¿Aplicamos la "
         "regla de ruido a todo RAMEDIS? `[ ] sí, muertes y analitos`  `[ ] solo las muertes`  `[ ] CONSULTAR MÉDICO`"),
        ("HMS_011 y HMS_035: el nombre del gold",
         "En el origen (RareBench) estos dos casos llevan varias etiquetas: el código OMIM (síndrome de Sjögren en el "
         "011, fiebre mediterránea familiar en el 035) y un grupo de cuatro códigos de Orphanet de artritis (reactiva "
         "y tres de artritis idiopática juvenil) que aparece junto en varios casos. Nuestra normalización tomó el "
         "nombre «Reactive arthritis» de ese grupo. Propuesta: el gold pasa a ser la enfermedad del código OMIM. "
         "`[ ] de acuerdo`  `[ ] no:`"),
    ]
    lines = ["## Preguntas que dejó abiertas la tarea 3", ""]
    for title, text in questions:
        number += 1
        lines += [f"### {number}. {title}", "", text, ""]
    return lines


def main():
    rng = random.Random(SEED)
    cases = load_cases()
    decisions = load_decisions()
    added = [r for r in decisions if r["kind"] == "clinical"]
    sections = [
        ("A. Nombre sin gen añadido en DDD",
         "¿El nombre sin gen es la misma enfermedad, sin el gen, y algo que un clínico pondría en un diferencial con estos síntomas?",
         ["correcto", "demasiado amplio", "otra enfermedad", "corregir:", "CONSULTAR MÉDICO"],
         pick([r for r in added if r["dataset"] == "ddd_hpo"], 12, rng)),
        ("B. Nombre sin gen añadido en otros datasets (se quita un subtipo genético)",
         "¿Se puede quitar ese subtipo sin cambiar de enfermedad?",
         ["correcto", "el subtipo es otra enfermedad: no quitarlo", "corregir:", "CONSULTAR MÉDICO"],
         pick([r for r in added if r["dataset"] != "ddd_hpo" and GENETIC_MARK.search(r["original"])], 6, rng)),
        ("C. No se añadió: quedaría un rasgo genérico",
         "¿Está bien no aceptar el nombre sin gen, o sí es una enfermedad con entidad propia?",
         ["bien así", "sí habría que aceptarlo", "aceptar este otro nombre:", "CONSULTAR MÉDICO"],
         pick([r for r in decisions if r["kind"] == "not_diagnosable"], 6, rng)),
    ]

    lines = [
        "# Revisión clínica — raras HPO v3: nombres sin gen rehechos",
        "",
        "**Responsable:** David · **Estado:** New · **Tarea:** `docs/tareas-david/04-nombres-sin-gen-v3.md`",
        "",
        "No se versiona (contiene las listas HPO de los casos). Se devuelve por canal privado.",
        "",
        "Los nombres sin gen se han rehecho para todos los casos con tus criterios de la tarea 3. Esta es una muestra "
        "nueva al azar: ninguno de los casos que ya revisaste.",
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
    lines += pending_questions(number)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {OUTPUT_PATH} ({number} cases)")


if __name__ == "__main__":
    main()
