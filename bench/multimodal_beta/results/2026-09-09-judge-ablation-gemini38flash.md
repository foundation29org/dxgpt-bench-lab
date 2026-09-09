# Ablación del juez — gemini-3.8-flash vs David

Mismas 100 T+I gpt5, mismo `labeled_input.json`, prompt `strict_equivalence`.
Gold: ronda 2 de David, 35 ids (`24910386` fuera). Curiosidad, no candidato
publicado. `thinking_level: low`.

## Acuerdo (match sí/no vs David)

| Juez | Acuerdo | Cobertura 100 | vs David |
|---|---:|---:|---|
| gemini-2.5-pro | 30/35 (85,7%) | 80 | referencia |
| gemini-2.5-flash | 31/35 (88,6%) | 85 | más laxo |
| gpt-5.4-mini | 30/35 (85,7%) | 78 | más estricto |
| gemini-3.8-flash | 28/35 (80,0%) | 72 | más estricto y peor |
| gemini-3.5-flash-lite | 28/35 (80,0%) | 75 | más estricto y peor |

Sigue fallando los 3 FN de Pro (`27656661`, `26819809`, `19721837`).
Sigue el FP `22563559`. Acierto extra: rechaza el FP `27068836`.
Tira 3 matches que David marcó `correcto`: `21424749`, `27709474`,
`25336332`.

LLM 12 matches (Pro ~16). El slug existe y responde; no gana a Pro ni
a Flash 2.5. No sustituye.

## Trazabilidad

- 3.8: `outputs/judge_audit/pilot100_ti_gemini38flash/`
