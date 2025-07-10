# DxGPT Latitude Bench

A systematic evaluation framework for measuring how well AI models perform medical diagnosis tasks. This project compares different AI systems by testing their ability to identify medical conditions and understand their severity.

## What This Project Does

This system presents medical cases to AI models and evaluates their diagnostic responses. It solves a key problem in medical AI evaluation: traditional methods penalized correct but differently-worded diagnoses. Our approach recognizes when diagnoses are medically equivalent even if the exact words differ.

## Core Components

**Evaluation System** (`bench/`)  
Three progressive approaches to testing AI diagnostic capabilities. Started with strict code matching, evolved to include semantic understanding, ensuring fair evaluation of medical expertise.

**Data Processing** (`data29/`)  
Manages nearly 10,000 medical cases from hospitals, medical exams, and rare disease databases. Creates balanced test sets that represent real medical diversity.

**Reusable Tools** (`utils/`)  
Portable modules for semantic analysis, medical classification systems, and AI model integration. These can be extracted for use in other projects.

## Key Innovation

The project discovered that expert medical responses were being unfairly penalized. For example, a specialist's diagnosis of "aneurysmal subarachnoid hemorrhage" would score zero against "subarachnoid hemorrhage" despite being more precise. Our semantic safety net fixes this by recognizing medical equivalence.

## Getting Started

1. Create a Python environment and install dependencies:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -e .
```

2. Configure API access in `.env` file (see `.env.example`)

3. Run an evaluation:
```bash
cd bench/pipelines/pipeline_v2*
python run.py
```

## Results and Insights

Testing revealed clear performance differences between AI models:
- Advanced visual models showed highest capability but variable consistency
- Standard language models provided reliable, stable performance
- Specialized medical models offered domain expertise with limitations

## Further Reading

For deeper understanding:
- [Conceptual model and research findings](bench/__conceptual-model-and-research-notes/)
- [Pipeline methodology details](bench/pipelines/)
- [Data processing documentation](data29/)
- [Reusable utilities](utils/)

## Purpose

This framework helps teams make informed decisions when selecting AI models for medical applications. It provides objective, reproducible metrics while respecting the nuanced nature of medical diagnosis.

---

*A project focused on advancing responsible medical AI evaluation through transparent, clinically-relevant assessment methods.*