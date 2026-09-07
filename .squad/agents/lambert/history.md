# Project Context

- **Owner:** Javier Logroño
- **Project:** DxGPT evaluation repository for auditing dataset quality and diagnosis benchmark reliability
- **Stack:** Python, pandas, scikit-learn, torch, transformers, Azure Text Analytics, Azure Translator
- **Created:** 2026-04-14T12:02:03.824Z

## Learnings

- Initial focus: review whether dataset phrasing, labels, and translations preserve clinical meaning and avoid unsafe or misleading diagnostic framing.
- `all_10`, `all_150`, and `all_275` are subsets of `all_450`, so major clinical-validity defects in `all_450` propagate into the smaller benchmark sets.
- The `R*` cases commonly use a Spanish boilerplate shell with English phenotype terms and frequent unknown demographics; this mixed-language symptom-list format is translation-sensitive and often pairs one vignette with multiple near-synonymous rare-disease labels.
- The `U*` cases are chart-style records with heavy administrative text and can include non-target labels such as treatment complications, precipitating illnesses, or past-history items alongside the main diagnosis.
- A nontrivial slice of `B*`/`Q*` cases are exam stems that depend on unseen figures or ask mechanism/management rather than diagnosis, which makes them unsafe for pure diagnostic benchmarking unless filtered.
