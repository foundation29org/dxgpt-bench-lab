# MedReaMM pilot250 — T+I con gpt56terra, sin la frase de imagen

Estado: **provisional; evaluación estricta completada**. Brazo emparejado
del mismo día: [2026-09-24-medreamm-pilot250-t-plus-i-gpt56terra-phrase.md](2026-09-24-medreamm-pilot250-t-plus-i-gpt56terra-phrase.md).
Los 100 de `medreamm_pilot100` van anidados (mismo seed `20260727`).

## Condiciones

- Fecha: 2026-09-24.
- Casos: 250. Elegibles 385 / 625. Rechazados por fuga o historia corta: 240.
- Entrada: historia e imágenes del mismo caso (`T+I`).
- Tenant: `dxgpt-local`.
- Modelo: `gpt56terra` (`gpt-5.6-terra` low) en 250/250.
- Frase de imagen: no se añade al prompt.

## Resultado técnico

- Respuestas: 250/250. Tres listas vacías (`20052363`, `32340587`, `28232322`).
- Resumidos por superar 1.000 caracteres: 77/250.
- Latencia media: 30,0 s.
- Diferencial: 5 diagnósticos en 106 casos, 4 en 104 y 3 en 37.

## Resultado strict_equivalence

- R@1: 147/250 — 58,8%.
- R@3: 180/250 — 72,0%.
- R@5: 191/250 — 76,4%.
- Cobertura: 191/250 — 76,4%.
- Posición media entre matches: 1,424.
- MRR: 0,655.

Resolución: 117 SNOMED, 3 ICD-10 exactos, 2 parent, 4 sibling, 19 BERT
autoconfirmados, 14 BERT contrastados y 32 decisiones del juez LLM.

Los 100 anidados: R@1 65%, R@3 75%, R@5 80%, cobertura 80%. El tramo
nuevo (150) es más difícil; no se puede comparar 58,8% con el 65% de n=100
como si fuera el mismo examen.

## Frente al brazo con frase (mismo día)

| Condición | R@1 | R@3 | R@5 | Cobertura | MRR |
|---|---:|---:|---:|---:|---:|
| Sin frase | 58,8% | 72,0% | 76,4% | 76,4% | 0,655 |
| Con frase | 60,8% | 73,6% | 77,6% | 78,0% | 0,674 |

McNemar n=250: cobertura 12 vs 16, `p=0,57`. R@1 16 vs 21, `p=0,51`.
En los 100 anidados, cobertura 80% = 80% y R@1 65% vs 66% (`p=1,0`).
Las tres listas vacías son las mismas. La frase no cambia T+I.

## Trazabilidad

- Manifest: `datasets/processed/medreamm_pilot250/manifest.yaml`.
- Respuestas: `outputs/pilot250_gpt56terra_TI_nophase/responses.jsonl`.
- Evaluación: `outputs/pilot250_gpt56terra_TI_nophase/evaluation_v4_primary_strict/`.
