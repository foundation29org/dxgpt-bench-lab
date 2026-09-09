# Auditoría del juez — all_256_clean, gpt-5.6-sol low

Estado: **provisional**. Mismas respuestas y códigos que el run histórico
`20260710151007`. Solo cambia el prompt del juez. `docs/benchmark-report.html`
**no se reescribe**.

## Condiciones

- Dataset: `all_256_clean`, prompt `juanjo_classic_v2`, traducción ON.
- Modelo: `gpt-5.6-sol` **low**. Run `20260710151007`.
- Juez: `gemini-2.5-pro`, `strict_equivalence`.
- Script: `reeval_traditional_strict.py`.

## Métricas

| Modelo | Juez | R@1 | R@3 | R@5 | Cobertura | Pos. media | MRR |
|---|---|---:|---:|---:|---:|---:|---:|
| Sol low | legacy | 68,4% | 88,7% | 98,4% | 98,4% | 1,619 | 0,795 |
| Sol low | strict | 59,0% | 73,8% | 80,5% | 80,9% | 1,527 | 0,673 |
| Sol medium | strict | 60,9% | 76,2% | 81,2% | 82,4% | 1,540 | — |
| Mini low | strict | 58,2% | 77,3% | 79,3% | 79,7% | 1,441 | — |

Con strict, low **no gana a medium** (59,0% vs 60,9% R@1; 80,9% vs 82,4%
cobertura). Sí gana a mini. LLM 74→24. **Mantener Sol medium.**

Cola luna + sol low cerrada.

## Trazabilidad

- Legacy: `.../gpt_5_6_sol_low_translated_en/20260710151007/`
- Strict: `outputs/judge_audit/all256_gpt56sol_low_strict/`
- Sol medium: [2026-09-08-all256-judge-audit-strict-gemini3pro-sol-gpt4o.md](2026-09-08-all256-judge-audit-strict-gemini3pro-sol-gpt4o.md).
