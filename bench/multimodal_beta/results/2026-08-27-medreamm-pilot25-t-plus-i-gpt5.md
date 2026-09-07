# MedReaMM pilot25 — T+I con gpt5

Estado: **provisional; pendiente de revisión médico-técnica**.

## Condiciones

- Fecha: 2026-08-27.
- Casos: 25.
- Entrada: historia clínica saneada e imágenes correspondientes.
- Endpoint: `POST http://localhost:8443/api/medical/analyze`.
- Tenant: `dxgpt-local`.
- Modelo solicitado y utilizado: `gpt5`.
- Captions: excluidas.
- Gold: diagnóstico primario, con ontología ICD-11 de origen.
- Resumen: umbral de producto de 1.000 caracteres; 9/25 resumidos.
- Evaluador: SNOMED, ICD-10, SapBERT y `gemini-2.5-pro`.

## Resultado técnico

- Peticiones completadas: 25/25.
- Errores: 0.
- Latencia media: aproximadamente 41 segundos.

## Resultado strict_equivalence

- R@1: 16/25 — 64%.
- R@3: 19/25 — 76%.
- R@5: 21/25 — 84%.
- Cobertura: 21/25 — 84%.
- Posición media entre matches: 1,571.

Resolución: 13 SNOMED, 1 ICD-10 exacto, 2 BERT autoconfirmados, 2 BERT
contrastados y 3 decisiones del juez LLM.

Casos sin match:

- `24174966`: Primary cardiac angiofibroma.
- `27656661`: Multiple sclerosis-like disorder.
- `30687305`: Refractory cytopenias with multilineage dysplasia.
- `27074070`: Mixed-cellularity subtype of classic Hodgkin's lymphoma.

## Puente legacy_similarity

Sobre las mismas respuestas:

- R@1: 18/25 — 72%.
- R@3: 22/25 — 88%.
- R@5 y cobertura: 25/25 — 100%.
- Posición media: 1,720.

Legacy aceptó como similares los cuatro rechazos strict:

- angiofibroma cardiaco → hemangioma cavernoso cardiaco, P1;
- trastorno similar a esclerosis múltiple → MOGAD, P5;
- citopenias refractarias → neoplasia con eosinofilia o leucemia eosinofílica,
  P1;
- Hodgkin clásico de celularidad mixta → Burkitt, P1.

Las respuestas de `gpt5` eran idénticas. Solo cambió la política del juez.

## Trazabilidad

- Manifest: `datasets/processed/medreamm_pilot25/manifest.yaml`.
- Respuestas: `outputs/pilot25_product/responses.jsonl`.
- Strict: `outputs/pilot25_product/evaluation_v4_primary_strict/`.
- Legacy: `outputs/pilot25_product/evaluation_v4_primary/`.
- Revisión clínica: [../MEDICAL_REVIEW.md](../MEDICAL_REVIEW.md).

## Cautelas

- Falta revisión manual de fuga y adjudicación de los siete casos del juez.
- Algunos golds pueden ser amplios, fenotípicos o morfológicos.
- `22389885` puede obtener un match SNOMED demasiado permisivo por su gold
  compuesto DLBCL/Burkitt.
- Esta ejecución por sí sola no demuestra aportación de las imágenes.
