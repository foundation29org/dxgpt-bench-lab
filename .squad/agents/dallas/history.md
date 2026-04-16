# Project Context

- **Owner:** Javier Logroño
- **Project:** DxGPT evaluation repository for auditing dataset quality and diagnosis benchmark reliability
- **Stack:** Python, pandas, scikit-learn, torch, transformers, Azure Text Analytics, Azure Translator
- **Created:** 2026-04-14T12:02:03.824Z

## Learnings

- Initial focus: inspect `pipeline_v4 - fork`, trace scoring and translation flow, and judge whether the current evaluation methodology is measuring diagnostic quality correctly.
- Current evaluator marks a case as matched when **any** gold diagnosis matches **any** generated DDX, then computes `average_position` only over matched cases; `watch.py` ranks runs by that matched-only average before success rate, so low-recall runs can outrank higher-recall ones.
- The production-style `juanjo_classic_v2` prompt asks for “N possible diagnoses”, but current configs typically run with `OUTPUT_SCHEMA: false`, so list length is not fixed and differs materially by model/run.
- Semantic rescue is a major share of current scores (e.g. 94/271 matches in the March 2026 `all_275` + `juanjo_classic_v2` + Gemini run), which makes judge choice a first-order benchmark variable rather than a minor implementation detail.
- Reproducibility is still exposed to external service drift: Azure healthcare labeling uses `model_version=\"latest\"`, SapBERT comes from a remote endpoint, and standalone validation loads the most recent saved `___config.yaml` before `config.yaml`.

### Nature Paper Integration Analysis (2026-04-14)

- Examined Nature paper (Chen et al., 2025, DeepRare) evaluation methodology: 6,401 cases across 9 datasets; uses full-denominator Recall@K (not matched-only). Their judge validated independently by 8 physicians at 88% concordance; ours is single-model at 0.90 threshold.
- **Feasibility assessment**: Of 9 Nature datasets, 2 are directly portable (MyGene2 ~146 cases, RareBench-RAMEDIS ~624 cases), 1 is partially feasible (DDD phenotype-only ~2,283), 3 require genomic pipeline (blocked), 2 are private in-house (Xinhua/Hunan, access denied), 1 is too specialized/small (MME, 40 cases).
- **Current bottleneck**: DxGPT datasets fail Tier 1 QA gates (boilerplate 21% > 10% threshold, label leakage 7% > 5% threshold) per Parker Decision; cannot responsibly ingest Nature datasets until cleaned.
- **Architecture difference**: Nature uses structured HPO input → DxGPT uses free-text narrative. HPO→narrative conversion feasible but requires semantic validation on pilot subset.
- **Metric alignment**: Nature reports Recall@1/3/5 on full denominator; DxGPT's matched-only average position can hide recall failures. Integration should use Nature's metric for comparability (see Dallas Decision on full-denominator primary metric).

---

## Phase 3 Analysis: Nature Paper Integration Feasibility (2026-04-16)

**Request:** Assess Nature paper datasets against DxGPT evaluation pipeline capabilities and provide phased integration roadmap.

**Dataset Fit Analysis:**

**Directly Portable (3 datasets, ~770 cases):**
- MyGene2 (146): Crowdsourced patient narratives + HPO; format directly maps to DxGPT JSON; high performance (74% Recall@1)
- RAMEDIS (624): Curated metabolic case reports; structured + free-text; clean labels (no genomic requirement)
- DDD phenotype-only (2,283): Via DECIPHER API; phenotype-only extraction feasible; largest publicly available rare disease cohort

**Partially Feasible (3 datasets, with caveats):**
- MIMIC-IV-Rare (1,875): Real clinical notes; good for testing unstructured text; but ICU-heavy (domain mismatch with pediatric ambulatory focus); label quality not clinically validated
- RareBench-HMS (88): Real outpatient clinic notes; German language (translation overhead); small sample size
- RareBench-LIRICAL (370): Genomic requirement blocks without VCF pipeline; phenotype-only subset unknown availability

**Not Feasible (3 datasets):**
- RareBench-MME (40): Specialized matchmaking format; too small statistically
- Xinhua (975): **PRIVATE**; paper explicitly notes local-only evaluation; cannot access without institutional collaboration
- Hunan (162): **PRIVATE**; pediatric focus, but access blocked; cannot request

**Metric Misalignment (Critical Issue):**
- Nature: Full-denominator Recall@K (e.g., 57.18% Recall@1 across all 6,401 cases) → transparent recall profile
- DxGPT: Matched-only average position (only averaged over cases with ≥1 match) → can hide poor recall
  - Example: 50% recall + perfect position on matched cases may outrank 80% recall + mediocre position in DxGPT's ranking
  - **Consequence:** Cannot directly compare Nature results to DxGPT metrics without fundamental methodology change

**Quality Assurance Status:**
- Nature datasets: Curated registries; expected clean profiles
- DxGPT current: FAIL Tier 1 gates (boilerplate 21% > 10%, leakage 7% > 5%)
- **Critical blocker:** Must clean DxGPT dataset first; otherwise Nature datasets may be contaminated when merged

**Phased Roadmap (RECOMMENDED):**

1. **Phase 1 (2–3 weeks):** 
   - Fetch MyGene2 + RAMEDIS APIs/sources
   - Convert to DxGPT JSON (HPO → narrative; labels → diagnosis field)
   - Merge with current 275 cases → ~1,000 case dataset
   - Run pipeline_v4 evaluation
   - **Report:** Use Recall@1/3/5 on full denominator (adopt Nature metric)
   - **Validate:** Parker QA checklist on merged dataset

2. **Phase 2 (4–6 weeks, contingent on Phase 1 success):**
   - Attempt DDD phenotype-only extraction (~2,283 cases)
   - Implement clinical expert validation (like Nature's 8-physician agreement pilot)
   - Stratify results by specialty/rarity to avoid masking domain gaps
   - Expected outcome: ~3,500 case dataset

3. **Phase 3 (DEFER — after Phases 1–2 stabilize):**
   - Consider genomic integration (LIRICAL, DDD+VCF) if board prioritizes
   - Requires new Exomiser-like variant prioritization module
   - Not critical for Phase 1

**Critical Prerequisite (MUST DO BEFORE PHASE 1):**
1. Fix boilerplate (strip "Motivo de consulta" from 57% of current dataset)
2. Remove diagnosis leakage (flag/remove 26% of cases with diagnosis in history)
3. Retrain judge on cleaned data
4. Re-run QA gates on cleaned baseline
5. **Then** ingest Nature datasets

**Risks & Mitigations:**
| Risk | Severity | Mitigation |
|------|----------|-----------|
| Metadata loss during HPO→narrative | Medium | Test 50-case pilot; compare Recall@1 before/after |
| Domain mismatch (rare genetic vs. broad pediatric) | Medium | Stratify results by disease prevalence; report separately |
| Judge choice materially affects outcomes | High | Implement physician validation on cleaned DxGPT |
| Merged dataset contains cross-contamination (DxGPT leakage + Nature data) | Critical | Keep separate in reporting; clean DxGPT first |
| Language barriers (Nature English/HPO; DxGPT Spanish+English) | Medium | Separate English-only evaluation; report stratification |

**Architecture Implications:**
- **Input modality shift:** Free-text (current) → HPO (Nature) → requires normalization layer
- **Metric shift:** Matched-only avg position → full-denominator Recall@K (fundamental change)
- **Validation shift:** Single model judge → clinical expert validation (training overhead)
- **Scale shift:** 275 → 3,500 cases (13× expansion) may expose new failure modes

**Next Steps (in order):**
1. Confirm Phase 1 approach alignment with Javier
2. Retrieve MyGene2 API documentation + RAMEDIS source repository
3. Document conversion rules (HPO phenotype → clinical narrative; diagnosis synonyms → canonical labels)
4. Implement 50-case pilot with MyGene2 subset
5. Validate pilot against pipeline_v4 + Parker QA
6. If pilot passes → proceed with full Phase 1 (146 + 624 cases)
7. Plan clinical expert validation cohort for Phase 2 (if board approves)

**Status:** COMPLETE — Roadmap ready for team decision. Awaiting Javier approval to proceed with Phase 1.
