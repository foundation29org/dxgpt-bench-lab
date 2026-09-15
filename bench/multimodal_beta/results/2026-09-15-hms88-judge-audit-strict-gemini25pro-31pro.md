# Auditoría del juez — HMS HPO 88, gemini-2.5-pro y 3.1-pro

Estado: **provisional**. Mismas listas DDX que los runs legacy. Solo cambia
el prompt del juez a `strict_equivalence`. Gold ORPHA: cero SNOMED/ICD.
n=88 es ruido para un flip de producto.

Paso 1 del plan HPO en `docs/ROADMAP.md` §4.5: 2.5-pro es el avanzado
real de producción (slug 3-pro 404). 3.1-pro era el candidato de julio.

## Condiciones

- Dataset: `hms_hpo.json`, 88 casos, prompt `juanjo_classic_v2`.
- Juez: `gemini-2.5-pro`, `reeval_traditional_strict.py`.
- gemini-2.5-pro low: run `20260417221140`.
- gemini-3.1-pro-preview low: run `20260713164514`.

## Métricas

| Modelo | Juez | R@1 | R@3 | R@5 | Cobertura | Pos. media |
|---|---|---:|---:|---:|---:|---:|
| gemini-2.5-pro low | legacy | 56,8% | 90,9% | 100% | 100% | 1,693 |
| gemini-2.5-pro low | strict | 40,9% | 55,7% | 59,1% | 59,1% | 1,481 |
| gemini-3.1-pro-preview low | legacy | 68,2% | 98,9% | 100% | 100% | 1,443 |
| gemini-3.1-pro-preview low | strict | 43,2% | 50,0% | 51,1% | 51,1% | 1,267 |
| gemini-3-pro-preview low | strict | 46,6% | 52,3% | 52,3% | 52,3% | 1,152 |
| gpt-5.6-terra low | strict | 43,2% | 60,2% | 65,9% | 65,9% | 1,690 |
| gpt-5.4-mini low | strict | 36,4% | 48,9% | 54,5% | 54,5% | 1,646 |

LLM: 2.5-pro 37 → 10; 3.1-pro 42 → 9.

Rank HMS strict por R@1: 3-pro 46,6% > Terra = 3.1-pro 43,2% > 2.5-pro
40,9% > mini 36,4%. Por cobertura: Terra 65,9% > 2.5-pro 59,1% > mini
54,5% > 3-pro 52,3% > 3.1-pro 51,1%.

El avanzado real (2.5-pro) no gana a Terra en R@1 ni en cobertura. 3.1-pro
empata R@1 con Terra y pierde cobertura; el 100% legacy era el juez viejo.
3-pro sigue primero en R@1 y último entre Geminis en cobertura.

3.5-flash y 3.8-flash van aparte (inferencia nueva, mismo día).

Estas cifras no se mezclan con MedReaMM ni con `all_256_clean`.

## Trazabilidad

- 2.5-pro legacy:
  `bench/pipelines/pipeline_v4 - fork/main/output/hms_hpo/juanjo_classic_v2/gemini_2_5_pro_low/20260417221140/`
- 2.5-pro strict: `outputs/judge_audit/hms88_gemini25pro_low_strict/`
- 3.1-pro legacy:
  `.../gemini_3_1_pro_preview_low/20260713164514/`
- 3.1-pro strict: `outputs/judge_audit/hms88_gemini31pro_low_strict/`
- mini / 3-pro:
  [2026-09-15-hms88-judge-audit-strict-mini-gemini3pro.md](2026-09-15-hms88-judge-audit-strict-mini-gemini3pro.md).
