# Auditoría del juez — all_256_clean, gpt-5.6-terra medium

Estado: **provisional**. Mismas respuestas y códigos que el run histórico
`20260710143407`. Solo cambia el prompt del juez. `docs/benchmark-report.html`
**no se reescribe**.

## Condiciones

- Dataset: `all_256_clean`, prompt `juanjo_classic_v2`, traducción ON.
- Modelo: `gpt-5.6-terra` **medium**. Run `20260710143407`.
- Juez: `gemini-2.5-pro`, `strict_equivalence`.
- Script: `reeval_traditional_strict.py`.

## Métricas

| Modelo | Juez | R@1 | R@3 | R@5 | Cobertura | Pos. media | MRR |
|---|---|---:|---:|---:|---:|---:|---:|
| Terra medium | legacy | 71,1% | 91,0% | 97,7% | 97,7% | 1,516 | 0,813 |
| Terra medium | strict | 62,5% | 79,3% | 84,0% | 84,4% | 1,491 | 0,710 |
| Terra high | strict | 62,5% | 80,5% | 84,4% | 85,2% | 1,477 | 0,716 |
| Terra low | strict | 63,3% | 80,1% | 83,2% | 83,2% | 1,404 | 0,714 |

Con strict, medium empata el R@1 de high (62,5%) y pierde cobertura
(84,4% vs 85,2%). Low sigue 1º por R@1 (63,3%). LLM 73→32.

La curva legacy low > high > medium se sostiene en R@1. xhigh pendiente.

## Trazabilidad

- Legacy: `.../gpt_5_6_terra_medium_translated_en/20260710143407/`
- Strict: `outputs/judge_audit/all256_gpt56terra_medium_strict/`
- High: [2026-09-09-all256-judge-audit-strict-terra-high.md](2026-09-09-all256-judge-audit-strict-terra-high.md).
