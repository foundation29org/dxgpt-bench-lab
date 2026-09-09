# Auditoría del juez — all_256_clean, gpt-5.6-luna low

Estado: **provisional**. Mismas respuestas y códigos que el run histórico
`20260710130720`. Solo cambia el prompt del juez. `docs/benchmark-report.html`
**no se reescribe**.

## Condiciones

- Dataset: `all_256_clean`, prompt `juanjo_classic_v2`, traducción ON.
- Modelo: `gpt-5.6-luna` **low**. Run `20260710130720`.
- Juez: `gemini-2.5-pro`, `strict_equivalence`.
- Script: `reeval_traditional_strict.py`.

## Métricas

| Modelo | Juez | R@1 | R@3 | R@5 | Cobertura | Pos. media | MRR |
|---|---|---:|---:|---:|---:|---:|---:|
| Luna low | legacy | 69,1% | 90,2% | 97,7% | 97,7% | 1,540 | 0,802 |
| Luna low | strict | 57,0% | 73,8% | 78,5% | 79,7% | 1,554 | 0,657 |
| Mini low | strict | 58,2% | 77,3% | 79,3% | 79,7% | 1,441 | — |
| Terra low | strict | 63,3% | 80,1% | 83,2% | 83,2% | 1,404 | 0,714 |

Con strict, luna **no gana a mini** (R@1 57,0% vs 58,2%; misma cobertura
79,7%). Queda 15º, entre gpt-4o y gemini-2.5-flash. LLM 79→29.

La lectura legacy (competitivo, no supera a mini) se sostiene.

## Trazabilidad

- Legacy: `.../gpt_5_6_luna_low_translated_en/20260710130720/`
- Strict: `outputs/judge_audit/all256_gpt56luna_low_strict/`
- Mini: [2026-08-31-all256-judge-audit-strict-mini-terra.md](2026-08-31-all256-judge-audit-strict-mini-terra.md).
