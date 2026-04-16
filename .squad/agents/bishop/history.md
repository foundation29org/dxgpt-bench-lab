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

### Recommendation
Phase 1: MyGene2 + RAMEDIS (~770 cases, 2–3 weeks)  
Phase 2: DDD phenotype (~2,283, if Phase 1 stable, 4–6 weeks)  
Phase 3: Defer genomic  
**Blocker:** Current DxGPT dataset fails QA; must clean first

### Full Analysis
See `.squad/decisions/inbox/bishop-nature-datasets.md` for complete dataset catalog with access paths, metadata, and integration roadmap.
