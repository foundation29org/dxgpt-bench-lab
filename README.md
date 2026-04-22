# DxGPT Evaluation Framework

A systematic pipeline for benchmarking AI models on medical diagnosis tasks. The framework presents clinical cases to LLMs, generates differential diagnoses (DDX), and evaluates them against gold-standard diagnoses using medical ontologies (SNOMED, ICD-10, OMIM, ORPHA), BERT semantic similarity, and an LLM judge.

---

## How it works

```
Clinical case (text or HPO list)
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
- `Recall@K` — % of cases where the correct diagnosis appears in the top K positions (K=1,3,5)

---

## Two evaluation tracks

### Track A — Free clinical text (narrative)
Input is a narrative clinical description (age, history, symptoms, exams) — as used in real DxGPT production. Evaluated on `all_256_clean` (256 QA-validated cases). Primary metric: `average_position` and `success_rate`.

**Top results (all_256_clean, judge: gemini-2.5-pro):**

| Model | Avg Pos | Success% |
|-------|---------|----------|
| gemini-2.5-pro low | **1.299** | 98.1% |
| gemini-3-pro-preview low | **1.299** | 98.1% |
| gemini-2.5-flash low | 1.434 | 98.1% |
| grok-4.1-fast-reasoning | 1.448 | 97.7% |
| gpt-5.4 full low | 1.502 | 98.8% |
| gpt-5.4-mini low | 1.526 | 98.1% |

### Track B — HPO symptom lists (structured)
Input is a comma-separated list of HPO terms (e.g. `"Seizures, Microcephaly, Hypotonia"`) — the same format used by the DeepRare Nature paper. Enables direct comparison against state-of-the-art rare disease systems. Primary metric: `Recall@K`.

**Top results (gemini-3-pro-preview, judge: gemini-2.5-pro):**

| Dataset | Cases | R@1 | R@3 | R@5 |
|---------|-------|-----|-----|-----|
| DDD (G2P) | 1,749 | **70.3%** | **97.6%** | 98.1% |
| MME | 40 | **77.5%** | **97.5%** | 97.5% |
| HMS | 88 | **72.7%** | **100%** | 100% |
| LIRICAL | 370 | **67.8%** | **98.1%** | 98.9% |
| MyGene2 | 146 | **61.0%** | **95.9%** | 95.9% |
| RAMEDIS | 624 | **54.3%** | **98.2%** | 98.7% |

> Track A and Track B results are **not comparable** — they use different input formats and metrics. Full ranking: [`rankingV2.txt`](bench/pipelines/pipeline_v4%20-%20fork/main/output/rankingV2.txt).

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
# Edit .env with your API credentials
```

Required variables:
```env
AZURE_LANGUAGE_ENDPOINT=...
AZURE_LANGUAGE_KEY=...
AZURE_OPENAI_ENDPOINT=...
AZURE_OPENAI_API_KEY=...
GOOGLE_API_KEY=...              # for Gemini models and judge
SAPBERT_ENDPOINT_URL=...        # optional — falls back to LLM judge if offline
```

### 3. Configure the run

Edit `bench/pipelines/pipeline_v4 - fork/main/config.yaml` or create a dedicated config file:

```yaml
DATASET_PATH: "bench/datasets/all_256_clean.json"

DXGPT_EMULATOR:
  MODEL: "gemini-3-pro-preview"   # recommended for best quality
  CANDIDATE_PROMPT_PATH: "bench/candidate-prompts/juanjo_classic_v2.txt"
  PARAMS:
    temperature: 0.1
    max_tokens: 12000
    thinking_level: "low"         # "low" | "medium" — for Gemini models
  TRANSLATE_CASE:
    ENABLED: true

EVALUATOR:
  JUDGE_MODEL: "gemini-2.5-pro"

MAIN:
  SHOULD_EMULATE: true
  SHOULD_LABEL: true
  SHOULD_EVALUATE: true
```

### 4. Run

```powershell
cd "bench/pipelines/pipeline_v4 - fork/main"
python main.py                              # uses config.yaml
python main.py --config my_config.yaml     # or a specific config
```

Results are written to `output/<dataset>/<prompt>/<model>/<timestamp>/`.

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
│       │   ├── main.py
│       │   ├── emulator.py
│       │   ├── medlabeler.py
│       │   ├── config.yaml              # Default config (only one kept in repo)
│       │   └── output/                  # All run results — each run dir
│       │                                # contains its own *___config.yaml snapshot
│       │                                # (full reproducibility without per-experiment
│       │                                # configs cluttering the pipeline root)
│       ├── pipeline_v1 - icd10/         # [Legacy]
│       ├── pipeline_v2 - icd10 + bert/  # [Legacy]
│       └── pipeline_v3 - full LLM/      # [Legacy]
│
├── data29/
│   └── data-repos/raw/                  # Raw source datasets (gitignored)
│
├── docs/
│   ├── ROADMAP.md                       # Full project roadmap
│   └── benchmark-report.html            # Executive benchmark report
│
└── utils/
    ├── llm/                             # LLM clients (Azure OpenAI, Gemini, Claude)
    ├── bert/                            # SapBERT similarity
    └── icd10/                           # ICD-10 taxonomy
```

---

## Key Documents

| Document | Purpose |
|----------|---------|
| `docs/benchmark-report.html` | Executive benchmark report — summary of all results for stakeholders |
| `docs/ROADMAP.md` | Full roadmap toward Nature paper dataset integration and publication |
| `bench/pipelines/pipeline_v4 - fork/main/output/rankingV2.txt` | Complete run history with all metrics and parameters |
| `bench/pipelines/pipeline_v4 - fork/main/GUIA_EVALUACION.md` | Step-by-step guide to run an evaluation |
| `docs/pipeline/experiment-log.md` | Experiment log and ablation analysis |
| `.squad/decisions.md` | Architectural decisions from the multidisciplinary team |

---

*Foundation 29 — advancing responsible medical AI evaluation.*
