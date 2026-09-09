# Auditoría del juez — all_256_clean, gpt-5.6-terra xhigh

Estado: **provisional**. Mismas respuestas y códigos que el artefacto
merged (run 12k + splice 20k de 4 EMPTY). Solo cambia el prompt del juez.
`docs/benchmark-report.html` **no se reescribe**.

## Condiciones

- Dataset: `all_256_clean`, prompt `juanjo_classic_v2`, traducción ON.
- Modelo: `gpt-5.6-terra` **xhigh**. Runs `20260727185344` + retry
  `20260728103627` (R176, R193, R254, R549).
- Detalle de entrada: `outputs/judge_audit/terra_xhigh_merged_evaluation_details.txt`.
- Juez: `gemini-2.5-pro`, `strict_equivalence`.
- Script: `reeval_traditional_strict.py`.

## Métricas

| Modelo | Juez | R@1 | R@3 | R@5 | Cobertura | Pos. media | MRR |
|---|---|---:|---:|---:|---:|---:|---:|
| Terra xhigh | legacy (merged) | 76,2% | 91,0% | 96,1% | 96,9% | 1,427 | 0,841 |
| Terra xhigh | strict | 62,5% | 75,0% | 78,9% | 79,7% | 1,431 | 0,691 |
| Terra medium | strict | 62,5% | 79,3% | 84,0% | 84,4% | 1,491 | 0,710 |
| Terra high | strict | 62,5% | 80,5% | 84,4% | 85,2% | 1,477 | 0,716 |
| Terra low | strict | 63,3% | 80,1% | 83,2% | 83,2% | 1,404 | 0,714 |

Con strict, xhigh empata el R@1 de high/medium (62,5%) y **pierde cobertura**
(79,7%, la peor de Terra). Legacy tenía el mejor R@1 de Terra (76,2%);
strict se lo come (LLM 75→29). Low sigue 1º por R@1. **No usar xhigh.**

Curva strict por R@1 luego cobertura: low > high > medium > xhigh.

## Trazabilidad

- Legacy 12k: `.../gpt_5_6_terra_xhigh_translated_en/20260727185344/`
- Merge: `outputs/judge_audit/terra_xhigh_merged_evaluation_details.txt`
- Strict: `outputs/judge_audit/all256_gpt56terra_xhigh_strict/`
- Medium: [2026-09-09-all256-judge-audit-strict-terra-medium.md](2026-09-09-all256-judge-audit-strict-terra-medium.md).
