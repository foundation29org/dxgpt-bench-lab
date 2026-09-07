# Project Context

- **Owner:** Javier Logroño
- **Project:** DxGPT evaluation repository for auditing dataset quality and diagnosis benchmark reliability
- **Stack:** Python, pandas, scikit-learn, torch, transformers, Azure Text Analytics, Azure Translator
- **Created:** 2026-04-14T12:02:03.824Z

## Learnings

- Initial focus: turn suspected dataset and pipeline flaws into explicit checks, adversarial cases, and reproducible validation steps.

### 2026-04-14 — QA Failure Modes Analysis

**Finding:** Bishop's dataset audit revealed five systematic failure modes (label leakage, boilerplate prefix, template markers, language mixing, list-format symptoms) affecting 1,254 cases across 9 datasets. Three are validity blockers; two degrade generalization.

**Key Insight:** 26% label leakage + 57% boilerplate prefix together guarantee inflated scores. A model can achieve 92.7% "success" while ranking 1.443 (worst percentile) vs. peers—metric divorce is a red flag.

**Decision:** Created QA checklist with eight explicit pass/fail gates that must succeed before trusting benchmark results. Gates operationalize Bishop's findings into reusable, testable rules.

**Action Items:**
- [ ] Implement validation script (`validation_checks.py`) that runs all gates on each dataset before eval.
- [ ] Label leakage threshold: ≤5% to pass (currently 26% aggregate).
- [ ] Boilerplate threshold: <10% (currently 57%).
- [ ] Version drift: every published result must include git commit + output path.
- [ ] Success metric sanity: report both % and rank together, never % alone.

**Caveat:** Current benchmark is **not trustworthy for decision-making** until Tier 1 cleanup is complete (label leakage removal, boilerplate stripping).

**Owner:** Javier to confirm blockers vs. warnings; Ripley to embed checks into eval workflow; Bishop to implement cleanup scripts.
