# MedReaMM pilot100 — I con gpt5

Estado: **provisional; evaluación estricta completada**.

## Condiciones

- Fecha: 2026-08-28.
- Casos: los mismos 100 de las condiciones anteriores.
- Entrada: únicamente las imágenes correctas.
- Texto y documentos: eliminados.
- Tenant: `dxgpt-local`.
- Modelo forzado: `gpt5`.
- Objetivo: medir cuánta señal diagnóstica contienen las imágenes sin historia.

Este control no representa el uso recomendado del producto.

## Resultado técnico

- Respuestas completadas: 100/100.
- Modelo final: `gpt5` en 100/100.
- Casos resumidos: 0/100 (no hay texto que resumir).
- Latencia media: 34,5 segundos.
- Mediana: 33,6 segundos.
- Diferencial: 6 diagnósticos en 17 casos, 5 en 70, 4 en 11, 3 en 1 y lista
  vacía en 1 (`23613701`).

## Resultado strict_equivalence

- R@1: 32/100 — 32%.
- R@3: 42/100 — 42%.
- R@5: 49/100 — 49%.
- Cobertura: 50/100 — 50%.
- Posición media entre matches: 1,860.
- MRR: 0,380.

Resolución: 32 SNOMED, 2 ICD-10 exactos, 1 ICD-10 sibling, 3 BERT
autoconfirmados, 1 BERT contrastado y 11 decisiones del juez LLM.

## Comparación emparejada con T

Manteniendo los mismos 100 casos, modelo y evaluador:

- cobertura `I`: 50%;
- cobertura `T`: 64%;
- match solo con `I`: 15;
- match solo con `T`: 29;
- McNemar exacto sobre discordantes: `p=0,049`.

Las imágenes solas no son ruido: aciertan la mitad de los golds. Tampoco
sustituyen a la historia. El producto necesita ambas, y las imágenes tienen
que ser las del mismo caso.

## Trazabilidad

- Manifest: `datasets/processed/medreamm_pilot100/manifest.yaml`.
- Respuestas: `outputs/pilot100_gpt5_I/responses.jsonl`.
- Evaluación: `outputs/pilot100_gpt5_I/evaluation_v4_primary_strict/`.
- Revisión clínica:
  `outputs/pilot100_gpt5_I/evaluation_v4_primary_strict/clinical_review.md`.
