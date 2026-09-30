# MedReaMM pilot250 — T+I con gpt56terra, frase de imagen neutra

Estado: **provisional; evaluación estricta completada**. Brazos del 24 de
septiembre: [sin frase](2026-09-24-medreamm-pilot250-t-plus-i-gpt56terra-nophase.md)
y [con la frase anterior](2026-09-24-medreamm-pilot250-t-plus-i-gpt56terra-phrase.md).

## Condiciones

- Fecha: 2026-09-29. Mismos 250 casos y mismo tenant `dxgpt-local`.
- Modelo: `gpt56terra` en 250/250.
- Frase, solo en el prompt de diagnóstico cuando hay texto e imágenes:
  `Interpret the attached medical images together with the clinical description above; use evidence from both.`
- La frase anterior era
  `Patient with medical imaging findings that require diagnostic interpretation`.

## Resultado técnico

- Respuestas: 250/250. Tres listas vacías, las mismas que el 24 de septiembre
  (`20052363`, `32340587`, `28232322`).
- Resumidos: 77/250.
- Latencia media: 32,7 s.

## Resultado strict_equivalence

- R@1: 146/250 — 58,4%.
- R@3: 180/250 — 72,0%.
- R@5: 190/250 — 76,0%.
- Cobertura: 190/250 — 76,0%.
- Posición media entre matches: 1,437.
- MRR: 0,651.

Resolución: 114 SNOMED, 5 ICD-10 exactos, 2 parent, 1 sibling, 13 BERT
autoconfirmados, 19 BERT contrastados y 36 decisiones del juez LLM.

Los 100 anidados: R@1 63%, R@3 73%, R@5 77%, cobertura 77%.

## Frente a los brazos del 24 de septiembre

| Condición | R@1 | R@3 | R@5 | Cobertura | MRR |
|---|---:|---:|---:|---:|---:|
| Sin frase | 58,8% | 72,0% | 76,4% | 76,4% | 0,655 |
| Frase anterior | 60,8% | 73,6% | 77,6% | 78,0% | 0,674 |
| Frase neutra | 58,4% | 72,0% | 76,0% | 76,0% | 0,651 |

McNemar n=250, frase neutra frente a sin frase: cobertura 16 vs 17, `p=1,0`.
R@1 22 vs 23, `p=1,0`. Frente a la frase anterior: cobertura 12 vs 17,
`p=0,46`. R@1 17 vs 23, `p=0,43`.

En los 100 anidados, frente a sin frase: cobertura 4 vs 7, `p=0,55`; R@1
4 vs 6, `p=0,75`. Frente a la frase anterior: cobertura 4 vs 7, `p=0,55`;
R@1 5 vs 8, `p=0,58`.

La frase neutra no mejora T+I. La anterior sigue por delante en las cifras,
sin que la diferencia sea significativa. Para producción se mantiene la
frase anterior.

## Trazabilidad

- Respuestas: `outputs/pilot250_gpt56terra_TI_neutral/responses.jsonl`.
- Evaluación: `outputs/pilot250_gpt56terra_TI_neutral/evaluation_v4_primary_strict/`.
