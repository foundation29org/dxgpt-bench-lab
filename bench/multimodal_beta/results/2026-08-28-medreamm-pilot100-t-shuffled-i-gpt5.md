# MedReaMM pilot100 — T+shuffled-I con gpt5

Estado: **provisional; evaluación estricta completada**.

## Condiciones

- Fecha: 2026-08-28.
- Casos: los mismos 100 de `T` y `T+I`.
- Texto: historia clínica original de cada caso.
- Imágenes: pertenecen al siguiente caso de la cohorte, con rotación circular.
- Tenant: `dxgpt-local`.
- Modelo forzado: `gpt5`.
- Objetivo: comprobar si la ganancia de `T+I` depende de la imagen correcta.

Cada respuesta registra `image_source_case_id`. En 100/100 esa fuente es
distinta del `case_id`.

## Resultado técnico

- Respuestas completadas: 100/100.
- Modelo final: `gpt5` en 100/100.
- Casos resumidos: 32/100.
- Latencia media: 44,5 segundos.
- Mediana: 44,6 segundos.
- Diferencial: 8 diagnósticos en 6 casos, 7 en 8, 6 en 57 y 5 en 29.

## Resultado strict_equivalence

- R@1: 46/100 — 46%.
- R@3: 57/100 — 57%.
- R@5: 60/100 — 60%.
- Cobertura: 62/100 — 62%.
- Posición media entre matches: 1,597.
- MRR: 0,516.

Resolución: 39 SNOMED, 1 ICD-10 exacto, 1 ICD-10 parent, 3 BERT
autoconfirmados, 5 BERT contrastados y 13 decisiones del juez LLM.

## Comparación emparejada

| Condición | R@1 | R@3 | R@5 | Cobertura |
|---|---:|---:|---:|---:|
| T+I | 61% | 74% | 78% | 80% |
| T | 43% | 58% | 63% | 64% |
| T+shuffled-I | 46% | 57% | 60% | 62% |

Frente a `T+I` (mismas historias, modelo y evaluador; imágenes incorrectas):

- match solo con `T+I`: 22;
- match solo con shuffled: 4 (`19721837`, `24054536`, `26819809`, `27332906`);
- match en ambas: 58;
- sin match en ninguna: 16;
- McNemar exacto sobre discordantes: `p=0,00053`.

Frente a `T` (mismas historias; shuffled añade imágenes ajenas):

- match solo con `T`: 8;
- match solo con shuffled: 6;
- McNemar: `p=0,79`.

La ganancia de 16 puntos de `T` a `T+I` desaparece al cambiar las imágenes.
`T+shuffled-I` es estadísticamente indistinguible de `T`. El producto no
mejora por «llevar imágenes»; mejora cuando las imágenes pertenecen al mismo
caso.

## Trazabilidad

- Manifest: `datasets/processed/medreamm_pilot100/manifest.yaml`.
- Respuestas: `outputs/pilot100_gpt5_T_shuffled_I/responses.jsonl`.
- Evaluación: `outputs/pilot100_gpt5_T_shuffled_I/evaluation_v4_primary_strict/`.
- Revisión clínica:
  `outputs/pilot100_gpt5_T_shuffled_I/evaluation_v4_primary_strict/clinical_review.md`.
- Comparación ciega frente a `T+I`:
  `outputs/comparisons/pilot100_gpt5_TI_vs_TshuffledI/`.
