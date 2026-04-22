# DxGPT Evaluation Framework

Repositorio de evaluacion para benchmarking de modelos LLM en diagnostico diferencial medico.

El pipeline actual toma un caso clinico o una lista HPO, genera un diferencial, lo codifica con ontologias medicas y evalua el resultado contra el gold diagnosis usando SNOMED, ICD-10, SapBERT y un juez LLM.

## Flujo del pipeline

```text
Clinical case or HPO list
        |
        v
[1. Emulator]    LLM genera un DDX rankeado
        |
        v
[2. Medlabeler]  Azure Text Analytics asigna SNOMED / ICD-10 / OMIM / ORPHA
        |
        v
[3. Evaluator]   SNOMED -> ICD-10 -> BERT -> juez LLM
        |
        v
summary.json + evaluation_details.txt + rankingV2.txt
```

## Estado actual

- Benchmark narrativo canonico: `all_256_clean`
- Mejor opcion OpenAI para produccion normal: `gpt-5.4-mini low`
- Mejor opcion avanzada: `gemini-3-pro-preview low`
- `thinking_level=medium` en Gemini se considero cerrado y no se recomienda

La fuente canonica de resultados vivos no es este README, sino:

- `bench/pipelines/pipeline_v4 - fork/main/README.md`
- `docs/ROADMAP.md`
- `bench/pipelines/pipeline_v4 - fork/main/output/rankingV2.txt`

## Documentacion canonica

| Documento | Rol |
|---|---|
| `README.md` | Entrada general al repo |
| `docs/README.md` | Mapa de documentacion y clasificacion canonica/historica |
| `bench/pipelines/pipeline_v4 - fork/main/README.md` | Estado actual del benchmark y recomendaciones de modelos |
| `bench/pipelines/pipeline_v4 - fork/main/GUIA_EVALUACION.md` | Runbook operativo para ejecutar y reanudar runs |
| `docs/ROADMAP.md` | Roadmap, fases y decisiones del proyecto |
| `docs/benchmark-report.html` | Informe ejecutivo para stakeholders |
| `docs/pipeline/experiment-log.md` | Bitacora tecnica y trazabilidad de experimentos |
| `docs/pipeline/methodology-notes.md` | Alineacion de metricas publicas y claims historicos |
| `docs/analysis/run-analysis-notes.md` | Analisis cualitativo de runs |
| `docs/archive/README.md` | Documentacion historica archivada |

## Quick Start

### 1. Preparar entorno

```powershell
py -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configurar credenciales

```powershell
Copy-Item .env.example .env
```

Rellena al menos:

```env
AZURE_LANGUAGE_ENDPOINT=...
AZURE_LANGUAGE_KEY=...
AZURE_OPENAI_ENDPOINT=...
AZURE_OPENAI_API_KEY=...
GOOGLE_API_KEY=...
SAPBERT_ENDPOINT_URL=...
```

### 3. Lanzar un run

```powershell
cd "bench/pipelines/pipeline_v4 - fork/main"
py validate.py
py main.py
```

O con un config especifico:

```powershell
py main.py --config config_mi_experimento.yaml
```

Los resultados quedan en `output/<dataset>/<prompt>/<model>/<timestamp>/`.

## Datasets y tracks

### Track A - texto clinico narrativo

- Dataset de referencia: `bench/datasets/all_256_clean.json`
- Uso: comparativa cercana al caso real de produccion
- Metricas principales: `average_position` y cobertura

### Track B - listas HPO

- Datasets tipo `*_hpo.json` y `ddd_hpo.json`
- Uso: comparativa con DeepRare y otros benchmarks de enfermedades raras
- Metricas principales: `Recall@1`, `Recall@3`, `Recall@5`

Los dos tracks no son comparables entre si.

## Estructura del repositorio

```text
eval/
├── bench/
│   ├── datasets/
│   ├── candidate-prompts/
│   └── pipelines/
│       └── pipeline_v4 - fork/main/     <- pipeline activo
├── docs/
│   ├── README.md
│   ├── ROADMAP.md
│   ├── benchmark-report.html
│   └── archive/
├── data29/
└── utils/
```

## Nota sobre reproducibilidad

Tras la limpieza del repo, los configs sueltos de experimentos ya no se conservan en la raiz del pipeline. La fuente de verdad para reejecutar o auditar un run es el snapshot guardado junto a sus resultados:

- `output/<dataset>/<prompt>/<model>/<prompt>___<model>___config.yaml`
- `output/<dataset>/<prompt>/<model>/<timestamp>/<prompt>___<model>___config.yaml`

Esto mantiene trazabilidad sin volver a llenar la raiz del pipeline de `config_*.yaml`.
