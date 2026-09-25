# MedReaMM pilot100 — T+I con gpt56terra, sin la frase de imagen

Estado: **provisional; evaluación estricta completada**. Es el número de
producto actual: la frase de imagen ya no se inyecta. El brazo del 8 sep
([2026-09-08-medreamm-pilot100-t-plus-i-gpt56terra.md](2026-09-08-medreamm-pilot100-t-plus-i-gpt56terra.md))
llevaba esa frase en los 100 casos.

## Condiciones

- Fecha: 2026-09-24.
- Casos: los mismos 100 de MedReaMM pilot100.
- Entrada: historia saneada e imágenes del mismo caso (`T+I`).
- Tenant: `dxgpt-local`.
- Modelo: `gpt56terra` (`gpt-5.6-terra` low) en 100/100.
- Frase de imagen: no se añade al prompt.

## Resultado técnico

- Respuestas: 100/100. Dos listas vacías (`20052363`, `32340587`).
- Resumidos por superar 1.000 caracteres: 32/100.
- Latencia media: 29,4 s.
- Diferencial: 6 diagnósticos en 2 casos, 5 en 39, 4 en 44 y 3 en 13.

## Resultado strict_equivalence

- R@1: 65/100 — 65%.
- R@3: 74/100 — 74%.
- R@5: 79/100 — 79%.
- Cobertura: 79/100 — 79%.
- Posición media entre matches: 1,367.
- MRR: 0,702.

Resolución: 54 SNOMED, 1 ICD-10 exacto, 1 ICD-10 parent, 1 ICD-10 sibling,
6 BERT autoconfirmados, 6 BERT contrastados y 10 decisiones del juez LLM.

Casos sin match:

- `24174966`: Primary cardiac angiofibroma.
- `25995698`: Extralobar pulmonary sequestration.
- `27656661`: Multiple sclerosis-like disorder.
- `30687305`: Refractory cytopenias with multilineage dysplasia.
- `case-4402`: Acute acalculous cholecystitis.
- `26819809`: Malignant gastrointestinal stromal tumor.
- `23482507`: Cavernous hemangioma of bone.
- `24910386`: Ischaemic scalp lesions.
- `N-10000050`: Cryptococcal pneumonia.
- `19721837`: Acute hypereosinophilic syndrome.
- `25336332`: Squamous cell carcinoma of tonsil.
- `28706431`: Primary pancreatic T-cell/histiocyte-rich large B-cell lymphoma.
- `20052363`: Lymphangiomatosis of the colon (lista vacía).
- `26958738`: Meningoencephalitis.
- `27332906`: Iododerma.
- `27709474`: Phosphaturic mesenchymal tumor.
- `28104685`: Bicondylar tibial plateau fracture.
- `28302624`: Intervertebral disc prolapse.
- `32340587`: Clear cell renal cell carcinoma (lista vacía).
- `N-10000083`: Intralobar bronchopulmonary sequestration.
- `N-10000086`: BRAF inhibitor-related toxic effects.

## Frente al T+I Terra con frase (8 sep, mismos 100, mismo juez)

| Condición | R@1 | R@3 | R@5 | Cobertura | Pos. media | Latencia |
|---|---:|---:|---:|---:|---:|---:|
| Con frase (8 sep) | 67% | 82% | 84% | 84% | 1,310 | 24,3 s |
| Sin frase (24 sep) | 65% | 74% | 79% | 79% | 1,367 | 29,4 s |

McNemar cobertura: 9 solo con frase, 4 solo sin frase, `p=0,27`.
R@1: 9 vs 7, `p=0,80`. La caída de cobertura no es significativa; dos de
los nueve casos perdidos salieron con lista vacía.

## Frente a gpt5 T+I (aún con frase) y a Terra T

Cobertura 79% vs gpt5 T+I 80% (`p=1,0`). R@1 65% vs 61% (`p=0,45`).

Terra T 65% → T+I sin frase 79%: 21 solo T+I, 7 solo T, `p=0,012`.
Sigue usando la imagen.

## Trazabilidad

- Manifest: `datasets/processed/medreamm_pilot100/manifest.yaml`.
- Respuestas: `outputs/pilot100_gpt56terra_TI_nophase/responses.jsonl`.
- Evaluación: `outputs/pilot100_gpt56terra_TI_nophase/evaluation_v4_primary_strict/`.
- Baseline con frase: [2026-09-08-medreamm-pilot100-t-plus-i-gpt56terra.md](2026-09-08-medreamm-pilot100-t-plus-i-gpt56terra.md).
