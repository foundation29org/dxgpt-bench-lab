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

## Governance

- All meaningful changes require team consensus
- Document architectural decisions here
- Keep history focused on work, decisions focused on direction
- Critical decisions (RED flags) must be addressed before proceeding
