# Auditoría del juez — all_256_clean, gemini-3.1-flash-lite low

Estado: **provisional**. Mismas respuestas y códigos que el run histórico
`20260710170553`. Solo cambia el prompt del juez. Pipeline V4 no se
modificó. `docs/benchmark-report.html` **no se reescribe**.

## Condiciones

- Dataset: `all_256_clean`, prompt `juanjo_classic_v2`, traducción ON.
- Modelo: `gemini-3.1-flash-lite` low. Run `20260710170553`.
- Juez: `gemini-2.5-pro`, `strict_equivalence`.
- Script: `reeval_traditional_strict.py`.

## Métricas

| Modelo | Juez | R@1 | R@3 | R@5 | Cobertura | Pos. media | MRR |
|---|---|---:|---:|---:|---:|---:|---:|
| gemini-3.1-flash-lite low | legacy | 69,1% | 91,8% | 98,8% | 98,8% | 1,526 | 0,809 |
| gemini-3.1-flash-lite low | strict | 57,8% | 74,6% | 78,1% | 78,1% | 1,445 | 0,659 |
| gpt-5.4-mini low | strict | 58,2% | 77,3% | 79,3% | 79,7% | 1,441 | 0,670 |
| gemini-3.5-flash low | strict | 62,1% | 75,4% | 75,4% | 75,4% | 1,223 | 0,682 |
| gpt-4o low | strict | 57,4% | 69,9% | 74,6% | 75,0% | 1,505 | 0,636 |

Con legacy, flash-lite era el candidato económico: mismo avg que mini
(1,526), +2 matches (98,8% vs 98,1%) y 2,8 s/caso. Con strict **no gana a
mini**: R@1 57,8% vs 58,2%, cobertura 78,1% vs 79,7%. El juez LLM pasa de
83 a 27 (más decisiones que Flash/3.1-pro, que bajaron a 14–17).

La cobertura (78%) queda entre mini (80%) y el cluster Gemini grande
(75%). No es el colapso a 75% de 3-pro / 3.1-pro / Flash; tampoco supera
al default de producto.

Rank all_256 strict (R@1, luego cobertura): Terra 63,3% > Astra 62,1%
(83%) > Flash 62,1% (75%) > 3.1-pro 61,3% > Sol 60,9% > 3-pro 59,8% >
mini 58,2% > **flash-lite 57,8%** > gpt-4o 57,4%.

Estas cifras **no** se comparan con MedReaMM 100.

## Trazabilidad

- Legacy:
  `.../gemini_3_1_flash_lite_low_translated_en/20260710170553/`
- Strict: `outputs/judge_audit/all256_gemini31flashlite_low_strict/`
- Flash:
  [2026-09-09-all256-judge-audit-strict-gemini35flash.md](2026-09-09-all256-judge-audit-strict-gemini35flash.md).
