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
