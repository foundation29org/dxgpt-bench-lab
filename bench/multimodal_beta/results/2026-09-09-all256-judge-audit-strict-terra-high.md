# Auditoría del juez — all_256_clean, gpt-5.6-terra high

Estado: **provisional**. Mismas respuestas y códigos que el run histórico
`20260727181120`. Solo cambia el prompt del juez. `docs/benchmark-report.html`
**no se reescribe**.

## Condiciones

- Dataset: `all_256_clean`, prompt `juanjo_classic_v2`, traducción ON.
- Modelo: `gpt-5.6-terra` **high**. Run `20260727181120`.
- Juez: `gemini-2.5-pro`, `strict_equivalence`.
- Script: `reeval_traditional_strict.py`.

## Métricas

| Modelo | Juez | R@1 | R@3 | R@5 | Cobertura | Pos. media | MRR |
|---|---|---:|---:|---:|---:|---:|---:|
| Terra high | legacy | 71,9% | 93,0% | 97,3% | 97,3% | 1,426 | 0,824 |
| Terra high | strict | 62,5% | 80,5% | 84,4% | 85,2% | 1,477 | 0,716 |
| Terra low | strict | 63,3% | 80,1% | 83,2% | 83,2% | 1,404 | 0,714 |

Con strict, high **no gana a low en R@1** (62,5% vs 63,3%). Gana cobertura
(85,2% vs 83,2%). Rank: R@1 manda → low sigue 1º, high entra 3º (detrás
de gpt-5.4 full). LLM 71→35.

La ablación legacy (low > high) se sostiene en R@1. Medium y xhigh
pendientes.

## Trazabilidad

- Legacy: `.../gpt_5_6_terra_high_translated_en/20260727181120/`
- Strict: `outputs/judge_audit/all256_gpt56terra_high_strict/`
- Low: [2026-08-31-all256-judge-audit-strict-mini-terra.md](2026-08-31-all256-judge-audit-strict-mini-terra.md).
