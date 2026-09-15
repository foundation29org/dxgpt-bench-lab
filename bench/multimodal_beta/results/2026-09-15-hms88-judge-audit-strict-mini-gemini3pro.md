# Auditoría del juez — HMS HPO 88, mini y gemini-3-pro

Estado: **provisional**. Mismas listas DDX que los runs legacy. Solo cambia
el prompt del juez a `strict_equivalence`. Gold ORPHA: cero SNOMED/ICD;
casi todo pasa por BERT o LLM. n=88 es ruido para un flip de producto.

## Condiciones

- Dataset: `hms_hpo.json`, 88 casos, prompt `juanjo_classic_v2`.
- Juez: `gemini-2.5-pro`, `reeval_traditional_strict.py`.
- Mini: run `20260417175146`.
- gemini-3-pro-preview low: run `20260420160939`.
- Terra y Astra ya estaban: `hms88_gpt56terra_low_strict`,
  `hms88_gpt6astra_low_strict`.

## Métricas

| Modelo | Juez | R@1 | R@3 | R@5 | Cobertura | Pos. media |
|---|---|---:|---:|---:|---:|---:|
| gpt-5.4-mini low | legacy | 53,4% | 86,4% | 100% | 100% | 1,909 |
| gpt-5.4-mini low | strict | 36,4% | 48,9% | 54,5% | 54,5% | 1,646 |
| gemini-3-pro-preview low | legacy | 72,7% | 100% | 100% | 100% | 1,375 |
| gemini-3-pro-preview low | strict | 46,6% | 52,3% | 52,3% | 52,3% | 1,152 |
| gpt-5.6-terra low | strict | 43,2% | 60,2% | 65,9% | 65,9% | 1,690 |
| gpt-6-astra low | strict | 43,2% | 54,5% | 59,1% | 59,1% | 1,577 |

LLM: mini 38 → 7; 3-pro 40 → 7; Terra 63 → 15.

Rank HMS strict por R@1: 3-pro 46,6% > Terra = Astra 43,2% > mini 36,4%.
Por cobertura: Terra 65,9% > Astra 59,1% > mini 54,5% > 3-pro 52,3%.

3-pro, cuando acierta, lo pone casi siempre en P1 (pos. 1,152). No
recupera matches tardíos. Terra cubre más casos. El 100% legacy de 3-pro
era el juez viejo, no equivalencia de entidad.

Mini no gana a Terra en ninguna métrica strict. 3-pro gana R@1 y pierde
cobertura. n=88 no cierra el avanzado; hace falta RAMEDIS/DDD para eso.

Estas cifras no se mezclan con MedReaMM ni con `all_256_clean`.

## Trazabilidad

- Mini legacy:
  `bench/pipelines/pipeline_v4 - fork/main/output/hms_hpo/juanjo_classic_v2/gpt_5_4_mini_low/20260417175146/`
- Mini strict: `outputs/judge_audit/hms88_gpt54mini_low_strict/`
- 3-pro legacy:
  `.../gemini_3_pro_preview/20260420160939/`
- 3-pro strict: `outputs/judge_audit/hms88_gemini3pro_low_strict/`
- Terra/Astra:
  [2026-09-09-hms88-gpt6astra.md](2026-09-09-hms88-gpt6astra.md).
