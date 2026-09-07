# Auditoría del juez — all_256_clean, mini y Terra low

Estado: **provisional**. Mismas respuestas y códigos que los runs históricos.
Solo cambia el prompt del juez. Pipeline V4 no se modificó.

## Condiciones

- Dataset: `all_256_clean`, prompt `juanjo_classic_v2`, traducción ON.
- Mini: run `20260417112331` (`gpt-5.4-mini` low).
- Terra: run `20260710140614` (`gpt-5.6-terra` low).
- Juez: `gemini-2.5-pro`, `strict_equivalence`.
- Script: `reeval_traditional_strict.py`.
- Salida: `outputs/judge_audit/all256_gpt54mini_low_strict/` y
  `outputs/judge_audit/all256_gpt56terra_low_strict/`.

## Métricas

| Modelo | Juez | R@1 | R@3 | R@5 | Cobertura | Pos. media | MRR |
|---|---|---:|---:|---:|---:|---:|---:|
| gpt-5.4-mini low | legacy | 68,0% | 92,6% | 98,0% | 98,1% | 1,526 | 0,800 |
| gpt-5.4-mini low | strict | 58,2% | 77,3% | 79,3% | 79,7% | 1,441 | 0,670 |
| gpt-5.6-terra low | legacy | 74,6% | 94,9% | 98,0% | 98,1% | 1,382 | 0,843 |
| gpt-5.6-terra low | strict | 63,3% | 80,1% | 83,2% | 83,2% | 1,404 | 0,714 |

Con legacy ambos cubren 251/256. Con strict, mini baja 47 casos (a 204) y
Terra 38 (a 213). Strict no recupera ningún caso que legacy hubiera
rechazado.

El 98,1% publicado de mini no es equivalencia diagnóstica. Bajo el mismo
juez que MedReaMM, mini queda en 79,7% y Terra en 83,2%. Terra gana a mini
en R@1 (+5,1 pp) y cobertura (+3,5 pp).

La posición media de mini “mejora” (1,526 → 1,441) porque caen matches
tardíos. No es una mejora de ranking: es pérdida de cobertura.

Decisiones del juez LLM: mini 71 → 24; Terra 70 → 26.

## Trazabilidad

- Mini legacy:
  `bench/pipelines/pipeline_v4 - fork/main/output/all_256_clean/juanjo_classic_v2/gpt_5_4_mini_low_translated_en/20260417112331/`
- Terra legacy:
  `bench/pipelines/pipeline_v4 - fork/main/output/all_256_clean/juanjo_classic_v2/gpt_5_6_terra_low_translated_en/20260710140614/`
