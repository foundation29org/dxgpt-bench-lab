# Squad Team

> DxGPT evaluation audit squad

## Coordinator

| Name | Role | Notes |
|------|------|-------|
| Squad | Coordinator | Routes work, enforces handoffs and reviewer gates. |

## Members

| Name | Role | Charter | Status |
|------|------|---------|--------|
| Ripley | Lead | `.squad/agents/ripley/charter.md` | Active |
| Bishop | Data Analyst | `.squad/agents/bishop/charter.md` | Active |
| Dallas | Evaluation Engineer | `.squad/agents/dallas/charter.md` | Active |
| Lambert | Medical Reviewer | `.squad/agents/lambert/charter.md` | Active |
| Parker | QA / Bench Tester | `.squad/agents/parker/charter.md` | Active |
| Scribe | Session Logger | `.squad/agents/scribe/charter.md` | Active |
| Ralph | Work Monitor | -- | Active |

## Project Context

- **Owner:** Javier Logroño
- **Project:** DxGPT evaluation repository focused on dataset quality, diagnosis benchmarking, and evaluation pipeline reliability
- **Stack:** Python, pandas, scikit-learn, torch, transformers, Azure Text Analytics, Azure Translator, benchmark datasets under `bench\datasets`, pipelines under `bench\pipelines`
- **Created:** 2026-04-14
- **Current focus:** Audit evaluation datasets, detect cleaning risks and language/translation artifacts, and assess whether `pipeline_v4 - fork` is a sound evaluation strategy
