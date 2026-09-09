# Auditoría del juez — all_256_clean, gpt-5.4 full (low)

Estado: **provisional**. Mismas respuestas y códigos que el run histórico
`20260417145054`. Solo cambia el prompt del juez. `docs/benchmark-report.html`
**no se reescribe**.

## Condiciones

- Dataset: `all_256_clean`, prompt `juanjo_classic_v2`, traducción ON.
- Modelo: `gpt-5.4` low (full, no mini). Run `20260417145054`.
- Juez: `gemini-2.5-pro`, `strict_equivalence`.
- Script: `reeval_traditional_strict.py`.

## Métricas

| Modelo | Juez | R@1 | R@3 | R@5 | Cobertura | Pos. media | MRR |
|---|---|---:|---:|---:|---:|---:|---:|
| gpt-5.4 full | legacy | 71,1% | 93,4% | 98,4% | 98,8% | 1,502 | 0,820 |
| gpt-5.4 full | strict | 62,9% | 80,9% | 85,5% | 86,3% | 1,502 | 0,720 |
| gpt-5.6-terra low | strict | 63,3% | 80,1% | 83,2% | 83,2% | 1,404 | 0,714 |
| gpt-5.4-mini low | strict | 58,2% | 77,3% | 79,3% | 79,7% | 1,441 | 0,670 |

Con strict, gpt-5.4 **gana a mini** (R@1 +4,7 pp, cobertura +6,6 pp) y
tiene la **mejor cobertura** del ranking (221/256, 86,3%). Terra low
sigue delante por R@1 (63,3% vs 62,9%; 162 vs 161 aciertos en P1).
LLM 64→27.

Rank: Terra 63,3% > **gpt-5.4 62,9%** > Astra 62,1%.

## Trazabilidad

- Legacy: `.../gpt_5_4_low_translated_en/20260417145054/`
- Strict: `outputs/judge_audit/all256_gpt54_low_strict/`
