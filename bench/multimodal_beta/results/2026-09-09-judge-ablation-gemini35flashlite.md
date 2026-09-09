# Ablación del juez — gemini-3.5-flash-lite vs David

Mismas 100 T+I gpt5, mismo `labeled_input.json`, prompt `strict_equivalence`.
Gold: ronda 2 de David, 35 ids (`24910386` fuera). El slug `gemini-2.5-flash-lite`
está retirado; este es el sustituto válido.

## Acuerdo (match sí/no vs David)

| Juez | Acuerdo | Cobertura 100 | vs David |
|---|---:|---:|---|
| gemini-2.5-pro | 30/35 (85,7%) | 80 | referencia |
| gemini-2.5-flash | 31/35 (88,6%) | 85 | más laxo |
| gpt-5.4-mini | 30/35 (85,7%) | 78 | más estricto |
| gemini-3.5-flash-lite | 28/35 (80,0%) | 75 | más estricto y peor |

Sigue fallando 2 de los 3 FN de Pro (`27656661`, `19721837`). Recupera
`26819809` (no aparece en desacuerdos). Sigue el FP `22563559`. Rechaza
4 matches que David marcó `correcto`: `27709474`, `N-10000086`,
`25336332`, `25282086`.

Más barato que Pro, peor árbitro. No sustituye.

## Trazabilidad

- Lite: `outputs/judge_audit/pilot100_ti_gemini35flashlite/`
- 2.5-flash-lite (404, inválido): [2026-09-09-judge-ablation-gemini25flashlite.md](2026-09-09-judge-ablation-gemini25flashlite.md)
