# MedReaMM pilot100 — I con gpt5, sin la frase de imagen

Estado: **provisional; evaluación estricta completada**.

## Condiciones

- Fecha: 2026-09-24.
- Casos: los mismos 100 de `2026-08-28-medreamm-pilot100-i-gpt5`.
- Entrada: únicamente las imágenes correctas.
- Texto y documentos: eliminados.
- Tenant: `dxgpt-local`.
- Modelo forzado: `gpt5`.
- `forceDiagnosis`: sí. Sin esto el clasificador para en `enrich` y no hay diferencial.
- Frase "Patient with medical imaging findings that require diagnostic interpretation": **no** se añade al prompt (`DXGPT_EVAL_SKIP_IMAGE_CONTEXT=1`).

Objetivo: ver si esa frase cambia la precisión cuando solo hay imagen.

## Resultado técnico

- Respuestas completadas: 100/100.
- Modelo final: `gpt5` en 100/100.
- Casos resumidos: 0/100.
- Latencia media: 37,3 segundos.
- Mediana: 34,1 segundos.
- Diferencial: 6 diagnósticos en 9 casos, 5 en 75, 4 en 14 y 3 en 2. Ninguna lista vacía.

## Resultado strict_equivalence

- R@1: 35/100 — 35%.
- R@3: 46/100 — 46%.
- R@5: 51/100 — 51%.
- Cobertura: 51/100 — 51%.
- Posición media entre matches: 1,725.
- MRR: 0,405.

Resolución: 32 SNOMED, 1 ICD-10 exacto, 1 ICD-10 sibling, 4 BERT
autoconfirmados, 2 BERT contrastados y 11 decisiones del juez LLM.

## Comparación con I + frase (2026-08-28)

Mismos 100 casos, mismo modelo, mismo juez `gemini-2.5-pro` + `strict_equivalence`.
La ejecución de agosto metía la frase como descripción; esta no la añade.

| Métrica | Con frase (28/08) | Sin frase (24/09) |
|---|---:|---:|
| R@1 | 32% | 35% |
| R@3 | 42% | 46% |
| R@5 | 49% | 51% |
| Cobertura | 50% | 51% |
| Pos. media | 1,860 | 1,725 |
| MRR | 0,380 | 0,405 |

No hay jsonl de agosto en disco, así que no hay McNemar emparejado. La
diferencia cabe en el ruido de una repetición del mismo modelo. **La frase no
aporta señal diagnóstica medible.**

## Trazabilidad

- Manifest: `datasets/processed/medreamm_pilot100/manifest.yaml`.
- Respuestas: `outputs/pilot100_gpt5_I_nophase/responses.jsonl`.
- Evaluación: `outputs/pilot100_gpt5_I_nophase/evaluation_v4_primary_strict/`.
- Baseline: [2026-08-28-medreamm-pilot100-i-gpt5.md](2026-08-28-medreamm-pilot100-i-gpt5.md).
