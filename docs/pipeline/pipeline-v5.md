# Pipeline V5: cómo se evalúa hoy DxGPT

**Estado:** evaluador vigente desde el 28-oct-2026. Código en
`bench/pipelines/pipeline_v5/main`. Pipeline V4 se mantiene, sin tocar, para
la serie histórica.

Este documento explica cómo funciona el pipeline actual. El *porqué* de cada
decisión (la discusión de la rúbrica del juez con Julián, los problemas que se
encontraron en V4 y lo que se acordó) está en
[JULIAN_HARNESS_REVIEW.md](../../bench/multimodal_beta/JULIAN_HARNESS_REVIEW.md),
§9–§12. Los resultados están en
[benchmark-report-v5.html](../benchmark-report-v5.html) y en el
[README de V5](../../bench/pipelines/pipeline_v5/main/README.md).

## Qué mide

Para cada caso clínico, el modelo evaluado devuelve una lista ordenada de
diagnósticos (el diferencial). El pipeline compara esa lista con el
diagnóstico de referencia del caso (el *gold*) y dice en qué posición de la
lista aparece la misma enfermedad, si aparece.

Con eso se calculan:

| Métrica | Qué significa |
|---|---|
| **R@1** | % de casos en los que el primer diagnóstico de la lista es el correcto. Es la cifra principal |
| **R@3**, **R@5** | % de casos con el correcto entre los 3 o los 5 primeros |
| **Cobertura** | % de casos con el correcto en cualquier posición. Solo es comparable entre modelos que dan listas de la misma longitud |
| **Posición media** | Media de la posición del acierto, solo en los casos acertados |
| **MRR** | Media de 1/posición (0 si no acierta): premia acertar arriba |

Cada métrica sale en dos lecturas:

- **Estricta:** solo cuenta la misma enfermedad (nota 2 del juez). Es la
  oficial.
- **Laxa:** cuenta también las enfermedades relacionadas (nota 1). Es de uso
  interno hasta que David valide dónde está la frontera entre 1 y 0.

## Las tres etapas

```text
dataset (casos + gold)
   │
   ▼
1. Emulador ── el modelo genera la lista de diagnósticos
   │            (prompt juanjo_classic_v2; traduce al inglés si hace falta)
   ▼
2. Labeler ─── Azure Text Analytics for Health pone códigos a cada diagnóstico
   │            (SNOMED, ICD-10, OMIM, ORPHA)
   ▼
3. Evaluador ─ compara cada opción con cada gold: código SNOMED idéntico
                o nota del juez (Gemini 2.5 Pro) → posición del acierto
```

El emulador y el labeler son los de V4. Lo que cambia en V5 es el evaluador.

### 1. Emulador (`emulator.py`)

- Rellena el prompt candidato (`bench/candidate-prompts/juanjo_classic_v2.txt`)
  con el texto del caso y llama al modelo con los parámetros de la
  configuración (`reasoning_effort` en OpenAI, Claude y Grok;
  `thinking_level` en Gemini).
- Si `TRANSLATE_CASE` está activo, traduce el caso al inglés con Azure
  Translator antes de enviarlo (los casos de urgencias están en español).
- Extrae la lista de diagnósticos de la respuesta. Reintenta los errores
  transitorios de la API.
- Escribe `*___ddxs_from_emulator.json`.

### 2. Labeler (`medlabeler.py`)

- Envía cada diagnóstico de la lista a Azure Text Analytics for Health y
  guarda los códigos SNOMED, ICD-10, OMIM y ORPHA que reconoce.
- Escribe `*___ddxs_from_labeler.json`, que es la entrada del evaluador: el
  caso, su gold y la lista con códigos.
- En `narrative_v2` el gold no lleva códigos, así que los códigos de la lista
  no deciden nada: todo lo decide el juez. Se conservan para auditar.

### 3. Evaluador (`evaluator.py`)

Para cada caso y para cada gold del caso:

1. **Códigos.** Si una opción comparte un código SNOMED con el gold, esa opción
   recibe un 2 sin preguntar al juez. Es la única capa automática (regla C1).
   La relación ICD-10 (mismo código, hijo, padre, hermano) se calcula y se
   guarda como dato, pero no puntúa.
2. **Juez.** Gemini 2.5 Pro recibe el gold tal como está en el dataset (más sus
   `accepted_names`, como «also known as») y la lista entera, y devuelve una
   nota por opción en JSON. Si la respuesta no es válida o la llamada falla,
   reintenta hasta `JUDGE_MAX_ATTEMPTS` veces.
3. **Nota final de cada opción:** 2 si hay SNOMED idéntico; si no, la nota del
   juez.

Después, para el caso:

- **Posición estricta** = la primera opción con nota 2, buscando en todos los
  gold del caso (si hay varios, basta con acertar uno: regla C3).
- **Posición laxa** = la primera opción con nota 1 o 2.

El juez dice también si el gold es una enfermedad (`reference_is_disease`).
No cambia la nota: sirve para encontrar gold mal formulados («Blindness»,
«Chest pain»).

## La rúbrica del juez (`graded_v2`)

El prompt está en `GradedEvaluator._build_judge_prompt`. En resumen:

| Nota | Cuándo |
|---|---|
| **2 · misma enfermedad** | Sinónimos, abreviaturas y variantes de escritura. Una forma más específica solo si todo paciente con la opción tiene el gold: un subtipo del gold, o el gold con lateralidad o extensión. «X con Y» (Y es complicación o manifestación) se acierta con «X», y «hallazgo debido a X» también con «X» |
| **1 · relacionada** | Categoría más amplia; omite un calificador que define el gold («GIST» frente a «GIST maligno»); otro subtipo, gen o fenotipo de la misma familia; causa, complicación, precursor o consecuencia; disyuntiva «A o B» que incluye el gold |
| **0 · otra enfermedad** | No se da crédito por una presentación parecida, la misma zona anatómica, el mismo mecanismo o el mismo tratamiento |

Reglas acordadas con Julián (§12 de JULIAN_HARNESS_REVIEW.md):

| Regla | Qué dice |
|---|---|
| C1 | Solo SNOMED idéntico decide sin juez. ICD-10 no, porque agrupa enfermedades distintas bajo un mismo código |
| C2 | «X con Y» y «hallazgo debido a X» se aciertan con «X» |
| C3 | Con varios gold, basta con acertar uno (sinónimos o diagnósticos simultáneos) |
| C4 | Los gold amplios se aciertan con una forma más específica |

## El gold

El evaluador lee los gold del campo `diagnoses` de cada caso:

```json
"diagnoses": [
  {"name": "Erdheim-Chester disease", "role": "principal", "accepted_names": ["ECD"]},
  {"name": "Respiratory failure", "role": "secondary"}
]
```

- `name` es lo que ve el juez, tal como está escrito. V4 usaba el texto
  normalizado por Azure, que a veces nombraba otra enfermedad («Cystic
  fibrosis with bronchiectasis» → «Bronchiectasis»).
- `accepted_names` son otros nombres de la misma enfermedad.
- El evaluador puntúa todos los gold por igual; `role` es informativo:
  - en urgencias (`narrative_v2`, bloque `urg`), los otros diagnósticos de la
    misma visita van con `role: secondary` y cuentan como acierto;
  - en raras (HPO v2), además del gold con gen («BBS9-related Bardet-Biedl
    syndrome») vale el nombre de la enfermedad sin gen («Bardet-Biedl
    syndrome»), porque la entrada es una lista de síntomas sin datos
    genéticos. Ese nombre sin gen va con `role: clinical`.
    `score_blocks.py --without-clinical` lo ignora y da la nota solo con el
    gold con gen, sobre las mismas llamadas al juez. Solo se hace en raras.

## Qué cambia respecto a V4

| | V4 strict | V5 |
|---|---|---|
| SNOMED idéntico | acierto sin juez | acierto sin juez (igual) |
| ICD-10 idéntico, hijo, padre, hermano | acierto sin juez | no deciden: se guardan y decide el juez |
| SapBERT (parecido de nombres) | ≥ 0,90 acierta solo; ≥ 0,80 adelanta la posición | no se usa |
| Cuándo entra el juez | solo si ninguna capa acierta | en todos los casos |
| Qué responde el juez | una posición (0 = ninguna) | una nota 2/1/0 por opción |
| Posición del acierto | la de la primera capa que acierta | la mejor entre códigos y juez |
| Texto del gold | normalizado por Azure | el del dataset, con sus nombres aceptados |
| Lecturas | una | estricta y laxa |

Efecto medido con las mismas listas de Terra en `all_256_clean`: R@1 sube de
63,3 % a 69,1 % (V4 ponía a veces el acierto más abajo por un hermano ICD) y
R@5 baja de 83,2 % a 81,2 % (salen aciertos de padres y hermanos ICD que eran
otra enfermedad). Detalle en el README de V5.

## Datasets

| Dataset | Casos | Uso |
|---|---:|---|
| `narrative_v2` v0.1 | 300 | Banco narrativo principal. Bloques: `live` (150 case reports de PubMed de jul–oct 2026), `urg` (60 urgencias en español), `exam` (60 viñetas de examen), `synth` (30 raras sintéticas). Cifra principal: `live`+`urg`. Pendiente de validación clínica ([README](../../data29/data-repos/narrative-v2/README.md)) |
| Raras HPO v2 | 3.006 | Seis datasets de listas HPO; además del gold con gen vale el nombre sin gen, y salen los gold dudosos de T3 ([README](../../data29/data-repos/hpo-v2/README.md)) |
| `all_256_clean` | 256 | Serie histórica, con V4 strict |

Las fechas de corte de los modelos y qué casos `live` pudo ver cada uno están
en `data29/data-repos/narrative-v2/model_cutoffs.yaml` y `live_dates.py`.

## Cómo se ejecuta

Desde `bench/pipelines/pipeline_v5/main`, con las claves en `eval/.env`.

**Run completo** (genera listas, códigos y nota):

```powershell
py main.py --config config_gpt61sol_low_narrative_v2.yaml
```

**Re-puntuar sin generar listas nuevas**, por ejemplo cuando David corrija el
gold de `narrative_v2` o para probar otro juez. Las listas no dependen del
gold, así que la diferencia se debe solo al evaluador o al gold:

```yaml
REUSE_LABELED_DDX: "<ruta al *___ddxs_from_labeler.json de un run anterior>"
REFRESH_GOLD_FROM_DATASET: true   # usa el gold actual de DATASET_PATH y quita los casos excluidos
MAIN:
  SHOULD_EMULATE: false
  SHOULD_LABEL: false
  SHOULD_EVALUATE: true
```

Ejemplos: `config_terra_low_all256.yaml` (mismas listas que V4) y
`config_terra_low_ddd_hpo_v2.yaml` y sus hermanos de raras.

**Herramientas:**

| Script | Para qué |
|---|---|
| `score_blocks.py` | R@1 y R@5 por bloque de `narrative_v2`, `live` sin los casos que el modelo pudo ver (`--live-dates`) y nota solo con el gold con gen, sin el nombre sin gen (`--without-clinical`) |
| `compare_runs.py` | Casos que cambian entre un run V4 y uno V5 con las mismas listas, agrupados por la capa de V4 que los decidía |
| `repair_judge_errors.py` | Vuelve a juzgar solo los casos en los que el juez falló tres veces (Gemini devuelve a veces 503) y reescribe las salidas del run |
| `build_report.py` | Regenera `docs/benchmark-report-v5.html` con los últimos runs |

### Claves de configuración

| Clave | Qué hace |
|---|---|
| `DATASET_PATH` | Dataset, relativo a la raíz de `eval` |
| `DXGPT_EMULATOR.MODEL` | Modelo evaluado (OpenAI vía Azure, Gemini, Claude o Grok según el nombre) |
| `DXGPT_EMULATOR.PARAMS` | `reasoning_effort` o `thinking_level`, `max_tokens`, `temperature` |
| `DXGPT_EMULATOR.TRANSLATE_CASE.ENABLED` | Traduce el caso al inglés antes de enviarlo |
| `DXGPT_EMULATOR.PARALLEL_WORKERS` | Casos en paralelo al generar |
| `EVALUATOR.JUDGE_MODEL`, `JUDGE_PARAMS` | Juez y sus parámetros (hoy Gemini 2.5 Pro, `thinking_level: low`, temperatura 0,1) |
| `EVALUATOR.JUDGE_MAX_ATTEMPTS`, `JUDGE_RETRY_DELAY_SECONDS` | Reintentos del juez |
| `EVALUATOR.PARALLEL_WORKERS` | Casos en paralelo al juzgar |
| `EVALUATOR.CASE_LIMIT` | Solo los primeros N casos (prueba rápida) |
| `REUSE_LABELED_DDX`, `REFRESH_GOLD_FROM_DATASET` | Re-puntuar listas de otro run, con el gold actual del dataset |
| `MAIN.SHOULD_EMULATE / SHOULD_LABEL / SHOULD_EVALUATE` | Qué etapas se ejecutan |

## Salidas

En `output/<dataset>/<prompt>/<modelo>/`:

- `*___config.yaml`: copia de la configuración usada (la fuente de verdad del run).
- `*___ddxs_from_emulator.json`, `*___ddxs_from_labeler.json`: listas y códigos.
- `emulator.log`, `medlabeler.log`.
- Una carpeta por evaluación (`<fecha>/`) con:
  - `evaluation_details.txt`: un bloque JSON por caso. `final_resolution`
    (estricta) y `lax_resolution` (laxa); `graded_trace` guarda, para cada gold
    y cada opción, el código idéntico si lo hay, la relación ICD-10, la nota del
    juez y la nota final;
  - `summary.json`: métricas en las dos lecturas y listas de auditoría
    (`code_judge_disagreements`, `icd10_relation_judge_grades`,
    `reference_not_disease`, `cases_with_judge_errors`);
  - `judge_metrics.json`: cada llamada al juez, con tokens, latencia y coste;
  - `evaluation.log`.

Los JSON con casos no se versionan (el repo es público).

## Coste y tiempo de referencia

Con 8 llamadas en paralelo:

| Run | Llamadas al juez | Coste del juez | Tiempo |
|---|---:|---:|---|
| `narrative_v2`, un modelo, run completo | ≈ 320 | ≈ 3–6 $ | 35–90 min (unos 20 son del labeler; los modelos lentos, como Opus 5, tardan más en generar) |
| Raras HPO v2, re-puntuar las seis | ≈ 4.500 | ≈ 64 $ | ≈ 1 h 20 min (DDD) |

A eso se suma el coste de generar las listas con el modelo evaluado.

## Límites conocidos

- **La escala 2/1/0 no está validada clínicamente.** David tiene que revisarla
  sobre casos de `narrative_v2`, sobre todo la frontera entre 1 y 0. Hasta
  entonces solo se publica la nota estricta.
- **El juez no es determinista del todo.** Repetir la evaluación puede mover
  unos pocos casos; no hay que leer diferencias de 1–2 casos como señal.
- **El juez decide casi todo.** Si cambia el modelo del juez, cambian las
  cifras. La elección del juez está pendiente (paso 6 del
  [ROADMAP](../ROADMAP.md)).
- **Los nombres sin gen de raras los propuso un LLM** y están pendientes de
  revisión clínica.
- **Listas de longitud distinta.** Claude Opus 5 devuelve unas 10 opciones y
  Gemini 3.1 Pro 3 o 4. Por eso se comparan R@1 y R@5, no la cobertura.
