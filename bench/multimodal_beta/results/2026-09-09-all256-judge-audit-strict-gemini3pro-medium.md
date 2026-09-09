# Auditoría del juez — all_256_clean, gemini-3-pro-preview medium

Estado: **provisional**. Mismas respuestas y códigos que el run histórico
`20260421215831`. Solo cambia el prompt del juez. `docs/benchmark-report.html`
**no se reescribe**.

## Condiciones

- Dataset: `all_256_clean`, prompt `juanjo_classic_v2`, traducción ON.
- Modelo: `gemini-3-pro-preview` **medium**. Run `20260421215831`.
- Juez: `gemini-2.5-pro`, `strict_equivalence`.
- Script: `reeval_traditional_strict.py`.

## Métricas

| Modelo | Juez | R@1 | R@3 | R@5 | Cobertura | Pos. media | MRR |
|---|---|---:|---:|---:|---:|---:|---:|
| gemini-3-pro medium | legacy | 77,0% | 95,3% | 98,1% | 98,1% | 1,315 | 0,861 |
| gemini-3-pro medium | strict | 59,4% | 71,1% | 73,0% | 73,0% | 1,289 | 0,651 |
| gemini-3-pro low | strict | 59,8% | 74,6% | 75,0% | 75,0% | 1,281 | 0,664 |

Con legacy, medium ganaba 1,2 pp de R@1 a low y perdía R@3. Con strict
**pierde en todo**: R@1 59,4% vs 59,8%, cobertura 73,0% vs 75,0%, R@3
71,1% vs 74,6%. LLM 81→17.

La decisión de no usar medium se sostiene (y se refuerza) con el juez
estricto.

## Trazabilidad

- Legacy: `.../gemini_3_pro_preview_medium_translated_en/20260421215831/`
- Strict: `outputs/judge_audit/all256_gemini3pro_medium_strict/`
- Low: [2026-09-08-all256-judge-audit-strict-gemini3pro-sol-gpt4o.md](2026-09-08-all256-judge-audit-strict-gemini3pro-sol-gpt4o.md).
