# MedReaMM pilot100 — I con gpt56terra, sin la frase de imagen

Estado: **provisional; evaluación estricta completada**. Brazo emparejado
con frase: [2026-09-24-medreamm-pilot100-i-gpt56terra-phrase.md](2026-09-24-medreamm-pilot100-i-gpt56terra-phrase.md).

## Condiciones

- Fecha: 2026-09-24.
- Casos: los mismos 100 de MedReaMM pilot100.
- Entrada: solo imágenes. Texto y documentos eliminados.
- Tenant: `dxgpt-local`.
- Modelo: `gpt56terra` (`gpt-5.6-terra` low).
- `forceDiagnosis`: sí.
- Frase de imagen: no se añade al prompt.

## Resultado técnico

- Respuestas: 100/100, `gpt56terra` en todos.
- Latencia media: 25,2 s. Mediana: 22,7 s.
- Diferencial: 5 diagnósticos en 23 casos, 4 en 54 y 3 en 23. Ninguna lista vacía.

## Resultado strict_equivalence

- R@1: 35/100 — 35%.
- R@3: 42/100 — 42%.
- R@5: 46/100 — 46%.
- Cobertura: 46/100 — 46%.
- Posición media entre matches: 1,543.
- MRR: 0,389.

Resolución: 25 SNOMED, 1 ICD-10 exacto, 1 ICD-10 sibling, 3 BERT
autoconfirmados, 4 BERT contrastados y 12 decisiones del juez LLM.

Mismo R@1 que el I-only de `gpt5` sin frase (35%). Cobertura un poco más baja
(46% frente a 51%). Frente al brazo Terra con frase del mismo día: R@1 35%
frente a 27%, cobertura 46% frente a 42%.

## Trazabilidad

- Manifest: `datasets/processed/medreamm_pilot100/manifest.yaml`.
- Respuestas: `outputs/pilot100_gpt56terra_I_nophase/responses.jsonl`.
- Evaluación: `outputs/pilot100_gpt56terra_I_nophase/evaluation_v4_primary_strict/`.
