# Pipeline V4 - Medical Diagnosis Evaluation System

## Overview

Pipeline de evaluación de modelos LLM para diagnóstico diferencial médico, con foco en enfermedades raras. Compara el rendimiento de DxGPT contra el paper de Nature [DeepRare (2025)](https://www.nature.com/articles/s41586-025-10097-9) usando los mismos datasets y métricas (Recall@K).

**Estado actual (2026-04-20):** Evaluación completa de 10+ modelos sobre `all_256_clean` (texto narrativo) y 6 datasets HPO del paper DeepRare. **gemini-2.5-pro supera el baseline GPT-4 del paper en los 6 datasets HPO (+5 a +32pp en Recall@1). DDD (1.749 casos): R@1=63.5%, R@3=91.8% con gemini-2.5-pro.**

### Datasets evaluados

| Dataset | Tipo | Casos | Fuente |
|---------|------|-------|--------|
| `all_256_clean` | Texto narrativo clínico | 256 | DxGPT interno (limpio) |
| `ramedis_hpo` | HPO terms | 624 | RareBench (HuggingFace) |
| `lirical_hpo` | HPO terms | 370 | RareBench (HuggingFace) |
| `hms_hpo` | HPO terms | 88 | RareBench (HuggingFace) |
| `mme_hpo` | HPO terms | 40 | RareBench (HuggingFace) |
| `mygene2_hpo` | HPO terms | 146 | Harvard Dataverse |
| `ddd_hpo` | HPO terms (G2P) | 1.749 | EBI Gene2Phenotype |

> Ver `docs/ROADMAP.md` para el plan completo y estado de los experimentos.

### Current Benchmark Results (2026-04-20)

> Full results in `output/rankingV2.txt`. All runs use prompt `juanjo_classic_v2`, judge `gemini-2.5-pro`, `temperature=0.1`, `BERT_accept=0.8/0.9`.

#### Track A — Narrative Clinical Text (`all_256_clean`, 256 casos)

| Rank | Model | Avg Pos ↓ | Success% | ~s/case | Notes |
|------|-------|-----------|----------|---------|-------|
| 🥇 | gemini-2.5-pro low | **1.299** | 98.1% | 27.9s | Best absolute quality |
| 🥇 | gemini-3-pro-preview low | **1.299** | 98.1% | 10.3s | Same quality, 3× faster |
| 3 | gemini-2.5-flash low | 1.434 | 98.1% | 21.1s | Good quality/speed balance |
| 4 | grok-4-1-fast-reasoning | 1.448 | 97.7% | 20.4s | Best non-Google alternative |
| 5 | gpt-5.4 full low | 1.502 | 98.8% | 17.3s | Best OpenAI quality |
| 6 | gpt-5.4-mini low | 1.526 | 98.1% | **4.7s** | ⭐ Best quality/speed (OpenAI) |
| 7 | o3 high | 1.530 | 98.8% | 15.9s | Obsolete — beaten in quality |
| 8 | gpt-4o low | 1.545 | 96.1% | 10.3s | Current production — superable |
| ⚠️ | claude-opus-4-7 | 1.668* | 80.1% | 17.1s | Low coverage — prompt not optimized |

> `*` avg_pos over matched cases only. 51/256 unmatched — see Paso 3.6 in ROADMAP.

#### Track B — HPO Datasets (DeepRare paper comparison)

| Dataset | Casos | gpt-4o R@1 | gpt-5.4-mini R@1 | gemini-2.5-pro R@1 | Ganador |
|---------|-------|-----------|-----------------|---------------------|---------|
| RAMEDIS | 624 | 49.2% | 46.3% | **54.2%** 🏆 | gemini +5pp |
| LIRICAL | 370 | 37.0% | 55.1% | **61.9%** 🏆 | gemini +7pp vs mini |
| HMS | 88 | 34.1% | 53.4% | **56.8%** 🏆 | gemini +3pp vs mini |
| MyGene2 | 146 | 23.3% | 38.4% | **55.5%** 🏆 | gemini +17pp vs mini |
| MME | 40 | 42.5% | 22.5% | **65.0%** 🏆 | gemini +22pp vs gpt-4o |
| **DDD** | **1.749** | **44.9%** | **52.4%** | **63.5%** 🏆 | gemini +18.6pp vs gpt-4o |

> gemini-2.5-pro wins in all 5 completed HPO datasets. gpt-5.4-mini beats gpt-4o in 4/5.

---

### Model Timing Reference

#### Emulation time (DDX generation only, excluding evaluation)

| Model | s/case | 256 cases | 1749 cases | Source |
|-------|--------|-----------|------------|--------|
| **gpt-5.4-mini low** | **~5s** | **~21 min** | **~2.5h** | DDD run |
| gpt-4o low | ~8-10s | ~40 min | ~3.7h | DDD + all_256 runs |
| gemini-3-pro-preview low | ~10s | ~44 min | ~4.9h | all_256 run |
| gpt-5.4 full low | ~17s | ~74 min | ~8.2h | all_256 run |
| o3 high | ~16s | ~68 min | ~7.7h | all_256 run |
| grok-4-1-fast-reasoning | ~20s | ~87 min | ~9.7h | all_256 run |
| gemini-2.5-flash low | ~21s | ~90 min | ~10.5h | all_256 run |
| gemini-2.5-pro low | ~28-34s | ~120 min | ~13-17h | all_256 + DDD runs |
| gpt-5-mini low | ~48s | ~205 min | ~23h | all_256 run |

> Evaluation phase (judge) adds ~1-3h per 256 cases regardless of the evaluated model.

#### Cost reference (Azure/API pricing, approximate 2026-04)

| Model | Input $/1M | Output $/1M | Relative cost/case | Real cost (256c) |
|-------|-----------|------------|-------------------|------------------|
| gpt-5.4-mini | ~$0.15 | ~$0.60 | ~1× (cheapest) | — |
| gemini-2.5-flash | ~$0.10 | ~$0.40 | ~0.7× | — |
| gemini-2.5-pro | ~$1.25 | ~$10.00 | ~12× | — |
| gpt-4o | ~$2.50 | ~$10.00 | ~15× | — |
| gpt-5.4 full | ~$3.75 | ~$15.00 | ~22× | — |
| **claude-opus-4-7** | — | — | — | **~$8 / 256 casos** (medido) |
| o3 | ~$10.00 | ~$40.00 | ~60× | — |

> `claude-opus-4-7`: coste real medido en run de all_256_clean = **$8 USD** (256 casos, max_tokens=12000). Referencia útil para estimar coste de Sonnet (~3-4×) y Haiku (~10-15×) más baratos.

---

### Production Recommendations

Based on the 2026-04 evaluation:

**Normal mode (replace gpt-4o):**
→ **`gpt-5.4-mini low`** — better avg_pos (1.526 vs 1.545), 2× faster, ~15× cheaper, better R@1 on HPO datasets

**Advanced mode (replace o3):**
→ **`gemini-3-pro-preview low`** — same quality as gemini-2.5-pro (1.299), 3× faster, better quality than gpt-5.4 full
→ **`gemini-2.5-pro low`** as alternative if gemini-3-pro-preview is unavailable

**o3 is obsolete:** beaten in quality by 6 models, no speed advantage.

---

## Components

### Core Files

- **`main.py`** - Pipeline orchestrator with state management and interactive decision points
- **`emulator.py`** - DDX generation using various LLM models (GPT-4O, O3, O1, Claude)
- **`medlabeler.py`** - Medical code attribution using Azure Text Analytics for standardized coding
- **`evaluator.py`** - Comprehensive DDX quality evaluation against GDX using dual methodology
- **`config.yaml`** - Configuration file with all parameters and model specifications

### Utility Files

- **`validate.py`** - Configuration and component validation
- **`watch.py`** - Real-time monitoring and progress tracking
- **`README.md`** - This comprehensive documentation

## Methodological Innovation

Pipeline V4 represents significant methodological advances over previous iterations:

### PV0 → PV4 Evolution
- **PV0**: Basic LLM-to-LLM evaluation with inherent bias
- **PV2**: Introduction of BERT semantic matching for objective assessment
- **PV3**: Dual evaluation methodology combining BERT + LLM judgment
- **PV4**: Refined architecture with bias detection and statistical validation

### Evaluation Methodology
The pipeline employs a sophisticated dual-track evaluation:

1. **BERT Semantic Matching**: Objective similarity assessment with configurable thresholds (0.80 acceptance, 0.90 auto-confirm)
2. **LLM Judgment**: Contextual evaluation for cases where semantic matching is insufficient
3. **Statistical Validation**: Comprehensive metrics including position-based ranking, confidence intervals, and effect size calculations

![Pipeline Evolution](../../__conceptual-model-and-research-notes/imgs/pv12vspv3.jpg)

## Configuration

The `config.yaml` file contains all configuration parameters:

```yaml
# General Information
EXPERIMENT_NAME: "no-name-provided"
EXPERIMENT_DESCRIPTION: "no-description-provided"

# Dataset Configuration
DATASET_PATH: "bench/datasets/all_450.json"

# DXGPT Emulator Configuration
DXGPT_EMULATOR:
  MODEL: "gpt-4o-summary"
  CANDIDATE_PROMPT_PATH: "bench/candidate-prompts/dxgpt_dev.txt"
  PARAMS:
    temperature: 0.1
    max_tokens: 4000
  OUTPUT_SCHEMA: true
  OUTPUT_SCHEMA_PATH: "bench/candidate-prompts/candidate_output_schema.json"

# Evaluator Configuration
EVALUATOR:
  BERT_ACCEPTANCE_THRESHOLD: 0.80
  BERT_AUTOCONFIRM_THRESHOLD: 0.90
  ENABLE_ICD10_PARENT_SEARCH: true
  ENABLE_ICD10_SIBLING_SEARCH: true

# Main Pipeline Control
MAIN:
  SHOULD_EMULATE: true
  SHOULD_LABEL: true
  SHOULD_EVALUATE: true
```

## Prerequisites

### Python Dependencies

The pipeline requires the following Python packages:
- `yaml`
- `json`
- `os`
- `sys`
- `datetime`
- `typing`
- `azure-ai-textanalytics`
- `python-dotenv`

### Environment Variables

Create a `.env` file in the **project root** (`C:\repo\DxGPT\eval\.env`) with all required variables.

You can copy the template:
```bash
cp .env.example .env
```

Then edit `.env` and fill in your actual credentials:

```env
# Azure Text Analytics (para medical code attribution - medlabeler.py)
AZURE_LANGUAGE_ENDPOINT=your_azure_language_endpoint_here
AZURE_LANGUAGE_KEY=your_azure_language_key_here

# Azure OpenAI (para LLM models - emulator.py, evaluator.py)
AZURE_OPENAI_ENDPOINT=your_azure_openai_endpoint_here
AZURE_OPENAI_API_KEY=your_azure_openai_api_key_here
AZURE_OPENAI_API_VERSION=2024-02-15-preview

# Hugging Face (para BERT similarity y modelos Hugging Face)
HF_TOKEN=your_huggingface_token_here
SAPBERT_ENDPOINT_URL=your_sapbert_endpoint_url_here
```

**IMPORTANTE**: El archivo `.env` debe estar en la **raíz del proyecto** (`C:\repo\DxGPT\eval\.env`), no en el directorio del pipeline.

### Utils Dependencies

The pipeline uses utilities from the `utils/` directory:
- `utils.llm` - LLM model interface
- `utils.bert.bert_similarity` - BERT similarity calculations
- `utils.icd10.taxonomy` - ICD-10 taxonomy operations

## Usage

### 1. Validation

First, validate the configuration and dependencies:

```bash
python3 validate.py
```

### 2. Full Pipeline

Run the complete pipeline:

```bash
python3 main.py
```

### 3. Individual Components

Run individual components separately:

```bash
# DDX Generation only
python3 emulator.py

# Medical Code Attribution only
python3 medlabeler.py

# Evaluation only
python3 evaluator.py
```

## Output Structure

The pipeline creates outputs in the following structure:

```
output/
├── <dataset_name>/
│   └── <prompt_name>/
│       └── <model_name>/
│           ├── <prompt_name>___<model_name>___ddxs_from_emulator.json (temporary)
│           ├── <prompt_name>___<model_name>___ddxs_from_labeler.json
│           ├── <prompt_name>___<model_name>___config.yaml
│           └── <timestamp>/
│               ├── <prompt_name>___<model_name>___evaluation.log
│               ├── <prompt_name>___<model_name>___evaluation_details.txt
│               ├── <prompt_name>___<model_name>___summary.json
│               └── <prompt_name>___<model_name>___config.yaml
```

For example, with dataset `all_5.json`, prompt `dxgpt_dev`, and model `gpt-4o-summary`:
```
output/
├── all_5/
│   └── dxgpt_dev/
│       └── gpt_4o_summary/
│           ├── dxgpt_dev___gpt_4o_summary___ddxs_from_emulator.json (temporary)
│           ├── dxgpt_dev___gpt_4o_summary___ddxs_from_labeler.json
│           ├── dxgpt_dev___gpt_4o_summary___config.yaml
│           └── 20250117123456/
│               ├── dxgpt_dev___gpt_4o_summary___evaluation.log
│               ├── dxgpt_dev___gpt_4o_summary___evaluation_details.txt
│               ├── dxgpt_dev___gpt_4o_summary___summary.json
│               └── dxgpt_dev___gpt_4o_summary___config.yaml
```

### File Naming Convention

- `-` characters are replaced with `_`
- Spaces and special characters are replaced with `_`
- Multiple consecutive `_` are collapsed to single `_`

## Pipeline States

The pipeline supports state management and resumption:

1. **Fresh Run**: All steps executed from beginning
2. **Resume from Labeling**: Skip DDX generation if results exist
3. **Resume from Evaluation**: Skip DDX generation and labeling if results exist
4. **Abort**: Users can abort the operation at any decision point

## User Interaction

The pipeline includes interactive prompts for decision-making:

- **Overwrite decisions**: When outputs already exist, users can choose to overwrite or continue
- **Abort option**: Every user prompt includes an abort option (❌ Abort operation)
- **Keyboard interrupt**: Users can press Ctrl+C to abort at any time
- **Clear options**: All choices are numbered and clearly presented

Example user prompt:
```
⚠️  DDX results already exist at output/all_5/dxgpt_dev/gpt_4o_summary/file.json

1. Re-run DDX generation (will overwrite existing results)
2. Continue with medical code labeling using existing DDX
3. ❌ Abort operation

Enter your choice (number): 
```

## Error Handling

The pipeline includes comprehensive error handling:

- Configuration validation
- File existence checks
- API error handling
- State consistency validation
- User interaction for conflict resolution

## Features

### State Management
- Automatic detection of existing outputs
- User prompts for overwrite decisions
- Resumption from any pipeline stage
- **Abort functionality**: Users can always choose to abort the operation

### File Organization
- Structured output directories
- Timestamped evaluation runs
- Configuration snapshots for reproducibility

### Validation
- Pre-execution validation of all components
- Configuration file validation
- Dataset format validation
- Prompt template validation

### Monitoring
- Progress tracking with terminal output
- Detailed logging for debugging
- Success/failure indicators

## Troubleshooting

### Common Issues

1. **Module not found errors**: Ensure the `utils/` directory is in the Python path
2. **Azure API errors**: Check your `.env` file and API credentials
3. **File path errors**: Verify the relative paths in `config.yaml`
4. **Memory errors**: Reduce batch sizes or dataset size for testing

### Debugging

1. Run `python3 validate.py` to check configuration
2. Check the evaluation log files for detailed error messages
3. Verify that all required files exist in the expected locations
4. Ensure Azure Text Analytics credentials are valid

## Contributing

When modifying the pipeline:

1. Update the configuration validation in `validate.py`
2. Update this README with any new features or requirements
3. Test all pipeline states (fresh, resume, etc.)
4. Ensure error handling is comprehensive