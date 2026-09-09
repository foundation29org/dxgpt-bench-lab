# Auditoría del juez — all_256_clean, gemini-2.5-flash low

Estado: **provisional**. Mismas respuestas y códigos que el run histórico
`20260418111043`. Solo cambia el prompt del juez. Pipeline V4 no se
modificó. `docs/benchmark-report.html` **no se reescribe**.

## Condiciones

- Dataset: `all_256_clean`, prompt `juanjo_classic_v2`, traducción ON.
- Modelo: `gemini-2.5-flash` low. Run `20260418111043`.
- Juez: `gemini-2.5-pro`, `strict_equivalence`.
- Script: `reeval_traditional_strict.py`.

## Métricas

| Modelo | Juez | R@1 | R@3 | R@5 | Cobertura | Pos. media | MRR |
|---|---|---:|---:|---:|---:|---:|---:|
| gemini-2.5-flash low | legacy | 69,9% | 94,9% | 98,1% | 98,1% | 1,434 | 0,818 |
| gemini-2.5-flash low | strict | 56,6% | 72,7% | 74,2% | 74,2% | 1,342 | 0,643 |
| gemini-3.5-flash low | strict | 62,1% | 75,4% | 75,4% | 75,4% | 1,223 | 0,682 |
| gemini-3.1-flash-lite low | strict | 57,8% | 74,6% | 78,1% | 78,1% | 1,445 | 0,659 |
| gpt-4o low | strict | 57,4% | 69,9% | 74,6% | 75,0% | 1,505 | 0,636 |

Con legacy cubría 251/256 (98,1%). Con strict baja a **190/256 (74,2%)**,
el suelo de la familia Gemini (por debajo de 3.5-flash 75,4% y de
flash-lite 78,1%). El juez LLM pasa de 82 a 20.

Queda **por debajo de gpt-4o** en R@1 (56,6% vs 57,4%) y cobertura
(74,2% vs 75,0%). 3.5-flash gana a 2.5-flash por 5,5 pp de R@1.

Estas cifras **no** se comparan con MedReaMM 100.

## Trazabilidad

- Legacy:
  `.../gemini_2_5_flash_low_translated_en/20260418111043/`
- Strict: `outputs/judge_audit/all256_gemini25flash_low_strict/`
