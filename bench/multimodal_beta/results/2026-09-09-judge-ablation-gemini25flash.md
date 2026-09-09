# Ablación del juez — gemini-2.5-flash vs David (ronda 2)

Mismas 100 T+I gpt5, mismo `labeled_input.json`. Solo cambia el modelo del
paso LLM. `24910386` fuera (etiqueta inválida).

## Acuerdo con David (35 ids)

| Juez | Acuerdo | Cobertura 100 |
|---|---:|---:|
| gemini-2.5-pro | 30/35 (85,7%) | 80/100 |
| gemini-2.5-flash | 31/35 (88,6%) | 85/100 |

Flash **recupera los 3 FN** de Pro (`27656661`, `26819809`, `19721837`).
Sigue aceptando los 2 FP (`27068836`, `22563559`). Añade 2 matches que
David dejó en 0: `24054536` (gold fenotípico) y `28620010` (fractura
unilateral vs bilateral).

Más de acuerdo con David por ser más laxo, no más estricto. No sustituir
a Pro todavía; esperar mini.

## Trazabilidad

- Baseline: `outputs/pilot100_product/evaluation_v4_primary_strict/`
- Flash: `outputs/judge_audit/pilot100_ti_gemini25flash/`
