# Auditoría del juez — all_256_clean, gemini-3.8-flash low

Estado: **provisional**. Inferencia nueva (`20260915150337`) y re-score
`strict_equivalence` sobre las mismas listas. Pipeline V4 no se modificó.
`docs/benchmark-report.html` **no se reescribe**.

Pregunta: ¿rompe el techo Gemini ~75% de cobertura strict, o cae igual
que 3.5-flash / 3-pro?

## Condiciones

- Dataset: `all_256_clean`, prompt `juanjo_classic_v2`, traducción ON.
- Modelo: `gemini-3.8-flash` low. Run `20260915150337`.
- Juez: `gemini-2.5-pro`, `strict_equivalence`.
- Script: `reeval_traditional_strict.py`.
- Latencia emulador: media 4,4 s/caso (mediana 3,8; p95 7,7; n=256).

## Métricas

| Modelo | Juez | R@1 | R@3 | R@5 | Cobertura | Pos. media |
|---|---|---:|---:|---:|---:|---:|
| gemini-3.8-flash low | legacy | 73,8% | 94,1% | 98,0% | 98,0% | 1,406 |
| gemini-3.8-flash low | strict | 59,8% | 73,8% | 77,7% | 77,7% | 1,402 |
| gemini-3.5-flash low | strict | 62,1% | 75,4% | 75,4% | 75,4% | 1,223 |
| gemini-3.1-pro-preview low | strict | 61,3% | 74,6% | 75,0% | 75,0% | 1,240 |
| gemini-3-pro-preview low | strict | 59,8% | 74,6% | 75,0% | 75,0% | 1,281 |
| gpt-5.6-terra low | strict | 63,3% | 80,1% | 83,2% | 83,2% | 1,404 |

Recuento strict: P1 153, P2 23, P3 13, P4 9, P5 1; 57 sin match.
El juez LLM pasa de 76 a 23.

3.8 Flash **no gana a 3.5-flash** en R@1 (59,8% vs 62,1%). Sube un poco
la cobertura Gemini (77,7% vs 75,4%): primer Gemini por encima del 75%,
sigue lejos de Terra (83,2%). Empata el R@1 de 3-pro y lo gana en
cobertura. Es el Gemini más rápido del ranking (4,4 s vs 6,1 de 3.5-flash
y ~10 de 3-pro).

No sustituye a 3.5-flash como candidato avanzado. No sustituye a Terra
como default.

Estas cifras **no** se comparan con MedReaMM 100.

## Trazabilidad

- Legacy:
  `bench/pipelines/pipeline_v4 - fork/main/output/all_256_clean/juanjo_classic_v2/gemini_3_8_flash_low_translated_en/20260915150337/`
- Strict: `outputs/judge_audit/all256_gemini38flash_low_strict/`
- Config: `bench/pipelines/pipeline_v4 - fork/main/config_gemini38flash_low_all256.yaml`
- 3.5-flash:
  [2026-09-09-all256-judge-audit-strict-gemini35flash.md](2026-09-09-all256-judge-audit-strict-gemini35flash.md).
