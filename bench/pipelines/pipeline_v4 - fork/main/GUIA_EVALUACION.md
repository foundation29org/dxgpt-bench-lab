# Guia de Evaluacion - Pipeline V4

Esta guia es el runbook operativo del pipeline actual. Su objetivo es explicar como lanzar, reanudar e interpretar runs.

No es la fuente canonica del benchmark. Para resultados y recomendaciones actuales usa:

- `bench/pipelines/pipeline_v4 - fork/main/README.md`
- `docs/ROADMAP.md`
- `bench/pipelines/pipeline_v4 - fork/main/output/rankingV2.txt`

## 1. Antes de ejecutar

### Requisitos

- Tener el repo preparado en `C:\repos\DxGPT\eval`
- Tener un `.env` en la raiz del repo: `C:\repos\DxGPT\eval\.env`
- Tener accesible el dataset referenciado en `DATASET_PATH`

Variables habituales:

```env
AZURE_LANGUAGE_ENDPOINT=...
AZURE_LANGUAGE_KEY=...
AZURE_OPENAI_ENDPOINT=...
AZURE_OPENAI_API_KEY=...
AZURE_OPENAI_API_VERSION=2024-02-15-preview
GOOGLE_API_KEY=...
GOOGLE_GENAI_API_KEY=...
AZURE_TRANSLATOR_KEY=...
AZURE_TRANSLATOR_ENDPOINT=...
AZURE_TRANSLATOR_REGION=...
HF_TOKEN=...
SAPBERT_ENDPOINT_URL=...
```

Instalacion:

```powershell
py -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### Dataset recomendado

Para nuevos benchmarks narrativos, usa:

```yaml
DATASET_PATH: "bench/datasets/all_256_clean.json"
```

Para comparativa tipo DeepRare, usa uno de los datasets HPO (`ramedis_hpo`, `lirical_hpo`, `hms_hpo`, `mme_hpo`, `mygene2_hpo`, `ddd_hpo`).

`all_275.json` y otros historicos deben tratarse como referencia o auditoria, no como baseline nuevo.

## 2. Que documento mirar para cada cosa

- `README.md` del pipeline: estado actual del benchmark, tablas y recomendacion de modelos
- `GUIA_EVALUACION.md`: como ejecutar el pipeline
- `docs/ROADMAP.md`: historia del proyecto, fases y decisiones
- `output/rankingV2.txt`: ranking completo de runs

## 3. Configuracion minima

El pipeline puede usar `config.yaml` o un fichero especifico pasado con `--config`.

### Ejemplo narrativo recomendado

```yaml
EXPERIMENT_NAME: "all_256_clean-gpt54mini-low"
DATASET_PATH: "bench/datasets/all_256_clean.json"

DXGPT_EMULATOR:
  MODEL: "gpt-5.4-mini"
  CANDIDATE_PROMPT_PATH: "bench/candidate-prompts/juanjo_classic_v2.txt"
  PARAMS:
    temperature: 0.1
    max_tokens: 12000
    reasoning_effort: "low"
  TRANSLATE_CASE:
    ENABLED: true
  PARALLEL_WORKERS: 8

EVALUATOR:
  BERT_ACCEPTANCE_THRESHOLD: 0.80
  BERT_AUTOCONFIRM_THRESHOLD: 0.90
  ENABLE_ICD10_PARENT_SEARCH: true
  ENABLE_ICD10_SIBLING_SEARCH: true
  JUDGE_MODEL: "gemini-2.5-pro"
  JUDGE_PARAMS:
    thinking_level: "low"
    max_tokens: 10000
    temperature: 0.1
  PARALLEL_WORKERS: 8

MAIN:
  SHOULD_EMULATE: true
  SHOULD_LABEL: true
  SHOULD_EVALUATE: true
```

### Ejemplo HPO recomendado

```yaml
EXPERIMENT_NAME: "ddd_hpo-gemini3pro-low"
DATASET_PATH: "bench/datasets/ddd_hpo.json"

DXGPT_EMULATOR:
  MODEL: "gemini-3-pro-preview"
  CANDIDATE_PROMPT_PATH: "bench/candidate-prompts/juanjo_classic_v2.txt"
  PARAMS:
    temperature: 0.1
    max_tokens: 12000
    thinking_level: "low"
  TRANSLATE_CASE:
    ENABLED: false
  PARALLEL_WORKERS: 4

EVALUATOR:
  JUDGE_MODEL: "gemini-2.5-pro"
  JUDGE_PARAMS:
    thinking_level: "low"
    max_tokens: 10000
    temperature: 0.1
  PARALLEL_WORKERS: 8

MAIN:
  SHOULD_EMULATE: true
  SHOULD_LABEL: true
  SHOULD_EVALUATE: true
```

### Reglas practicas de configuracion

- `JUDGE_MODEL` afecta a la comparabilidad. Si cambias el juez, cambia el experimento.
- `JUDGE_PARAMS` conviene fijarlos explicitamente, no dejar logica implicita.
- `thinking_level=medium` en Gemini ya se cerro como experimento y no se recomienda para produccion ni benchmark. Mantener `low`.
- `reasoning_effort=low` es el punto de partida recomendado para GPT-5.x y o3.
- `TRANSLATE_CASE.ENABLED: false` suele ser lo correcto para datasets HPO ya en ingles.
- `PARALLEL_WORKERS` existe tanto en emulador como en evaluador. Ajustalo al rate limit real del proveedor.

## 4. Como ejecutar

Desde el directorio del pipeline:

```powershell
cd "C:\repos\DxGPT\eval\bench\pipelines\pipeline_v4 - fork\main"
py validate.py
py main.py
```

Con un config dedicado:

```powershell
cd "C:\repos\DxGPT\eval\bench\pipelines\pipeline_v4 - fork\main"
py main.py --config config_mi_experimento.yaml
```

## 5. Como reanudar o re-evaluar

El pipeline detecta automaticamente el estado de la carpeta de salida del experimento:

- Si ya existe el JSON del emulador, te ofrece continuar desde labeling
- Si ya existe el JSON del labeler, te ofrece continuar desde evaluation
- Si abortas, no borra los artefactos ya generados

Casos tipicos:

| Objetivo | SHOULD_EMULATE | SHOULD_LABEL | SHOULD_EVALUATE |
|---|---|---|---|
| Run completo | `true` | `true` | `true` |
| Solo generar DDX | `true` | `false` | `false` |
| Generar DDX y codigos | `true` | `true` | `false` |
| Solo re-evaluar desde JSON ya etiquetado | `false` | `false` | `true` |

Nota importante: para reproducibilidad fuerte, la fuente de verdad del run no es el `config.yaml` suelto del directorio, sino el snapshot guardado por el pipeline en:

- `output/<dataset>/<prompt>/<model>/<prompt>___<model>___config.yaml`
- `output/<dataset>/<prompt>/<model>/<timestamp>/<prompt>___<model>___config.yaml`

## 6. Que genera el pipeline

Estructura normal:

```text
output/
└── <dataset>/
    └── <prompt>/
        └── <model>/
            ├── <prompt>___<model>___ddxs_from_labeler.json
            ├── <prompt>___<model>___config.yaml
            ├── emulator.log
            ├── medlabeler.log
            └── <timestamp>/
                ├── evaluation.log
                ├── evaluation_details.txt
                ├── summary.json
                └── <prompt>___<model>___config.yaml
```

## 7. Como interpretar los resultados

### `summary.json`

Campos mas utiles:

- `matched_cases` / `unmatched_cases`
- `top_counts`
- `average_position`
- `final_score_percentage`
- `resolution_method_counts`

Interpretacion rapida:

- `average_position`: cuanto mas bajo, mejor
- `final_score_percentage`: cobertura total del diagnostico correcto dentro del DDX
- `P1`, `P2`, `P3`... permiten derivar `Recall@1`, `Recall@3`, `Recall@5`
- `resolution_method_counts` indica cuanto resuelve SNOMED, ICD-10, BERT o juez LLM

### `evaluation.log`

Sirve para seguir el resultado caso a caso y detectar:

- muchos `NO_MATCH` o `REJECTED`
- exceso de `LLM_JUDGMENT`
- errores de rate limit o credenciales

### `evaluation_details.txt`

Sirve para auditoria fina. Usalo cuando quieras responder preguntas como:

- por que un caso no matcheo
- por que un P1 paso a P3
- si el juez esta siendo demasiado permisivo
- si BERT esta resolviendo poco por estar offline o mal configurado

## 8. Recomendaciones operativas actuales

- Modo normal en OpenAI: `gpt-5.4-mini low`
- Modo avanzado: `gemini-3-pro-preview low`
- Juez por defecto para benchmark: `gemini-2.5-pro`
- Prompt de referencia: `bench/candidate-prompts/juanjo_classic_v2.txt`
- Dataset narrativo de referencia: `all_256_clean`

## 9. Troubleshooting

### Falta `.env` o credenciales

- Verifica que el `.env` esta en `C:\repos\DxGPT\eval\.env`
- Revisa variables `AZURE_*`, `GOOGLE_*`, `HF_TOKEN` y `SAPBERT_ENDPOINT_URL`

### Error de modulos o dependencias

```powershell
pip install -r requirements.txt
py validate.py
```

### Muchos `REJECTED` o `NO_MATCH`

- Revisa `evaluation_details.txt`
- Comprueba que el dataset es el esperado
- Verifica si SapBERT esta activo
- Confirma que el juez es comparable con otros runs

### Rate limits o latencia alta

- Baja `PARALLEL_WORKERS`
- Cambia de region o deployment si el proveedor esta degradado
- Para GPT-5-mini, no asumir que la latencia historica sigue siendo valida

### Resultados no comparables con otro run

Revisa siempre:

- dataset
- prompt
- modelo
- `JUDGE_MODEL`
- `JUDGE_PARAMS`
- `TRANSLATE_CASE`
- thresholds BERT

Si cambia cualquiera de esos bloques, no compares como si fuera el mismo experimento.

## 10. Regla editorial del repo

Si actualizas instrucciones operativas, hazlo aqui.

Si actualizas resultados, recomendaciones de modelos o conclusiones del benchmark, hazlo en:

- `bench/pipelines/pipeline_v4 - fork/main/README.md`
- `docs/ROADMAP.md`
- `output/rankingV2.txt`
