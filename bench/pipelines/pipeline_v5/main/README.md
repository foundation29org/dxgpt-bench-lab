# Pipeline V5

Pipeline V5 cambia solo el **evaluador**. El emulador, el labeler y el formato
de salida son los de Pipeline V4, que se queda intacto en
`bench/pipelines/pipeline_v4 - fork/main`.

Origen de los cambios: la revisión de la rúbrica del juez
(`bench/multimodal_beta/JULIAN_HARNESS_REVIEW.md`, §9–§11) y el plan del
evaluador en `docs/ROADMAP.md`.

## Qué cambia respecto a V4

| | V4 strict | V5 |
|---|---|---|
| SNOMED exacto | acierto sin juez | acierto sin juez (igual) |
| ICD-10 exacto | acierto sin juez | **no decide** desde `graded_v2` (regla C1): decide el juez |
| ICD-10 hijo, padre, hermano | acierto sin juez | **no deciden**: se guardan como dato y decide el juez |
| SapBERT ≥ 0,90 | acierto sin juez | **no se usa** |
| SapBERT ≥ 0,80 | adelanta la posición del juez | **no se usa** |
| Cuándo se llama al juez | solo si ninguna capa acierta | **en todos los casos** |
| Texto del gold que lee el juez | `normalized_text` del labeler | **el gold tal como está en el dataset** |
| Respuesta del juez | una posición (`0` = ninguna) | **una nota por opción**: 2 / 1 / 0, en JSON |
| Posición del acierto | la de la primera capa que acierta | **la mejor** entre códigos exactos y juez |
| Métricas | una lectura | **estricta** (solo 2) y **laxa** (2 o 1) |

Notas del juez (`graded_v1`):

- **2**: misma entidad. Sinónimos, abreviaturas y variantes. Una forma más
  específica solo si todo paciente con la opción tiene el diagnóstico de
  referencia (subtipo de la referencia, o la referencia con lateralidad o
  extensión añadidas).
- **1**: relacionado, no igual. Categoría más amplia, omite un calificador que
  define la referencia («GIST» frente a «GIST maligno»), otro subtipo, gen o
  fenotipo de la misma familia, causa, complicación, precursor o consecuencia,
  o una disyuntiva «A o B».
- **0**: otra enfermedad.

Desde `graded_v2` (reglas de la rúbrica contestadas por Julián):

- **C1:** solo SNOMED exacto decide sin juez.
- **C2:** «X con Y» (Y es una complicación o manifestación) y «hallazgo debido
  a X» se aciertan con «X».
- **C3:** con varios gold, basta con acertar uno.
- **C4:** las referencias amplias se aciertan con una forma más específica.
- Si el gold trae `accepted_names`, el juez los recibe como «also known as».

El juez también indica si la referencia es una enfermedad
(`reference_is_disease`). No cambia la nota: sirve para limpiar el dataset.

La cifra oficial es la **estricta**. La laxa es de uso interno mientras la
frontera entre 1 y 0 no esté validada clínicamente.

## Cómo ejecutar

Igual que V4, desde esta carpeta:

```powershell
cd "C:\repos\DxGPT\eval\bench\pipelines\pipeline_v5\main"
py main.py --config config_terra_low_all256.yaml
```

`REUSE_LABELED_DDX` copia la salida del labeler de un run anterior y evalúa
esas mismas listas, sin llamar al emulador ni al labeler. Así la diferencia
con V4 se debe solo al evaluador. Sin esa clave, V5 hace un run completo como
V4.

`EVALUATOR.CASE_LIMIT: N` evalúa solo los primeros N casos (prueba rápida).

## Salidas

En `output/<dataset>/<prompt>/<modelo>/<timestamp>/`:

- `evaluation_details.txt`: un bloque JSON por caso, separados por `---`.
  `final_resolution` (estricta) y `lax_resolution` (laxa) siguen el formato de
  V4. `graded_trace` guarda, por cada opción, el código exacto si lo hay, la
  relación ICD-10, la nota del juez y la nota final.
- `summary.json`: R@1, R@3, R@5, cobertura, posición media y MRR en las dos
  lecturas. También incluye las listas de auditoría:
  - `code_judge_disagreements`: código exacto, pero el juez no da un 2;
  - `icd10_relation_judge_grades`: qué nota pone el juez a hijos, padres y
    hermanos ICD;
  - `reference_not_disease`: gold que el juez no considera una enfermedad.
- `judge_metrics.json`: cada llamada al juez, con tokens, latencia y coste
  estimado.

Comparación con V4 sobre las mismas listas:

```powershell
py compare_runs.py --baseline "<v4>\evaluation_details.txt" --candidate "<v5>\evaluation_details.txt"
```

Escribe `comparison.md` junto al run de V5, con los casos que cambian
agrupados por la capa de V4 que los decidía.

## Primer run: Terra low en all_256_clean (27-oct-2026)

Mismas listas DDX que el run `20260710140614`. Juez Gemini 2.5 Pro, prompt
`graded_v1`, anterior a las reglas C1 y C2.

| Evaluación | R@1 | R@3 | R@5 |
|---|---:|---:|---:|
| V4 strict (canónico) | 63,3 % | 80,1 % | 83,2 % |
| V5, gold normalizado (`20261027194849`) | 69,9 % | 80,1 % | 82,0 % |
| V5, gold original (`20261027200004`) | **69,1 %** | 79,3 % | **81,2 %** |
| V5 laxa, gold original | 88,7 % | 94,5 % | 96,9 % |

357 llamadas al juez, 0 respuestas inválidas, ≈ 4,2 $, p50 10 s, ≈ 10 min.
Detalle caso a caso en `comparison.md` de cada run.

- **R@1 sube unos 6 puntos.** V4 fijaba la posición con la primera capa que
  acertaba. En Boerhaave, Terra lo tenía en P1 y V4 lo contaba en P3 por un
  hermano ICD (Mallory-Weiss).
- **R@5 baja 2 puntos.** Salen unos 12 aciertos de hermanos/padres ICD y BERT
  que eran otra enfermedad: Mallory-Weiss por Boerhaave, MADD por déficit de
  CPT I, rubéola congénita por CMV fetal. Entran otros por la regla «más
  específico», varios con gold amplios.
- **Hermanos y padres ICD:** de 75 opciones con esa relación, el juez solo da
  un 2 a 12.
- **BERT no aporta aciertos que no dé el juez.** De los 16 casos que V4
  resolvía con BERT, el juez da un 2 a 14 y un 1 a 2. Sus fallos están en
  raras, con nombres casi iguales (L-2 frente a D-2 hidroxiglutárica).
- **La nota laxa (≈ 97 %) reproduce el 98 % del juez antiguo.**

## Pendiente

Cosas que el run ha sacado a la luz y que necesitan decisión clínica (David):

- **ICD-10 exacto también falla.** ICD-10 agrupa enfermedades distintas bajo
  un mismo código: déficit de piruvato deshidrogenasa frente a déficit de
  piruvato carboxilasa, miositis por cuerpos de inclusión frente a
  polimiositis. Propuesta: que lo decida el juez y que solo SNOMED exacto
  decida sin juez. En este run, R@5 bajaría unos 2 puntos.
- **Gold compuestos** («X with Y», «X due to Y»): el juez da un 1 a «X» solo
  («Cystic fibrosis» frente a «Cystic fibrosis with bronchiectasis») y SNOMED
  da un 2. Hay que fijar la regla. Son la mayoría de
  `code_judge_disagreements`.
- **Casos con varios gold** (69 de 256). En los `R` son sinónimos y basta uno.
  En los `T` son diagnósticos simultáneos, y David exige que una opción los
  cubra todos (T795, T208). Falta un campo en el dataset que lo indique y la
  regla correspondiente. Es la regla que más mueve la cifra. V4 y V5 aplican
  la misma («basta uno»). Si se aplica a los `T` la de septiembre, R@1 pasa
  de 69,1 % a 62,1 % y R@5 de 81,2 % a 72,3 %. Si basta con que todos
  aparezcan en la lista, R@5 queda en 75,4 %.
- **Gold amplios o que no son enfermedad** (24 marcados por el juez): con la
  regla «más específico» se aciertan con cualquier enfermedad concreta de la
  categoría («Ovarian tumor» → Sertoli-Leydig). Hay que limpiarlos o
  excluirlos.
- **Raras (HPO):** añadir al dataset un gold clínico sin gen ni subtipo
  molecular («BBS9-related BBS» → «BBS») para los casos cuya entrada no trae
  datos genéticos. Sin eso, V5 penaliza en DDD aciertos que V4 contaba vía
  SapBERT.
- **Validar la escala con David** sobre los casos que cambian entre V4 y V5.
