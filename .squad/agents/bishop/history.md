# Project Context

- **Owner:** Javier Logroño
- **Project:** DxGPT evaluation repository for auditing dataset quality and diagnosis benchmark reliability
- **Stack:** Python, pandas, scikit-learn, torch, transformers, Azure Text Analytics, Azure Translator
- **Created:** 2026-04-14T12:02:03.824Z

## Learnings

- Initial focus: profile datasets for repeated prefixes like `motivo consulta`, language mix, translation artifacts, duplication, and other evaluation-distorting patterns.

## Phase 1 Analysis (2026-04-14)

**Deep dataset audit completed across 9 evaluation files (1,254 cases).**

### Key Findings
1. **57% of cases (701)** start with identical "Motivo de consulta" boilerplate—systematic prefix bias.
2. **26% of cases (323)** have diagnosis terms appearing in clinical history—critical label leakage.
3. **Template markers** (Anamnesis, Antecedentes, Exploracion) embedded in 55% of cases—processing artifacts.
4. **Spanish-English mixing** in 2-4% of cases—translation evaluation risk.
5. **Dash-separated symptom lists** in 50%+ of cases—unfair parsing advantage.

### Affected Datasets (in severity order)
- **Highest risk:** all_5, all_10, largest_* (100% boilerplate; 60%+ leakage)
- **Medium risk:** all_150, all_250 (60-70% boilerplate; 30-50% leakage)
- **Lowest risk:** all_275, all_450 (33-32% boilerplate; 16-18% leakage)
- **Special case:** ukranian.json (9 records, mostly clean except mixed language)

### Recommendations
**Tier 1 (Critical):**
- Remove diagnosis terms from case text (fix leakage in 323 cases).
- Strip "Motivo de consulta" prefix (701 cases).

**Tier 2 (Important):**
- Separate or flag Spanish-English mixed cases (68 cases).
- Document/strip template markers (Anamnesis, etc.).

**Tier 3 (Polish):**
- Convert dash lists to natural language prose (~300 cases).

### Next Action
Awaiting team consensus (Ripley, Javier) on cleanup priority before implementing fixes.

---

## Phase 2 Analysis: DeepRare Paper Dataset Catalog (2026-04-14)

**Request:** Identify datasets from Nature paper (DeepRare, s41586-025-10097-9) for potential integration into DxGPT evaluation.

### Key Findings
1. **Paper evaluates 9 datasets / 6,401 cases / 2,919 rare diseases** across three difficulty tiers
2. **7 public datasets accessible** via direct download or APIs (MIMIC-IV-Rare, DDD, MyGene2, RareBench-*, HMS)
3. **2 in-house datasets private** — Xinhua (975 cases, 168 with WES) and Hunan (162 cases, all WES) unavailable without institutional collaboration
4. **Critical distinction:** Public datasets are CURATED RARE DISEASE REGISTRIES, not raw clinical notes like DxGPT's current data—may avoid boilerplate/leakage issues entirely
5. **Best candidates for DxGPT swap:** MIMIC-IV-Rare (1,875 real clinical notes; highest realism) and MyGene2 (146 crowdsourced cases; phenotype-rich)

### Dataset Tiers by Difficulty
- **Easy:** RareBench-MME (40), RareBench-LIRICAL (370), DDD (2,283) — literature-derived, well-documented
- **Moderate:** RAMEDIS (624), MyGene2 (146) — curated case reports, varied documentation
- **Hard:** HMS (88), MIMIC-IV-Rare (1,875), Xinhua (975), Hunan (162) — real clinical practice, diverse presentations

### Critical Insight
The Nature paper's public datasets DON'T HAVE the boilerplate/leakage problems plaguing DxGPT. Why? They are DISEASE-CENTRIC REGISTRIES (built for rare disease diagnosis), not HOSPITAL EHR PIPELINES (built for clinical operations). This suggests different preprocessing discipline. **Recommend audit of public datasets against QA checklist before declaring them "clean."**

### Full Analysis
See `.squad/decisions/inbox/bishop-nature-datasets.md` for complete dataset catalog with access paths, metadata, and integration roadmap.

---

## Phase 3 Analysis: Nature Paper Integration Assessment (2026-04-16)

**Request:** Partner with Dallas to assess how Nature paper datasets fit DxGPT evaluation pipeline.

**Key Findings:**
1. **Public dataset audit:** All 7 public datasets accessible; **DDD largest** (2,283 cases) and most feasible for developmental disorder focus
2. **MyGene2 standout:** 146 cases; crowdsourced real patient narratives; 74% Recall@1 (highest in Nature paper)
3. **MIMIC-IV-Rare promising:** 1,875 real clinical notes; tests unstructured free-text like DxGPT; second-largest public
4. **Xinhua/Hunan off-limits:** Private institutional data; explicitly local-only evaluation in paper; respect privacy boundaries
5. **QA assumption risky:** Nature datasets are "clean" registries but must be audited against Parker QA checklist (boilerplate, leakage, templates, language mixing) before adoption—don't assume registry ≈ clean

### Dataset Tier Recommendations
- **Tier 1 (integrate immediately):** MyGene2 (146), RAMEDIS (624)
- **Tier 2 (exploratory):** DDD phenotype (2,283), MIMIC-IV-Rare (1,875, subset), HMS (88)
- **Tier 3 (defer):** Genomic (LIRICAL, DDD+VCF), specialized (MME)
- **Tier 4 (blocked):** Xinhua, Hunan (privacy)

### Insight for DxGPT
Nature's datasets avoid boilerplate/leakage through **disease-centric registry discipline**, not cleanup. Hospital pipelines (like DxGPT's source) are built for operations, not diagnosis benchmarking. **Lesson:** If DxGPT datasets are from hospital EHRs, boilerplate/leakage are structural, not just data quality issues. Fix Tier 1 QA gates before adopting Nature datasets.

### Full Analysis
See `.squad/decisions/inbox/bishop-nature-datasets.md` for complete dataset catalog with access paths, metadata, and integration roadmap.

---

## Phase 4 Analysis: Data Ingestion and Curation Strategy (2026-04-16)

**Request:** Assess data layer architecture; clarify relationship between raw source ingestion, per-source evaluation, and subdataset curation with case variability.

### Key Tension Identified

Three competing needs:
1. **Store raw source datasets** (data29/data-repos/raw/)
2. **Audit each source independently** (separate concerns)
3. **Create mixed subdatasets** for case variability (bench/datasets current practice)

**Current state:** Datasets flow raw → processed → mixed without explicit provenance tracking. After evaluation, no way to decompose metrics by source family.

### Recommended Architecture: Three-Tier Model

**Tier 1 — Raw Source Repository** (data29/data-repos/raw/)
- Immutable archive with SOURCE_MANIFEST.json (provenance, source type, clinical context)
- Each source documented: origin URL, license, clinical collection dates, schema version, hash
- Enforce readonly after ingestion

**Tier 2 — Normalized Intermediates** (data29/data-repos/normalized-by-source/)
- Per-source processing: schema normalization, ICD-10 mapping, complexity assignment
- QA validation per source: run Parker checklist before merging
- Generate qa_report_*.txt for each source (boilerplate%, leakage%, language mixing%)
- Separate concerns: identify source-specific issues; don't mix until audited

**Tier 3 — Curated Evaluation Datasets** (data29/data-repos/curated-datasets/)
- Mixed subdatasets with **lineage tracking**: _metadata.json + _lineage.txt per dataset
- Composition documented: cases per source, diversity strategy (ICD-10 chapters, complexity bins, severity tiers)
- Each curated set linked back to normalized sources; immutable once created
- Enable decomposition of results by source family (stratified reporting)

### Critical Insight

**Both per-source evaluation AND mixed subdatasets are necessary — they serve different purposes.**

Per-source audit ≠ per-source evaluation. Audit sources in isolation to catch contamination BEFORE merging. Then deliberately mix for robustness testing. This prevents cross-contamination: clean + clean → trustworthy mixed results.

### Specific Learnings

1. **Subdataset mixing is clinically sound:** Single-source datasets may overfit to symptom patterns (e.g., RAMEDIS weighted toward metabolic disorders). Real systems see heterogeneous mixes. Mixing tests generalization.

2. **Current blind spot:** bench/datasets mixes sources without tracking composition. Can't answer "how many cases from source X?" or "is source Y degrading performance?" Metadata is invisible.

3. **QA before merge:** DxGPT internal (FAIL: 57% boilerplate, 26% leakage); RAMEDIS (PASS: <5% boilerplate, <2% leakage). Merge dirty + clean = both contaminated. Audit first.

4. **Provenance metadata is operational:** _lineage.txt (source_id → new_id mapping) enables:
   - Case-level debugging (which errors correlate with which sources?)
   - Stratified metrics (Recall@1 by source, complexity, language)
   - Reproducibility (exact subset frozen, versionable)

5. **External source discipline matters:** Nature datasets (registries) avoid boilerplate through **disease-centric design**, not cleanup. Hospital EHR pipelines are operations-first, not diagnosis-first. Different preprocessing explains quality gap.

### Key Files/Paths

- Current raw: `data29/data-repos/raw/` (ramedis.json, medbulltes5op.json, urgtorre.json, etc.)
- Current processed: `bench/datasets/` (all_*.json, no provenance)
- Recommended new: `data29/data-repos/normalized-by-source/` + `curated-datasets/`
- QA tool: `bench/validation_checks.py` (Parker decision #5; ready to use)
- Nature catalog: `.squad/decisions/bishop-nature-datasets.md`

### Recommendation for Javier

1. Confirm source provenance for each file in raw/ (hospital EHR? synthetic? manual?)
2. Prioritize cleanup: clean DxGPT internal first, then ingest Nature datasets
3. Adopt three-tier structure for scalability (new sources added without touching existing evaluation sets)
4. Report results stratified by source (transparency + debugging)

### Decision Document

See `.squad/decisions.md` (Decision #9) for full architecture specification, implementation checklist, and phased roadmap.

---

## Phase 5: Data Architecture Decision Finalized (2026-04-16)

**Action:** Merged `.squad/decisions/inbox/bishop-data-ingestion-strategy.md` into `.squad/decisions.md` as Decision #9.

**Summary:** Three-tier data architecture approved:
- **Tier 1 (Raw):** Immutable source repository with SOURCE_MANIFEST.json
- **Tier 2 (Normalized):** Per-source processing with Parker QA validation
- **Tier 3 (Curated):** Mixed subdatasets with lineage tracking

**Implementation Status:** READY — Awaiting Javier confirmation to proceed with Tier 1 setup.

**Cross-team update:** Coordinated with Dallas (Evaluation Engineer) on dual-mode strategy to ensure data architecture supports per-source audit + optional mixed evaluation.
