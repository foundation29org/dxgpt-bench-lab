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
