# Auditoría del juez — all_256_clean, gemini-2.5-pro low

Estado: **provisional**. Mismas respuestas y códigos que el run histórico
`20260417174222`. Solo cambia el prompt del juez. Pipeline V4 no se
modificó. `docs/benchmark-report.html` **no se reescribe**.

Por qué ahora: el Server configura `gemini-3-pro-preview` como avanzado,
pero ese slug devuelve 404 y la cadena cae a `gemini-2.5-pro`
(`services/helpDiagnose.js`, `callAdvancedModelChain`). El avanzado real
en producción es 2.5 Pro y no tenía cifra strict.

## Condiciones

- Dataset: `all_256_clean`, prompt `juanjo_classic_v2`, traducción ON.
- Modelo: `gemini-2.5-pro` low. Run `20260417174222`.
- Juez: `gemini-2.5-pro`, `strict_equivalence`. **El juez es el mismo
  modelo que el evaluado.** El resultado no muestra inflación: cae igual
  que el resto de Gemini.
- Script: `reeval_traditional_strict.py`.

## Métricas

| Modelo | Juez | R@1 | R@3 | R@5 | Cobertura | Pos. media | MRR |
|---|---|---:|---:|---:|---:|---:|---:|
| gemini-2.5-pro low | legacy | 77,0% | 95,7% | 98,1% | 98,1% | 1,299 | — |
| gemini-2.5-pro low | strict | 59,4% | 74,2% | 75,4% | 75,4% | 1,295 | 0,664 |
| gemini-3-pro-preview low | strict | 59,8% | 74,6% | 75,0% | 75,0% | 1,281 | 0,664 |
| gemini-3.5-flash low | strict | 62,1% | 75,4% | 75,4% | 75,4% | 1,223 | 0,682 |
| gpt-5.6-terra low | strict | 63,3% | 80,1% | 83,2% | 83,2% | 1,404 | 0,714 |

Recuento strict: P1 152, P2 28, P3 10, P4 3; 63 sin match. El juez LLM
pasa de 87 a 23 decisiones.

Empata con `gemini-3-pro-preview` (59,4% vs 59,8%; 193 vs 192 matches).
El cambio de 2.5 Pro a 3-pro que se hizo el 18 de agosto no movía la
métrica strict; y en producción tampoco llegó a aplicarse.

`gemini-3.5-flash low` gana a ambos en R@1 (+2,7 pp), misma cobertura,
6,1 s/caso frente a ~28 s de 2.5 Pro. Ninguno de los tres alcanza a Terra
low en R@1 ni en cobertura.

Latencia del run original: ~28–34 s/caso.

Estas cifras **no** se comparan con MedReaMM 100.

## Trazabilidad

- Legacy:
  `bench/pipelines/pipeline_v4 - fork/main/output/all_256_clean/juanjo_classic_v2/gemini_2_5_pro_low_translated_en/20260417174222/`
- Strict: `outputs/judge_audit/all256_gemini25pro_low_strict/`
- 3-pro, Sol, gpt-4o:
  [2026-09-08-all256-judge-audit-strict-gemini3pro-sol-gpt4o.md](2026-09-08-all256-judge-audit-strict-gemini3pro-sol-gpt4o.md).
- 3.5-flash:
  [2026-09-09-all256-judge-audit-strict-gemini35flash.md](2026-09-09-all256-judge-audit-strict-gemini35flash.md).
