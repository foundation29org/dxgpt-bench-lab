# Auditoría del juez — all_256_clean, gpt-5.6-luna medium

Estado: **provisional**. Mismas respuestas y códigos que el run histórico
`20260710133922`. Solo cambia el prompt del juez. `docs/benchmark-report.html`
**no se reescribe**.

## Condiciones

- Dataset: `all_256_clean`, prompt `juanjo_classic_v2`, traducción ON.
- Modelo: `gpt-5.6-luna` **medium**. Run `20260710133922`.
- Juez: `gemini-2.5-pro`, `strict_equivalence`.
- Script: `reeval_traditional_strict.py`.

## Métricas

| Modelo | Juez | R@1 | R@3 | R@5 | Cobertura | Pos. media | MRR |
|---|---|---:|---:|---:|---:|---:|---:|
| Luna medium | legacy | 66,0% | 91,4% | 97,3% | 97,7% | 1,584 | 0,784 |
| Luna medium | strict | 56,6% | 74,2% | 78,9% | 79,7% | 1,554 | 0,654 |
| Luna low | strict | 57,0% | 73,8% | 78,5% | 79,7% | 1,554 | 0,657 |

Con strict, medium **no gana a low** en R@1 (56,6% vs 57,0%). Misma
cobertura 79,7%. LLM 80→31. **No usar medium.** Low sigue siendo el luna
a comparar; tampoco gana a mini.

## Trazabilidad

- Legacy: `.../gpt_5_6_luna_medium_translated_en/20260710133922/`
- Strict: `outputs/judge_audit/all256_gpt56luna_medium_strict/`
- Low: [2026-09-09-all256-judge-audit-strict-luna-low.md](2026-09-09-all256-judge-audit-strict-luna-low.md).
