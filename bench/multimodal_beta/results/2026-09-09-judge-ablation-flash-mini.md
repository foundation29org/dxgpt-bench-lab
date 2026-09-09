# Ablación del juez — Flash y gpt-5.4-mini vs David

Mismas 100 T+I gpt5, mismo `labeled_input.json`, prompt `strict_equivalence`.
Gold: ronda 2 de David, 35 ids (`24910386` fuera).

## Acuerdo (match sí/no vs David)

| Juez | Acuerdo | Cobertura 100 | vs David |
|---|---:|---:|---|
| gemini-2.5-pro | 30/35 (85,7%) | 80 | referencia |
| gemini-2.5-flash | 31/35 (88,6%) | 85 | más laxo |
| gpt-5.4-mini | 30/35 (85,7%) | 78 | más estricto |

Flash gana un punto recuperando los 3 FN de Pro, pero acepta 2 casos que
David dejó en 0 y sigue con los 2 FP.

Mini empata el recuento de Pro en **otros** casos: rechaza el FP
`27068836` y acierta el FN `26819809`, pero tira dos matches que David
marcó `correcto` (`21424749`, `27709474`) y sigue con `22563559`.

Ninguno sustituye a Pro. Flash no vale como árbitro más barato si el
criterio es “mismos errores que David/Pro”. Mini tampoco: misma nota,
sitios distintos.

**Decisión:** conservar `gemini-2.5-pro` como juez de evaluación.

## Trazabilidad

- Pro: `outputs/pilot100_product/evaluation_v4_primary_strict/`
- Flash: `outputs/judge_audit/pilot100_ti_gemini25flash/`
- Mini: `outputs/judge_audit/pilot100_ti_gpt54mini/`
- Flash detalle: [2026-09-09-judge-ablation-gemini25flash.md](2026-09-09-judge-ablation-gemini25flash.md).
