# DxGPT Evaluation Framework

A systematic pipeline for benchmarking AI models on medical diagnosis tasks. The framework presents clinical cases to LLMs, generates differential diagnoses (DDX), and evaluates them against gold-standard diagnoses using medical ontologies (SNOMED, ICD-10, OMIM, ORPHA), BERT semantic similarity, and an LLM judge.

---

## How it works

```
Clinical case (text)
        │
        ▼
[1. Emulator]    LLM generates a ranked list of up to 10 differential diagnoses
        │
        ▼
[2. Medlabeler]  Azure Text Analytics assigns SNOMED / ICD-10 / OMIM / ORPHA codes
        │
        ▼
[3. Evaluator]   Compares DDX against gold diagnosis via SNOMED → ICD-10 → BERT → LLM judge
        │
        ▼
  summary.json + evaluation_details.txt
```

**Metrics:**
- `average_position` — mean rank at which the correct diagnosis appears (lower = better)
- `success_rate` — % of cases where the correct diagnosis appears anywhere in the DDX list

---

## Quick Start

### 1. Install dependencies

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure credentials

```powershell
cp .env.example .env
# Edit .env with your Azure credentials
```

Required variables:
```env
AZURE_LANGUAGE_ENDPOINT=...
AZURE_LANGUAGE_KEY=...
AZURE_OPENAI_ENDPOINT=...
AZURE_OPENAI_API_KEY=...
SAPBERT_ENDPOINT_URL=...        # optional — falls back to LLM judge if offline
```

### 3. Configure the run

Edit `bench/pipelines/pipeline_v4 - fork/main/config.yaml`:

```yaml
DATASET_PATH: "bench/datasets/all_275.json"
DXGPT_EMULATOR:
  MODEL: "gpt-4o"
  PARAMS:
    temperature: 0.1
    max_tokens: 12000
TRANSLATE_CASE:
  ENABLED: true
JUDGE_MODEL: "gemini-2.5-pro"
```

### 4. Run

```powershell
cd "bench/pipelines/pipeline_v4 - fork/main"
python main.py
```

Results are written to `output/<dataset>/<prompt>/<model>/<timestamp>/`.

---

## Benchmark Results

The full ranking with all runs, per-model breakdown, fixed parameters, and run metadata is maintained in [`rankingV2.txt`](bench/pipelines/pipeline_v4%20-%20fork/main/output/rankingV2.txt).

Models evaluated include gemini-2.5-pro, grok-4.1-fast-reasoning, gpt-5.1, gpt-5.2, gpt-5.4-mini, gpt-5-mini, gpt-4o, o3, and gemini-3-pro-preview, across datasets of 150 and 275 clinical cases.

---

## Repository Structure

```
eval/
├── bench/
│   ├── datasets/                        # Evaluation datasets (gitignored)
│   ├── candidate-prompts/               # Prompt templates
│   ├── validation_checks.py             # Dataset QA script
│   └── pipelines/
│       ├── pipeline_v4 - fork/main/     # ← Active pipeline
│       ├── pipeline_v1 - icd10/         # [Legacy]
│       ├── pipeline_v2 - icd10 + bert/  # [Legacy]
│       └── pipeline_v3 - full LLM/      # [Legacy]
│
├── data29/
│   └── data-repos/raw/                  # Raw source datasets (gitignored)
│
└── utils/
    ├── llm/                             # Azure OpenAI client
    ├── bert/                            # SapBERT similarity
    └── icd10/                           # ICD-10 taxonomy
```

---

## Key Documents

| Document | Purpose |
|----------|---------|
| `bench/pipelines/pipeline_v4 - fork/main/GUIA_EVALUACION.md` | Step-by-step guide to run an evaluation |
| `docs/pipeline/experiment-log.md` | Experiment log and ablation analysis |
| `docs/ROADMAP.md` | Full roadmap toward Nature paper dataset integration |
| `docs/analysis/run-analysis-notes.md` | Qualitative analysis of failed cases per run |
| `.squad/decisions.md` | Architectural decisions from the multidisciplinary team |

---

*Foundation 29 — advancing responsible medical AI evaluation.*
