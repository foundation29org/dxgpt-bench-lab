# Auditoría del juez — all_256_clean, gpt-5.6-luna xhigh

Estado: **provisional e inválido como curva de effort**. 22/256 son
`EMPTY_RESPONSE` (reasoning agotó `max_tokens=12000`). No hay splice a 20k
como en Terra. `docs/benchmark-report.html` **no se reescribe**.

## Condiciones

- Dataset: `all_256_clean`, prompt `juanjo_classic_v2`, traducción ON.
- Modelo: `gpt-5.6-luna` **xhigh**. Run `20260727132551`.
- Juez: `gemini-2.5-pro`, `strict_equivalence`.
- Script: `reeval_traditional_strict.py`.

## Métricas

| Modelo | Juez | R@1 | R@3 | R@5 | Cobertura | Pos. media | MRR |
|---|---|---:|---:|---:|---:|---:|---:|
| Luna xhigh | legacy | 62,9% | 82,0% | 89,1% | 89,5% | 1,594 | 0,728 |
| Luna xhigh | strict | 55,5% | 69,5% | 73,0% | 75,0% | 1,573 | 0,626 |
| Luna high | strict | 60,9% | 77,3% | 82,0% | 83,6% | 1,575 | 0,693 |
| Luna low | strict | 57,0% | 73,8% | 78,5% | 79,7% | 1,554 | 0,657 |

El 75% de cobertura arrastra los 22 vacíos; no es que el juez se ponga más
duro. **No usar xhigh.** La luna que cuenta en strict es **high**. LLM 73→34.

## Trazabilidad

- Legacy: `.../gpt_5_6_luna_xhigh_translated_en/20260727132551/`
- Strict: `outputs/judge_audit/all256_gpt56luna_xhigh_strict/`
- High: [2026-09-09-all256-judge-audit-strict-luna-high.md](2026-09-09-all256-judge-audit-strict-luna-high.md).
