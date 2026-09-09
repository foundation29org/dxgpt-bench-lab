# Auditoría del juez — all_256_clean, gemini-3-pro, Sol medium y gpt-4o

Estado: **provisional**. Mismas respuestas y códigos que los runs históricos.
Solo cambia el prompt del juez. Pipeline V4 no se modificó. Mismo script y
mismo `gemini-2.5-pro` que el 31 ago (mini y Terra).

## Condiciones

- Dataset: `all_256_clean`, prompt `juanjo_classic_v2`, traducción ON.
- gemini-3-pro-preview low: run `20260418102428`.
- gpt-5.6-sol medium: run `20260727194932`.
- gpt-4o low (baseline histórico): run `20260416131009`.
- Juez: `gemini-2.5-pro`, `strict_equivalence`.
- Script: `reeval_traditional_strict.py`.

## Métricas

| Modelo | Juez | R@1 | R@3 | R@5 | Cobertura | Pos. media | MRR |
|---|---|---:|---:|---:|---:|---:|---:|
| gpt-5.4-mini low | legacy | 68,0% | 92,6% | 98,0% | 98,1% | 1,526 | 0,800 |
| gpt-5.4-mini low | strict | 58,2% | 77,3% | 79,3% | 79,7% | 1,441 | 0,670 |
| gpt-5.6-terra low | legacy | 74,6% | 94,9% | 98,0% | 98,1% | 1,382 | 0,843 |
| gpt-5.6-terra low | strict | 63,3% | 80,1% | 83,2% | 83,2% | 1,404 | 0,714 |
| gpt-5.6-sol medium | legacy | 69,9% | 89,5% | 96,9% | 97,7% | 1,584 | 0,801 |
| gpt-5.6-sol medium | strict | 60,9% | 76,2% | 81,2% | 82,4% | 1,540 | 0,690 |
| gemini-3-pro-preview low | legacy | 75,8% | 98,0% | 98,0% | 98,0% | 1,299 | 0,857 |
| gemini-3-pro-preview low | strict | 59,8% | 74,6% | 75,0% | 75,0% | 1,281 | 0,664 |
| gpt-4o low | legacy | 69,9% | 88,7% | 96,1% | 96,1% | 1,545 | 0,796 |
| gpt-4o low | strict | 57,4% | 69,9% | 74,6% | 75,0% | 1,505 | 0,636 |

Con legacy, gemini-3-pro era el mejor ranking (pos. 1,299, R@1 75,8%,
cobertura 98%). Con strict queda empatado con gpt-4o en cobertura (75%) y
por debajo de mini, Sol y Terra.

Eso **no** rehace el pipeline. Las listas DDX, SNOMED, ICD-10 y SapBERT
son las del run histórico. Solo cambia el último paso: el prompt del juez
LLM (`legacy_similarity` → `strict_equivalence`). El juez LLM de
gemini-3-pro pasa de 74 a 16 decisiones. El modelo no “acertaba menos”;
el árbitro dejaba de aceptar diagnósticos relacionados o más específicos
que no son la misma entidad que el gold.

El 98% narrativo era el juez legacy. Con strict, en `all_256_clean`:
Terra 83% > Sol 82% > mini 80% > gemini-3-pro = gpt-4o 75%. gemini-3-pro
no era el nº 1; era el que más “parecidos” le colaba el árbitro.

Estas cifras **no** se comparan con MedReaMM 100 (otro dataset, otro
flujo, imágenes). Solo puente de juez entre tracks.

## Trazabilidad

- gemini-3-pro legacy:
  `.../gemini_3_pro_preview_low_translated_en/20260418102428/`
- Sol medium legacy:
  `.../gpt_5_6_sol_medium_translated_en/20260727194932/`
- gpt-4o legacy:
  `.../gpt_4o_low_translated_en/20260416131009/`
- Strict: `outputs/judge_audit/all256_gemini3pro_low_strict/`,
  `all256_gpt56sol_medium_strict/`, `all256_gpt4o_low_strict/`.
- Mini y Terra: [2026-08-31-all256-judge-audit-strict-mini-terra.md](2026-08-31-all256-judge-audit-strict-mini-terra.md).
