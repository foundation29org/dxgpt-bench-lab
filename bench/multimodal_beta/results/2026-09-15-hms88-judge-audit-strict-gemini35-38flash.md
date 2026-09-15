# Auditoría del juez — HMS HPO 88, gemini-3.5-flash y 3.8-flash

Estado: **provisional**. Inferencia nueva (2026-09-15), prompt
`juanjo_classic_v2`, `TRANSLATE_CASE` off, `thinking_level` low. Gold
ORPHA: cero SNOMED/ICD. n=88 es ruido para un flip de producto.

Paso 1 del plan HPO en `docs/ROADMAP.md` §4.5: si 3.8 no gana R@1 a 3.5
ni a Terra, se para. 3.8 gana a 3.5 y pierde con Terra (1 caso).

## Condiciones

- Dataset: `hms_hpo.json`, 88 casos.
- Juez: `gemini-2.5-pro`, `reeval_traditional_strict.py`.
- gemini-3.5-flash low: run `20260915170201`. ~6,9 s/caso.
- gemini-3.8-flash low: run `20260915170206`. ~5,4 s/caso.

## Métricas

| Modelo | Juez | R@1 | R@3 | R@5 | Cobertura | Pos. media |
|---|---|---:|---:|---:|---:|---:|
| gemini-3.5-flash low | legacy | 63,6% | 98,9% | 98,9% | 98,9% | 1,517 |
| gemini-3.5-flash low | strict | 38,6% | 48,9% | 48,9% | 48,9% | 1,326 |
| gemini-3.8-flash low | legacy | 59,1% | 89,8% | 100% | 100% | 1,886 |
| gemini-3.8-flash low | strict | 42,0% | 51,1% | 54,5% | 54,5% | 1,521 |
| gemini-3-pro-preview low | strict | 46,6% | 52,3% | 52,3% | 52,3% | 1,152 |
| gpt-5.6-terra low | strict | 43,2% | 60,2% | 65,9% | 65,9% | 1,690 |
| gemini-2.5-pro low | strict | 40,9% | 55,7% | 59,1% | 59,1% | 1,481 |
| gpt-5.4-mini low | strict | 36,4% | 48,9% | 54,5% | 54,5% | 1,646 |

LLM: 3.5-flash 42 → 5; 3.8-flash 40 → 7.

Rank HMS strict por R@1: 3-pro 46,6% > Terra 43,2% > 3.8-flash 42,0% >
2.5-pro 40,9% > 3.5-flash 38,6% > mini 36,4%. Por cobertura: Terra 65,9%
> 2.5-pro 59,1% > mini = 3.8-flash 54,5% > 3-pro 52,3% > 3.5-flash 48,9%.

En all_256, 3.5 ganaba R@1 a 3.8 (62,1% vs 59,8%). En HMS se invierte:
3.8 42,0% vs 3.5 38,6%. Ninguno alcanza a Terra. 3.5-flash, el candidato
barato a avanzado por all_256, queda por debajo de 2.5-pro (el avanzado
real de prod) en R@1 y en cobertura.

Gate: 3.8 gana R@1 a 3.5, pierde con Terra (37 vs 38 aciertos P1). DDD
strict queda opcional; no se lanza solo con este n=88.

Estas cifras no se mezclan con MedReaMM ni con `all_256_clean`.

## Trazabilidad

- 3.5-flash:
  `bench/pipelines/pipeline_v4 - fork/main/output/hms_hpo/juanjo_classic_v2/gemini_3_5_flash_low/20260915170201/`
- 3.5-flash strict: `outputs/judge_audit/hms88_gemini35flash_low_strict/`
- 3.8-flash:
  `.../gemini_3_8_flash_low/20260915170206/`
- 3.8-flash strict: `outputs/judge_audit/hms88_gemini38flash_low_strict/`
- 2.5-pro / 3.1-pro:
  [2026-09-15-hms88-judge-audit-strict-gemini25pro-31pro.md](2026-09-15-hms88-judge-audit-strict-gemini25pro-31pro.md).
