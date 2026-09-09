# Auditoría del juez — all_256_clean, gemini-3.5-flash low

Estado: **provisional**. Mismas respuestas y códigos que el run histórico
`20260710163857`. Solo cambia el prompt del juez. Pipeline V4 no se
modificó. `docs/benchmark-report.html` **no se reescribe**.

## Condiciones

- Dataset: `all_256_clean`, prompt `juanjo_classic_v2`, traducción ON.
- Modelo: `gemini-3.5-flash` low. Run `20260710163857`.
- Juez: `gemini-2.5-pro`, `strict_equivalence`.
- Script: `reeval_traditional_strict.py`.

## Métricas

| Modelo | Juez | R@1 | R@3 | R@5 | Cobertura | Pos. media | MRR |
|---|---|---:|---:|---:|---:|---:|---:|
| gemini-3.5-flash low | legacy | 77,0% | 97,3% | 97,7% | 97,7% | 1,284 | 0,862 |
| gemini-3.5-flash low | strict | 62,1% | 75,4% | 75,4% | 75,4% | 1,223 | 0,682 |
| gemini-3.1-pro-preview low | strict | 61,3% | 74,6% | 75,0% | 75,0% | 1,240 | 0,675 |
| gemini-3-pro-preview low | strict | 59,8% | 74,6% | 75,0% | 75,0% | 1,281 | 0,664 |
| gpt-6-astra low | strict | 62,1% | 78,5% | 82,0% | 83,2% | 1,460 | — |
| gpt-5.6-terra low | strict | 63,3% | 80,1% | 83,2% | 83,2% | 1,404 | 0,714 |

Con legacy, Flash era el candidato calidad/latencia (casi 3.1-pro: R@1
77,0% vs 77,3%, 6,1 s/caso). Con strict baja a **193/256 (75,4%)**, el
mismo colapso Gemini que 3.1-pro y 3-pro. El juez LLM pasa de 72 a 14.

Flash **gana a 3.1-pro** en R@1 (62,1% vs 61,3%) y cobertura (193 vs 192).
Empata el R@1 de Astra (62,1%); Astra gana por cobertura (83,2% vs 75,4%).

Rank all_256 strict (R@1, luego cobertura): Terra 63,3% > Astra 62,1%
(cobertura 83%) > Flash 62,1% (cobertura 75%) > 3.1-pro 61,3% > Sol 60,9%
> 3-pro 59,8% > mini 58,2% > gpt-4o 57,4%.

Estas cifras **no** se comparan con MedReaMM 100.

## Trazabilidad

- Legacy:
  `.../gemini_3_5_flash_low_translated_en/20260710163857/`
- Strict: `outputs/judge_audit/all256_gemini35flash_low_strict/`
- 3.1-pro:
  [2026-09-09-all256-judge-audit-strict-gemini31pro.md](2026-09-09-all256-judge-audit-strict-gemini31pro.md).
