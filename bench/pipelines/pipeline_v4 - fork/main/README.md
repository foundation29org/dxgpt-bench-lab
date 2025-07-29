# Pipeline V4 - Medical Diagnosis Evaluation System

## Overview

This is the fourth iteration of our medical diagnosis evaluation pipeline, representing the culmination of extensive research and development in pediatric diagnostic AI assessment. The pipeline evolved through multiple iterations (PV0-PV4) to address critical methodological challenges in evaluating LLM-based diagnostic systems.

### Pipeline Evolution and Study Context

This evaluation framework was developed through a comprehensive study involving 9,677 total medical cases curated from multiple specialized datasets including pediatric emergency medicine, rare diseases (RAMEDIS), and clinical vignettes. The final validated dataset of 450 cases represents a carefully stratified sample ensuring:

- **Diagnostic diversity**: 497 unique diagnoses across 22 ICD-10 chapters
- **Complexity representation**: Cases ranging from C2 to C10 complexity levels  
- **Multi-diagnostic scenarios**: 31.8% of cases with multiple concurrent diagnoses
- **Source heterogeneity**: Integration of 7 distinct medical data sources (B, J, Q, R, S, T, U)

The pipeline architecture addresses three critical evaluation phases:
1. **Differential Diagnosis Generation (DDX)** using state-of-the-art LLM models
2. **Medical Code Attribution** using Azure Text Analytics for standardized coding (ICD-10, SNOMED, OMIM, ORPHA)
3. **Quality Evaluation** against gold standard reference diagnoses (GDX) using both BERT semantic matching and LLM-based judgment

### Key Research Findings

Our comprehensive evaluation across multiple model architectures revealed significant performance variations:

- **O3-Images**: Leading performance with 93.65% accuracy in top-3 diagnostic predictions
- **GPT-4O-Summary**: Strong baseline performance at 84.31% accuracy  
- **O3-PRO**: Specialized variant showing 88.8% accuracy but with specific failure patterns
- **O1**: Advanced reasoning model achieving competitive diagnostic accuracy

![Model Performance Comparison](../../__conceptual-model-and-research-notes/imgs/modelos_openai_rojos.jpg)

The study identified critical insights into diagnostic AI evaluation methodology, bias detection, and the importance of position-based ranking metrics in medical diagnostic systems.

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

Create a `.env` file in the project root with:
```
AZURE_LANGUAGE_ENDPOINT=your_azure_endpoint
AZURE_LANGUAGE_KEY=your_azure_key
```

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