# Auditoría del juez — all_256_clean, gpt-6-astra low

Estado: **provisional**. Inferencia nueva de Astra; el puente legacy vs
strict usa las mismas listas DDX y los mismos códigos. Solo cambia el
prompt del juez. Pipeline V4 no se modificó.

## Condiciones

- Dataset: `all_256_clean`, prompt `juanjo_classic_v2`, traducción ON.
- Modelo: `gpt-6-astra`, `reasoning_effort: low`.
- Run: `20260908232755` (256/256, 0 listas vacías, ~32,5 s/caso).
- Juez: `gemini-2.5-pro`, `strict_equivalence`.
- Script: `reeval_traditional_strict.py`.
- Salida: `outputs/judge_audit/all256_gpt6astra_low_strict/`.
- Config de inferencia:
  `bench/pipelines/pipeline_v4 - fork/main/config_astra_low_all256.yaml`.

## Métricas

| Modelo | Juez | R@1 | R@3 | R@5 | Cobertura | Pos. media | MRR |
|---|---|---:|---:|---:|---:|---:|---:|
| gpt-5.4-mini low | legacy | 68,0% | 92,6% | 98,0% | 98,1% | 1,526 | 0,800 |
| gpt-5.4-mini low | strict | 58,2% | 77,3% | 79,3% | 79,7% | 1,441 | 0,670 |
| gpt-5.6-terra low | legacy | 74,6% | 94,9% | 98,0% | 98,1% | 1,382 | 0,843 |
| gpt-5.6-terra low | strict | 63,3% | 80,1% | 83,2% | 83,2% | 1,404 | 0,714 |
| gpt-5.6-sol medium | legacy | 69,9% | 89,5% | 96,9% | 97,7% | 1,584 | 0,801 |
| gpt-5.6-sol medium | strict | 60,9% | 76,2% | 81,2% | 82,4% | 1,540 | 0,690 |
| gpt-6-astra low | legacy | 72,3% | 93,0% | 98,0% | 98,1% | 1,442 | 0,827 |
| gpt-6-astra low | strict | 62,1% | 78,5% | 82,0% | 83,2% | 1,460 | 0,706 |
| gemini-3-pro-preview low | legacy | 75,8% | 98,0% | 98,0% | 98,0% | 1,299 | 0,857 |
| gemini-3-pro-preview low | strict | 59,8% | 74,6% | 75,0% | 75,0% | 1,281 | 0,664 |
| gpt-4o low | legacy | 69,9% | 88,7% | 96,1% | 96,1% | 1,545 | 0,796 |
| gpt-4o low | strict | 57,4% | 69,9% | 74,6% | 75,0% | 1,505 | 0,636 |

Con legacy, Astra cubre 251/256 (98,1%), igual que Terra y mini. No gana
el ranking HTML por `avg_pos`: 1,442 frente a Terra 1,382 y gemini-3-pro
1,299. R@1 72,3% frente a Terra 74,6%. Decisiones del juez LLM: 67
(Terra 70, gemini-3-pro 74).

Con strict, Astra empata a Terra en cobertura (213/256, **83,2%**) y queda
un punto por detrás en R@1 (62,1% vs 63,3%). Tres matches caen en P6–P7:
por eso R@5 (82,0%) es menor que la cobertura. Decisiones LLM: 67 → 24
(Terra 70 → 26).

El 98% narrativo era el juez legacy. Con strict, en `all_256_clean`:
Astra = Terra 83% > Sol 82% > mini 80% > gemini-3-pro = gpt-4o 75%.
Por R@1: Terra 63% > Astra 62% > Sol 61% > gemini-3-pro 60% > mini 58% >
gpt-4o 57%.

Estas cifras **no** se comparan con MedReaMM 100 (otro dataset, otro
flujo, imágenes). En MedReaMM texto, Astra T 67% vs Terra T 65%; aquí,
con el mismo juez strict sobre narrativa curada, no hay ventaja de
cobertura.

Decisión (2026-09-08): Astra no a producto. Latencia ~2× Terra, más
caro, y no gana en cobertura ni R@1. Un HPO pequeño (HMS 88 / MyGene2
146) queda como curiosidad opcional. **No DDD** (1.749 casos).

`docs/benchmark-report.html` se deja tal cual (legacy). Las cifras
strict van a `docs/benchmark-report-strict-texto.html`.

## Trazabilidad

- Astra legacy:
  `bench/pipelines/pipeline_v4 - fork/main/output/all_256_clean/juanjo_classic_v2/gpt_6_astra_low_translated_en/20260908232755/`
- Astra strict: `outputs/judge_audit/all256_gpt6astra_low_strict/`
- Mini y Terra:
  [2026-08-31-all256-judge-audit-strict-mini-terra.md](2026-08-31-all256-judge-audit-strict-mini-terra.md)
- gemini-3-pro, Sol, gpt-4o:
  [2026-09-08-all256-judge-audit-strict-gemini3pro-sol-gpt4o.md](2026-09-08-all256-judge-audit-strict-gemini3pro-sol-gpt4o.md)
