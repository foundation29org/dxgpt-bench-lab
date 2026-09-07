# DxGPT Evaluation Framework

Repository for benchmarking LLMs on medical differential-diagnosis tasks.

The current pipeline takes either a clinical case or an HPO symptom list, generates a ranked differential, maps it to medical ontologies, and evaluates the result against the gold diagnosis using SNOMED, ICD-10, SapBERT, and an LLM judge.

## Pipeline Flow

```text
Clinical case or HPO list
        |
        v
[1. Emulator]    LLM generates a ranked DDX
        |
        v
[2. Medlabeler]  Azure Text Analytics assigns SNOMED / ICD-10 / OMIM / ORPHA
        |
        v
[3. Evaluator]   SNOMED -> ICD-10 -> BERT -> LLM judge
        |
        v
summary.json + evaluation_details.txt + rankingV2.txt
```

## Current Status

- Canonical narrative benchmark: `all_256_clean`
- Best OpenAI option for normal production use: `gpt-5.4-mini low`
- Best advanced option: `gemini-3-pro-preview low`
- Gemini `thinking_level=medium` has been tested and is not recommended

The canonical sources for live results are not this README, but:

- `bench/pipelines/pipeline_v4 - fork/main/README.md`
- `docs/ROADMAP.md`
- `bench/pipelines/pipeline_v4 - fork/main/output/rankingV2.txt`

## Canonical Documentation

| Document | Role |
|---|---|
| `README.md` | General entry point to the repo |
| `docs/README.md` | Documentation map and canonical/historical classification |
| `bench/pipelines/pipeline_v4 - fork/main/README.md` | Current benchmark state and model recommendations |
| `bench/pipelines/pipeline_v4 - fork/main/GUIA_EVALUACION.md` | Operational runbook for launching and resuming runs |
| `docs/ROADMAP.md` | Project roadmap, phases, and decisions |
| `docs/benchmark-report.html` | Executive report for stakeholders |
| `docs/pipeline/experiment-log.md` | Technical log and experiment traceability |
| `docs/pipeline/methodology-notes.md` | Alignment of public metrics and historical claims |
| `docs/analysis/run-analysis-notes.md` | Qualitative run analysis |
| `docs/archive/README.md` | Archived historical documentation |

## Quick Start

### 1. Prepare the environment

```powershell
py -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure credentials

```powershell
Copy-Item .env.example .env
```

Fill in at least:

```env
AZURE_LANGUAGE_ENDPOINT=...
AZURE_LANGUAGE_KEY=...
AZURE_OPENAI_ENDPOINT=...
AZURE_OPENAI_API_KEY=...
GOOGLE_API_KEY=...
SAPBERT_ENDPOINT_URL=...
```

### 3. Launch a run

```powershell
cd "bench/pipelines/pipeline_v4 - fork/main"
py validate.py
py main.py
```

Or with a specific config:

```powershell
py main.py --config config_my_experiment.yaml
```

Results are written to `output/<dataset>/<prompt>/<model>/<timestamp>/`.

## Datasets and Tracks

### Track A - Narrative Clinical Text

- Reference dataset: `bench/datasets/all_256_clean.json`
- Use case: closest benchmark to the real production workflow
- Primary metrics: `average_position` and coverage

### Track B - HPO Lists

- Datasets such as `*_hpo.json` and `ddd_hpo.json`
- Use case: comparison against DeepRare and other rare-disease benchmarks
- Primary metrics: `Recall@1`, `Recall@3`, `Recall@5`

The two tracks are not directly comparable.

## Repository Structure

```text
eval/
├── bench/
│   ├── datasets/
│   ├── candidate-prompts/
│   └── pipelines/
│       └── pipeline_v4 - fork/main/     <- active pipeline
├── docs/
│   ├── README.md
│   ├── ROADMAP.md
│   ├── benchmark-report.html
│   └── archive/
├── data29/
└── utils/
```

## Reproducibility Note

After the repo cleanup, loose per-experiment config files are no longer kept in the pipeline root. The source of truth for reproducing or auditing a run is the snapshot stored with its outputs:

- `output/<dataset>/<prompt>/<model>/<prompt>___<model>___config.yaml`
- `output/<dataset>/<prompt>/<model>/<timestamp>/<prompt>___<model>___config.yaml`

This preserves traceability without cluttering the pipeline root with `config_*.yaml` files again.
