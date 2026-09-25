# MedReaMM pilot100 — I con gpt56terra, con la frase de imagen

Estado: **provisional; evaluación estricta completada**. Brazo emparejado
de [2026-09-24-medreamm-pilot100-i-gpt56terra-nophase.md](2026-09-24-medreamm-pilot100-i-gpt56terra-nophase.md).

## Condiciones

- Fecha: 2026-09-24.
- Casos: los mismos 100, mismo día, mismo código, mismo juez.
- Entrada: solo imágenes. `forceDiagnosis`: sí.
- Modelo: `gpt56terra` (`gpt-5.6-terra` low).
- Frase de imagen: sí se añade al prompt (`withImageContext`).

## Resultado técnico

- Respuestas: 100/100.
- Latencia media: 24,2 s. Mediana: 22,2 s.
- Diferencial: 5 diagnósticos en 14 casos, 4 en 45 y 3 en 41.

## Resultado strict_equivalence

- R@1: 27/100 — 27%.
- R@3: 40/100 — 40%.
- R@5: 42/100 — 42%.
- Cobertura: 42/100 — 42%.
- Posición media entre matches: 1,524.
- MRR: 0,335.

Resolución: 23 SNOMED, 1 ICD-10 exacto, 2 ICD-10 sibling, 6 BERT
autoconfirmados, 1 BERT contrastado y 9 decisiones del juez LLM.

## Comparación emparejada: sin frase vs con frase (Terra)

| Métrica | Sin frase | Con frase |
|---|---:|---:|
| R@1 | 35% | 27% |
| R@3 | 42% | 40% |
| R@5 | 46% | 42% |
| Cobertura | 46% | 42% |
| Pos. media | 1,543 | 1,524 |
| MRR | 0,389 | 0,335 |

McNemar exacto sobre cobertura: 12 solo sin frase, 8 solo con frase,
20 discordantes, `p=0,50`. Sobre R@1: 13 solo sin frase, 5 solo con frase,
`p=0,096`.

La frase no aporta señal. En Terra mueve el R@1 8 puntos hacia abajo;
el contraste no llega a p<0,05, pero va en la misma dirección que gpt5
(32% con frase → 35% sin frase).

## Trazabilidad

- Respuestas: `outputs/pilot100_gpt56terra_I_phrase/responses.jsonl`.
- Evaluación: `outputs/pilot100_gpt56terra_I_phrase/evaluation_v4_primary_strict/`.
