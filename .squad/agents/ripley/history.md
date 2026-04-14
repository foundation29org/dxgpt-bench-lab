# Project Context

- **Owner:** Javier Logroño
- **Project:** DxGPT evaluation repository for auditing dataset quality and diagnosis benchmark reliability
- **Stack:** Python, pandas, scikit-learn, torch, transformers, Azure Text Analytics, Azure Translator
- **Created:** 2026-04-14T12:02:03.824Z

## Learnings

- Initial focus: audit evaluation datasets for noise, prefixes, leakage, language artifacts, translation distortion, and weaknesses in `bench\pipelines\pipeline_v4 - fork`.
- **Dataset composition matters**: `all_450` has 7 source prefixes (Q/R/B/T/S/U/J) with fundamentally different formats. R-prefix (22%) are synthetic symptom lists with no demographics. T-prefix (11%) are genuine Spanish narratives. B/Q/S/J are English vignettes. Aggregate scores hide source-specific performance.
- **"Motivo de consulta" prefix**: Present in all R (100) and T (50) prefix cases across `all_450`. It's a synthetic wrapper, not a real chief complaint. Persists after translation. Should be stripped or reported as confounder.
- **R-prefix cases have no demographics**: All 100 R-prefix cases say "sexo desconocido, desconocidos años." These are structurally degraded compared to other sources.
- **Dataset nesting**: `all_150 ⊂ all_250 ⊂ all_450` and `all_275 ⊂ all_450`. But all_150 has 39% R-prefix vs all_275's 21% — different compositions mean different benchmarks.
- **SNOMED coverage gap**: 38% of diagnoses in `all_275` lack SNOMED codes, forcing fallback to ICD-10 or semantic matching. This creates systematic bias in the evaluation cascade.
- **Judge model inconsistency**: `ranking.txt` (2025) used `gpt_4o_summary` as judge; `rankingV2.txt` (2026) uses `gemini-2.5-pro`. Cross-ranking comparisons are invalid without fixing the judge.
- **Duplicate ranking entries**: Same dataset+prompt+model appear multiple times with wildly different results (e.g., 56% vs 92.7% vs 96%). No commit hash or config hash in ranking entries to explain the difference.
- **"1.326 – 92.7%" untraceable**: Transparency doc confirmed 92.7% maps to pos ~1.443, not 1.326. Prompt cited as "classic_v2" but artifact is from "juanjo_classic". Public claims need correction.
- **Evaluation cascade**: SNOMED → ICD-10 (exact/child/parent/sibling) → BERT (auto-confirm ≥ 0.90) → LLM judge. ICD-10 sibling matching may be over-generous. BERT auto-confirm threshold not clinician-validated.
- **Audit rubric written**: 5-dimension rubric (dataset integrity RED, language AMBER, metrics AMBER, reproducibility RED, public claims RED). Filed as decision in `.squad/decisions/inbox/ripley-eval-rubric.md`.
