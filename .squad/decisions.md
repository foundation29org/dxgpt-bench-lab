# Squad Decisions

## Active Decisions (2026-04-14)

### 1. Ripley Decision — DxGPT Evaluation Audit Rubric

**Date:** 2026-04-14  
**Status:** PROPOSED — requires team review

**Audit Verdict:**

| Dimension | Verdict | Summary |
|-----------|---------|---------|
| Dataset integrity | 🔴 RED | Boilerplate prefix, mixed formats, missing demographics in 22% of cases |
| Language/translation validity | 🟡 AMBER | Spanish-frame cases translated at runtime create systematic input-quality gap |
| Metric validity | 🟡 AMBER | Evaluation cascade conflates code-match and semantic-match; ICD-10 sibling matching generous; judge model varies |
| Reproducibility | 🔴 RED | Same config appears multiple times with wildly different results; no deduplication or version pinning |
| Public-claims alignment | 🔴 RED | Published "1.326 – 92.7%" untraceable; prompt name mislabeled in reports |

**Critical Findings:**

1. **Dataset Integrity (RED):** 33–40% boilerplate prefix contamination; 38% of diagnoses in all_275 lack SNOMED codes; composition varies across splits.
2. **Language/Translation (AMBER):** Spanish cases translated at runtime; English cases unchanged; no validation of translation quality.
3. **Metric Validity (AMBER):** ICD-10 sibling matching generous; BERT ≥ 0.90 auto-confirms without review; judge model varies.
4. **Reproducibility (RED):** Same configs appear multiple times with 56.0%, 92.7%, 96.0% results; no metadata in ranking entries.
5. **Public Claims (RED):** "1.326 – 92.7%" untraceable; 92.7% from `juanjo_classic` (not `_v2`) with avg position 1.443 (not 1.326).

**Priority Actions:** Strip boilerplate, remove diagnosis leakage, correct/retract untraceable claims, fix ranking metadata, stratify by source, validate BERT thresholds.

---

### 2. Bishop Decision — Dataset Integrity Issues

**Date:** 2026-04-14  
**Scope:** 9 datasets, 1,254 cases  
**Status:** CRITICAL — Tier 1 cleanup required before final evaluation

**Five Failure Modes (by severity):**

1. **Label Leakage (CRITICAL):** 26% of cases (323/1,254) have diagnosis terms in clinical history. Model doesn't diagnose—it pattern-matches. Benchmark meaningless.
2. **Boilerplate Prefix (HIGH):** 57% (701 cases) start with synthetic "Motivo de consulta" prefix. Pipeline artifact, not clinical data. Inflates scores.
3. **Template Markers (MEDIUM):** ~69% have section headers (Anamnesis, Antecedentes, etc.). Model uses shortcuts instead of reasoning.
4. **Language Mixing (MEDIUM):** ~68 cases mix Spanish/English. Translation evaluation unreliable.
5. **Dash-List Symptoms (LOW):** 55–100% in small datasets. Easier parsing; doesn't reflect clinical practice.

**Cleanup Plan:**
- **Tier 1:** Remove diagnosis terms (323), strip boilerplate (701)
- **Tier 2:** Separate mixed-language, document templates
- **Tier 3:** Convert dash-lists to prose

**Recommendation:** Block final evaluation until Tier 1 complete. Not trustworthy for decision-making.

---

### 3. Dallas Decision — Evaluation Strategy Assessment

**Date:** 2026-04-14  
**Status:** PROPOSED — methodology review required

**Verdict:** Current strategy unsuitable for public reporting as-is. Acceptable only for internal regression tracking.

**Six Issues:**
1. Misaligned ranking logic (average_position prioritized over success rate)
2. Unfixed K (different models emit different # of DDX)
3. Judge choice materially affects outcomes (Gemini: 94/matches from LLM_JUDGMENT)
4. Version drift (ranking.txt + rankingV2 mix different judges/datasets)
5. Hidden translation assumptions (DDX sent as English; model_version=latest)
6. Dataset integrity blocks benchmark interpretation

**Minimum Controls:**
1. Fix benchmark spec (hashes, judge, commit, service versions)
2. Fix K explicitly in schema
3. Full-denominator primary metric (top-1/3/5, not matched-only average position)
4. Single-gold/multi-gold reported separately
5. Freeze judge; manually audit semantic-only accepts
6. Pin external scorer versions

**Bottom Line:** Frozen rerun required with fixed K, fixed judge, fixed translation, full-denominator metric.

---

### 4. Lambert Decision — Clinical Validity and Risks

**Date:** 2026-04-14  
**Status:** PROPOSED — clinical review required

**Verdict:** Datasets contain clinically dangerous issues. Filtering required before model-ranking claims trusted.

**Critical Issues:**
1. Spanish boilerplate + English phenotype lists (non-diagnostic format)
2. Figure-dependent and exam-style stems (not pure diagnosis)
3. Multi-label synonyms and non-diagnostic labels (polluted gold)
4. Chart metadata (leaks meaning or creates shortcuts)

**Guardrails:**
1. Exclude cases depending on unseen figures or explicitly stating diagnosis
2. Collapse diagnosis synonyms; remove history/treatment/biomarker items
3. Detect language at field level; preserve medical entities; skip blind translation
4. Stratify by source family (R*, B*, Q*, T*, U*) in evaluation

---

### 5. Parker Decision — QA Validation Checklist and Script

**Date:** 2026-04-14  
**Status:** IMPLEMENTED — ready for immediate use

**Deliverables:**
- Eight-gate pass/fail checklist
- `validation_checks.py` script
- `QA_VALIDATION_README.md` docs

**Gates:** Label Leakage (CRITICAL ≤5%), Boilerplate (HIGH <10%), Template Markers (MEDIUM <20%), Language Mixing (MEDIUM <5%), List-Format (LOW ≤30%), Version Drift (CRITICAL), Judge/Model Mismatch (CRITICAL), Success Metric Sanity (CRITICAL).

**Test Results (all_275.json):**
- Label Leakage: 19/275 FAIL (7% > 5%)
- Boilerplate Prefix: 57/275 FAIL (21% > 10%)
- Template Markers: 87/275 (32%, in warn range)
- List-Format: 0/275 PASS

**Finding:** all_275 **fails Tier 1 gates**. Requires cleanup.

---

### 6. Parker Decision — Validation Output Fix

**Date:** 2026-04-14  
**Status:** COMPLETED

**Bug:** Count line printed `Count: 19/19` instead of `Count: 19/275`  
**Fix:** Modified run_all_checks() to return (results, dataset_size); updated print_results() signature  
**Impact:** Surgical change (3 functions); output now accurate

---

### 7. Bishop Decision — Nature Paper Dataset Catalog

**Date:** 2026-04-16  
**Status:** COMPLETED  
**Scope:** 9 datasets, 6,401 cases, 2,919 rare diseases  
**Author:** Bishop (Data Analyst)

**Deliverable:** Complete metadata catalog for Nature paper (DeepRare, s41586-025-10097-9) datasets with access paths and integration blockers.

**Public Datasets (7, ~4,526 cases):**
1. **RareBench-MME** (40 cases) — Matchmaker Exchange; literature-derived; easy
2. **RareBench-LIRICAL** (370) — HPO + genomic variants; literature; easy-moderate
3. **DDD** (2,283) — DECIPHER database; developmental disorders; easy-moderate; **LARGEST PUBLIC**
4. **RAMEDIS** (624) — Rare metabolic disorders; curated case reports; moderate
5. **MyGene2** (146) — Crowdsourced patient cases; HPO + narratives; **HIGHEST DEEPRARE PERFORMANCE** (74% Recall@1)
6. **RareBench-HMS** (88) — Hannover Medical School outpatient; free-text; hard
7. **MIMIC-IV-Rare** (1,875) — PhysioNet ICU notes; de-identified; hard; **2ND LARGEST PUBLIC**

**Private/In-House Datasets (2, 1,137 cases):**
8. **Xinhua Hospital** (975) — Shanghai Jiao Tong; pediatric; privacy-protected; no external access
9. **Hunan Hospital** (162) — Xiangya; pediatric; privacy-protected; no external access

**Critical Distinction:** Nature's datasets are **curated rare-disease registries** (disease-centric, clean), NOT hospital EHR pipelines (boilerplate-prone). Different preprocessing discipline may avoid DxGPT's label leakage and boilerplate contamination issues.

**Recommended Integration Tier 1 (HIGH-IMPACT PUBLIC):**
- MIMIC-IV-Rare (1,875): Real unstructured notes; tests current pipeline directly
- DDD (2,283): Largest; well-documented; genetically validated
- MyGene2 (146): Crowdsourced; highest performance; readily available

**QA Concern:** Audit public datasets against Parker QA checklist (boilerplate, leakage, template markers, language mixing) before adoption. Assume "clean" reputation doesn't guarantee freedom from DxGPT-analogous issues.

**Reference:** Chen et al., 2025. "DeepRare: an agentic LLM-based system for rare disease diagnosis." *Nature*. s41586-025-10097-9.

---

### 8. Dallas Decision — Nature Datasets Fit Assessment

**Date:** 2026-04-16  
**Status:** COMPLETED  
**Author:** Dallas (Evaluation Engineer)  
**Related:** Bishop Decision #7

**Executive Summary:**
Of 9 Nature datasets, 3 are directly mappable to DxGPT (MyGene2, RAMEDIS, DDD phenotype-only), 3 are partially feasible (MIMIC-IV-Rare, LIRICAL, HMS), and 3 are not feasible (MME too small; Xinhua/Hunan private). **Primary blocker:** DxGPT current datasets fail Tier 1 QA gates; must clean before Nature ingestion to avoid cross-contamination.

**Fit Assessment Matrix:**

| Dataset | Cases | Direct? | Effort | DxGPT Value | Recommendation |
|---------|-------|---------|--------|-------------|---|
| MyGene2 | 146 | ✅ YES | LOW | HIGH | **PURSUE** |
| RAMEDIS | 624 | ✅ YES | MEDIUM | MEDIUM–HIGH | **PURSUE** |
| DDD (phenotype) | 2,283 | 🟡 PARTIAL | MEDIUM–HIGH | VERY HIGH | **CONSIDER** |
| RareBench-HMS | 88 | 🟡 PARTIAL | MEDIUM | LOW–MEDIUM | Low priority |
| MIMIC-IV-Rare (subset) | ~400–600 | 🟡 PARTIAL | MEDIUM–HIGH | LOW (domain mismatch) | Low priority |
| RareBench-LIRICAL | 370 | 🟡 PARTIAL | HIGH (genomic) | MEDIUM | Defer |
| RareBench-MME | 40 | 🔴 NO | VERY HIGH | VERY LOW | Skip |
| Xinhua Hospital | 975 | 🔴 NO | N/A | N/A | **BLOCKED** |
| Hunan Hospital | 162 | 🔴 NO | N/A | N/A | **BLOCKED** |

**Critical Differences (Nature vs. DxGPT):**
- **Metric:** Nature = full-denominator Recall@K; DxGPT = matched-only average position (can hide recall failures)
- **Input:** Nature = structured HPO; DxGPT = free-text narrative
- **Label quality:** Nature = genetic + clinical validation (rigorous); DxGPT = mixed sources with boilerplate/leakage
- **Judge:** Nature = 8 independent physicians, 88% concordance; DxGPT = single model, 0.90 BERT threshold
- **QA status:** Nature = pass; DxGPT = fail (Tier 1)

**Phased Integration Roadmap:**

**Phase 1 (2–3 weeks) — IMMEDIATE:**
- Fetch MyGene2 (~146 cases) + RAMEDIS (~624 cases)
- Standardize to DxGPT JSON schema
- Merge into dataset (275 + 770 = ~1,000 cases)
- Run pipeline_v4; report Recall@1/3/5 per-dataset (full-denominator, not matched-only)
- Run Parker QA validation on merged set

**Phase 2 (4–6 weeks) — IF Phase 1 STABLE:**
- Assess DDD phenotype availability (~2,283 cases)
- Validate clinical expert agreement on sample (like Nature's 8-physician validation)
- Expand to ~3,500 cases total
- Stratify results by specialty/rarity

**Phase 3 (DEFER):**
- Genomic integration (LIRICAL, DDD+VCF) — requires Exomiser-like pipeline module
- Do NOT attempt Xinhua/Hunan (respect privacy boundaries)

**Prerequisites for Phase 1:**
1. Fix boilerplate contamination (strip 57% prefix from current dataset)
2. Remove diagnosis leakage (flag/remove 26% of cases with diagnosis in history)
3. Retrain judge on cleaned data
4. **Then** ingest Nature datasets

**Risks & Mitigations:**
- **Metadata loss:** HPO→free-text conversion may lose precision → Test on 50-case pilot
- **Domain mismatch:** Nature focuses on rare genetic; DxGPT includes broader pediatrics → Stratify by prevalence in results
- **Judge drift:** Different validation methods → Implement physician validation on DxGPT pre/post integration
- **Contaminated labels:** Current DxGPT leakage may skew metrics when merged → Keep datasets separate in reporting; clean DxGPT first
- **Language barriers:** Most Nature datasets are English; DxGPT is Spanish+English mix → Separate English-only evaluation; report language stratification

**Next Steps:**
1. Confirm Phase 1 approach with Javier
2. Retrieve MyGene2 API schema + RAMEDIS source repository
3. Document conversion rules (HPO → free-text, labels → diagnosis fields)
4. Pilot on 50-case subset; validate against pipeline_v4
5. Run Parker QA checks before reporting

---

### 9. Bishop Decision — Data Ingestion and Curation Strategy

**Date:** 2026-04-16  
**Status:** RECOMMENDED  
**Scope:** Data layer architecture; provenance preservation; contamination prevention  
**Author:** Bishop (Data Analyst)

**Recommendation:** Adopt a **three-tier data architecture** that separates raw source datasets, normalized intermediates, and evaluation-ready subdatasets. This avoids label contamination, preserves provenance, and enables safe mixing of heterogeneous sources (DxGPT internal + Nature paper external).

**Current state:** Datasets flow directly from raw sources → processed → bench/datasets (mixed subsets) without explicit provenance tracking. After evaluation, no way to decompose metrics by source family.

**Three-Tier Model:**

1. **Tier 1 — Raw Source Repository** (`data29/data-repos/raw/`)
   - Immutable archive with `SOURCE_MANIFEST.json` documenting provenance
   - Each source: origin URL, license, clinical collection dates, schema version, hash
   - Enforce readonly after ingestion

2. **Tier 2 — Normalized Intermediates** (`data29/data-repos/normalized-by-source/`)
   - Per-source processing: schema normalization, ICD-10 mapping
   - QA validation before merging: run Parker checklist on each source
   - Generate `qa_report_*.txt` per source (boilerplate%, leakage%, language mixing%)
   - Example: ramedis → ramedis_v1.json + qa_report_ramedis_v1.txt + provenance.json

3. **Tier 3 — Curated Evaluation Subdatasets** (`data29/data-repos/curated-datasets/`)
   - Mixed subdatasets with lineage tracking: `_metadata.json` + `_lineage.txt`
   - Composition documented: cases per source, diversity strategy, curation date
   - Enable decomposition of results by source family (stratified reporting)
   - Example: dx_baseline_450.json → dx_baseline_450/_metadata.json (composition) + dx_baseline_450/_lineage.txt (case tracking)

**Critical Insight:**

Both per-source evaluation AND mixed subdatasets are necessary—they serve different purposes:
- Per-source audit catches contamination BEFORE merging
- Mixed subdatasets test generalization AFTER sources are individually validated
- This prevents cross-contamination: clean + clean → trustworthy mixed results

**For Nature Paper Datasets (Phase 1 roadmap):**

1. Ingest: Fetch MyGene2 + RAMEDIS from public sources
2. Normalize to unified schema → `normalized-by-source/`
3. Run Parker QA on both (expected: PASS)
4. Create curated dataset: `dx_nature_intake_770.json` with full lineage
5. Evaluate per-source, then optionally mix

**Implementation Checklist:**

- [ ] Add SOURCE_MANIFEST.json to data29/data-repos/raw/
- [ ] Create normalized-by-source/ structure
- [ ] Normalize each source to unified schema; document schema version
- [ ] Run Parker QA on each source; generate qa_report_*.txt
- [ ] Create provenance.json linking raw → normalized
- [ ] Create curated-datasets/ with _metadata.json + _lineage.txt templates
- [ ] Define diversity_config.yaml (sampling rules)
- [ ] Update documentation with three-tier diagram

**Related Decisions:**

- **Dallas Decision #9 (new):** Recommends dual-mode evaluation (per-source primary, mixed secondary)
- **Parker Decision #5:** QA validation checklist (8 gates) ready to audit new sources

---

### 10. Dallas Decision — Evaluation Strategy for Nature Paper Integration

**Date:** 2026-04-16  
**Status:** ACTIVE — Implementation-ready  
**Author:** Dallas (Evaluation Engineer)  
**Related:** Bishop Decision #9 (Data Ingestion Strategy)

**The Question:** Should we evaluate against each dataset individually, mixed subdatasets, or both?

**Recommendation: Dual-mode evaluation strategy**

1. **Per-source evaluation (PRIMARY, Tier 1):** Report Recall@1/3/5 separately for each dataset family (MyGene2, RAMEDIS, DDD, etc.). This respects provenance, enables comparison to Nature's published baseline, and prevents weaker domains from masking stronger ones.

2. **Mixed subdatasets (SECONDARY, Tier 2):** Create stratified subsets mixing source families only *after* per-source validation passes QA. This tests domain generalization but must not become the primary metric.

**Why Per-Source Evaluation Is Necessary:**

- Nature paper reports per-dataset; you must match their metric to claim comparability
- Per-source evaluation respects data provenance and catches quality issues before mixing
- Allows detection of domain-specific failures
- Baseline for root-cause analysis (is the gap due to judge, prompt, or data version?)

**Why Mixed Subdatasets Still Matter:**

- Current DxGPT builds diversity-optimized subsets for regression testing (good)
- Mixing prevents overfitting to single-source symptom patterns
- But only valid if underlying per-source datasets are clean (hence Tier 1 prerequisite)

**Critical Blocker: DxGPT Cleanup Required First**

Before ingesting Nature data:
1. Clean DxGPT internal: strip boilerplate (57% of cases), remove diagnosis leakage (26% of cases)
2. Retrain judge on cleaned data
3. Re-run Parker QA gates → all PASS
4. **Then** ingest Nature datasets

Reason: Merging dirty + clean = cross-contamination; both signals become untrustworthy. Separate concerns.

**Metric Alignment with Nature:**

- Nature: Full-denominator Recall@K (e.g., "57% Recall@1 across all 6,401 cases")
- Current DxGPT: Matched-only average position (only cases with ≥1 match)
- **Required change:** Adopt Nature's metric to enable direct comparison

Why full-denominator matters: Matched-only average position can hide 30% recall failures while appearing better on matched cases.

**Evaluation Architecture:**

| Tier | Scope | Dataset Examples | Primary Metric | Notes |
|------|-------|------------------|----------------|-------|
| **1** | Per-source | MyGene2 (146), RAMEDIS (624), DDD (2,283) | Recall@1/3/5 (full-denom) | REQUIRED; baseline for Nature comparison |
| **2** | Mixed | MyGene2 + RAMEDIS (770) | Recall@1/3/5 (full-denom) + per-source breakdown | OPTIONAL; only if Tier 1 passes QA |
| **3** | Extended | Genomic integration (DDD+VCF, LIRICAL) | [TBD] | FUTURE; defer until Tier 1–2 stable |

**Stratification Requirements:**

Report results stratified by:
- **Disease prevalence:** Rare genetic vs. mixed/broader pediatric
- **Case complexity:** High (C5+), Medium (C3-C4), Low (C1-C2)
- **Input modality:** Free-text narrative, HPO-structured
- **Language:** English-only, Mixed language

**Reporting Template:**

```
## Evaluation Results

### Per-Dataset Baselines (Tier 1 — Primary)
| Dataset | Cases | Recall@1 | Recall@3 | Recall@5 | Avg Position | Parker QA |
|---------|-------|----------|----------|----------|-------------|-----------|
| MyGene2 | 146 | X% | X% | X% | X | PASS |
| RAMEDIS | 624 | X% | X% | X% | X | PASS |

**Nature Paper Baseline (for reference):**
| Dataset | Recall@1 | 
|---------|----------|
| MyGene2 | 74% |

### Stratified Results
- **Rare genetic (MyGene2, RAMEDIS):** Recall@1 = X%
- **Mixed/broader:** Recall@1 = Y%

### Mixed Subdataset Results (Tier 2, optional)
MyGene2 + RAMEDIS (770 cases): Recall@1 = X% (breakdown: MyGene2 = X%, RAMEDIS = X%)
```

**Red Flags to Watch:**

| Risk | Signal | Mitigation |
|------|--------|-----------|
| **Leakage during ingestion** | Recall on mixed > Nature's baseline for same dataset | Stop; audit labels; re-run Parker QA |
| **Prompt overfitting** | MyGene2 Recall@1 differs by >15% from Nature's published | Check for dataset-specific keywords in prompt |
| **Judge drift** | Semantic matching score varies >5% between runs | Freeze service versions; validate on sample |
| **Contamination** | Mixed results rank higher than per-source | Keep separate in reporting; clean DxGPT first |

**Phased Integration Roadmap:**

**Phase 1 (2–3 weeks, IMMEDIATE):**
1. Fetch MyGene2 + RAMEDIS from public sources
2. Convert to DxGPT JSON schema (HPO→narrative, labels→diagnosis field)
3. Run pipeline_v4; report Recall@1/3/5 per-dataset (full-denominator)
4. Run Parker QA validation; document status

**Phase 2 (4–6 weeks, IF Phase 1 STABLE):**
1. Assess DDD phenotype availability (~2,283 cases)
2. Implement clinical expert validation (8-physician agreement pilot)
3. Expand to ~3,500 cases
4. Stratify results by specialty/rarity

**Phase 3 (DEFER):**
1. Genomic integration (LIRICAL, DDD+VCF) — requires Exomiser module
2. Do NOT attempt Xinhua/Hunan (privacy boundaries)

**Decision Boundary:**

- **If Recall@1 matches Nature's within ±10%:** Evaluation pipeline is correctly wired; safe to mix and stratify
- **If Recall@1 < Nature's by >15%:** Do not mix yet. Investigate: dataset version? judge quality? metric differences? Fix gap before Tier 2

**Next Steps:**

1. ✅ Team alignment: Confirm Tier 1→Tier 2→Tier 3 approach with Javier
2. Clean DxGPT first (prerequisite for all phases)
3. Fetch Nature datasets (MyGene2, RAMEDIS)
4. Pilot on 50-case subset
5. Full Phase 1 evaluation
6. Decide on Tier 2 (optional mixed subdatasets)

---

## Governance

- All meaningful changes require team consensus
- Document architectural decisions here
- Keep history focused on work, decisions focused on direction
- Critical decisions (RED flags) must be addressed before proceeding
