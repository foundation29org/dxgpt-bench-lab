# Auditoría del juez — all_256_clean, gpt-5.6-luna high

Estado: **provisional**. Mismas respuestas y códigos que el run histórico
`20260727120622`. Solo cambia el prompt del juez. `docs/benchmark-report.html`
**no se reescribe**.

## Condiciones

- Dataset: `all_256_clean`, prompt `juanjo_classic_v2`, traducción ON.
- Modelo: `gpt-5.6-luna` **high**. Run `20260727120622`.
- Juez: `gemini-2.5-pro`, `strict_equivalence`.
- Script: `reeval_traditional_strict.py`.

## Métricas

| Modelo | Juez | R@1 | R@3 | R@5 | Cobertura | Pos. media | MRR |
|---|---|---:|---:|---:|---:|---:|---:|
| Luna high | legacy | 68,8% | 90,6% | 97,3% | 97,7% | 1,564 | 0,799 |
| Luna high | strict | 60,9% | 77,3% | 82,0% | 83,6% | 1,575 | 0,693 |
| Luna low | strict | 57,0% | 73,8% | 78,5% | 79,7% | 1,554 | 0,657 |
| Sol medium | strict | 60,9% | 76,2% | 81,2% | 82,4% | 1,540 | — |

Con strict, high **gana a low** (R@1 60,9% vs 57,0%; cobertura 83,6% vs
79,7%). Empata el R@1 de Sol medium y gana cobertura. Eso **invierte** la
decisión legacy (mantener low). LLM 71→31.

No entra en el top Terra/gpt-5.4 (63,3% / 62,9%). Sigue por debajo de
gemini-3.1-pro en R@1 (61,3%), con mucha más cobertura.

## Trazabilidad

- Legacy: `.../gpt_5_6_luna_high_translated_en/20260727120622/`
- Strict: `outputs/judge_audit/all256_gpt56luna_high_strict/`
- Low: [2026-09-09-all256-judge-audit-strict-luna-low.md](2026-09-09-all256-judge-audit-strict-luna-low.md).
