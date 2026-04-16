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

### Roadmap Review (2026-04-14)

- **Roadmap assessment**: Javier's ROADMAP.md correctly prioritizes Phase 1 (dataset cleanup) before Phase 2 (Nature integration). This is the right call — cannot compare against Nature on dirty data.
- **Phase 1 structure is sound**: Label leakage removal (7%), boilerplate stripping (21%), three-level architecture (raw/normalized/curated), re-baseline on clean data.
- **Four critical issues identified**:
  1. **Template markers WARN ambiguity**: Roadmap says "PASS/WARN" acceptable. Should explicitly reject WARN >40% for external publication.
  2. **Expected baseline drop not documented**: Phase 1.4 rebaseline will drop 5–8% (healthy; indicates data quality improvement). Javier needs to expect this before seeing scores.
  3. **Recall@K implementation timing**: Phase 3 plan implements Recall@K *after* Phase 2.5 runs. This means re-running 770 cases. Recommend implementing in evaluator.py *before* Phase 2.5.
  4. **Phase 2.4 pilot too small**: 50 cases insufficient to validate format artifacts. Add success gate: Recall@1 ≥ 30% in pilot → proceed. <30% → stop and investigate.
- **Sequence verdict**: Phase 1 before Phase 2 is unambiguously correct. Do not parallelize. Do not skip.
- **Clinical validation**: Phase 4.3 marked "optional." Should be mandatory for publication. Budget 16 hours (5 cases, 2 physicians, 88% target concordance from Nature paper).
- **Decision memo filed**: `.squad/decisions/inbox/ripley-roadmap-review.md` with 4 explicit gates required before execution.

### Roadmap Review Completion (2026-04-16)

- **Status: DECISION ENDORSED** — Roadmap review merged to `.squad/decisions.md` as Decision #11.
- **Four gates formalized**: (1) template marker threshold (reject WARN >40%), (2) baseline drop documentation (5–8% expected), (3) Recall@K implementation timing (before Phase 2.5), (4) Phase 2.4 pilot gate (Recall@1 ≥ 30%).
- **Clinical validation escalation**: Phase 4.3 promoted from optional to mandatory (16 hours budget, 88% target concordance).
- **Sequence endorsed**: Phase 1 before Phase 2 is unambiguously correct. Execute as written.
- **Next checkpoint**: Paso 1.1 completion + QA report on all_275_clean.json
- **Confidence**: High
