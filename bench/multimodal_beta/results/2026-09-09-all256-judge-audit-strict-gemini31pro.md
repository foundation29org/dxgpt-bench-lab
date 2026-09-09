# Auditoría del juez — all_256_clean, gemini-3.1-pro-preview low

Estado: **provisional**. Mismas respuestas y códigos que el run histórico
`20260710160926`. Solo cambia el prompt del juez. Pipeline V4 no se
modificó. `docs/benchmark-report.html` **no se reescribe**.

## Condiciones

- Dataset: `all_256_clean`, prompt `juanjo_classic_v2`, traducción ON.
- Modelo: `gemini-3.1-pro-preview` low. Run `20260710160926`.
- Juez: `gemini-2.5-pro`, `strict_equivalence`.
- Script: `reeval_traditional_strict.py`.

## Métricas

| Modelo | Juez | R@1 | R@3 | R@5 | Cobertura | Pos. media | MRR |
|---|---|---:|---:|---:|---:|---:|---:|
| gemini-3.1-pro-preview low | legacy | 77,3% | 97,7% | 98,1% | 98,1% | 1,267 | 0,868 |
| gemini-3.1-pro-preview low | strict | 61,3% | 74,6% | 75,0% | 75,0% | 1,240 | 0,675 |
| gemini-3-pro-preview low | strict | 59,8% | 74,6% | 75,0% | 75,0% | 1,281 | 0,664 |
| gpt-5.6-terra low | strict | 63,3% | 80,1% | 83,2% | 83,2% | 1,404 | 0,714 |
| gpt-5.6-sol medium | strict | 60,9% | 76,2% | 81,2% | 82,4% | 1,540 | 0,690 |

Con legacy, 3.1-pro era el líder narrativo del HTML oficial (pos. 1,267,
R@1 77,3%, cobertura 98,1%). Con strict baja a **192/256 (75%)**, la
misma cobertura que gemini-3-pro. Gana a 3-pro en R@1 (61,3% vs 59,8%)
con cobertura idéntica. Pierde cobertura frente a Terra (83%) y Sol (82%).

El juez LLM pasa de 75 a 17 decisiones. El modelo no “acertaba menos”;
el árbitro dejaba de aceptar relacionados.

Rank all_256 strict (R@1, luego cobertura): Terra 63,3% > Astra 62,1% >
3.1-pro 61,3% > Sol 60,9% > 3-pro 59,8% > mini 58,2% > gpt-4o 57,4%.
3.1-pro entra por R@1 por encima de Sol; su cobertura es la de Gemini
(75%), no la de Terra/Sol.

Estas cifras **no** se comparan con MedReaMM 100.

## Trazabilidad

- Legacy:
  `.../gemini_3_1_pro_preview_low_translated_en/20260710160926/`
- Strict: `outputs/judge_audit/all256_gemini31pro_low_strict/`
- gemini-3-pro, Sol, gpt-4o:
  [2026-09-08-all256-judge-audit-strict-gemini3pro-sol-gpt4o.md](2026-09-08-all256-judge-audit-strict-gemini3pro-sol-gpt4o.md).
