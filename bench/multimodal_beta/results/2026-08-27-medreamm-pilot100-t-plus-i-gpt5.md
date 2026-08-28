# MedReaMM pilot100 — T+I con gpt5

Estado: **provisional; pendiente de revisión médico-técnica**.

## Condiciones y resultado técnico

- Fecha: 2026-08-27.
- Casos: 100; incluye el piloto inicial y 75 casos adicionales.
- Entrada: historia clínica saneada e imágenes correspondientes.
- Tenant: `dxgpt-local`.
- Modelo: `gpt5` en 100/100 casos.
- Peticiones completadas: 100/100, sin errores.
- Resumidos por superar 1.000 caracteres: 32/100.
- Latencia media: 40,2 segundos.
- Mediana: 39,6 segundos.
- Percentil 95: 51,6 segundos.
- Rango: 28,2–82,1 segundos.
- Diferencial: 4 diagnósticos en 1 caso, 5 en 52, 6 en 43, 7 en 2 y 8 en
  2.

## Resultado strict_equivalence

- R@1: 61/100 — 61%.
- R@3: 74/100 — 74%.
- R@5: 78/100 — 78%.
- Cobertura: 80/100 — 80%.
- Matches en P6: 2.
- Posición media entre matches: 1,462.
- MRR: 0,685.

Resolución: 48 SNOMED, 1 ICD-10 exacto, 1 ICD-10 parent, 1 ICD-10 sibling, 7
BERT autoconfirmados, 6 BERT contrastados y 16 decisiones del juez LLM.

Casos sin match:

- `24174966`: Primary cardiac angiofibroma.
- `25995698`: Extralobar pulmonary sequestration.
- `27656661`: Multiple sclerosis-like disorder.
- `30687305`: Refractory cytopenias with multilineage dysplasia.
- `27074070`: Mixed-cellularity subtype of classic Hodgkin's lymphoma.
- `24054536`: Peripheral air embolism.
- `29748223`: Oesophageal cancer.
- `27332906`: Iododerma.
- `32340587`: Clear cell renal cell carcinoma.
- `N-10000032`: Pancreatic ductal adenocarcinoma.
- `26819809`: Malignant gastrointestinal stromal tumor.
- `24910386`: Ischaemic scalp lesions.
- `23752113`: Prostatic adenocarcinoma.
- `N-10000050`: Cryptococcal pneumonia.
- `23574122`: Torus palatinus.
- `19721837`: Acute hypereosinophilic syndrome.
- `26958738`: Meningoencephalitis.
- `28620010`: Right femoral neck fracture.
- `28706431`: Primary pancreatic T-cell/histiocyte-rich large B-cell lymphoma.
- `28104685`: Bicondylar tibial plateau fracture.

## Puente legacy_similarity

Reutilizando la misma inferencia y el mismo `labeled_input.json`:

- R@1: 72%.
- R@3: 89%.
- R@5: 96%.
- Cobertura: 99%.
- Posición media: 1,586.
- MRR: 0,820.
- Decisiones del juez LLM: 35, frente a 16 con strict.

Legacy convirtió en matches 19 de los 20 rechazos strict. Solo mantuvo como
rechazo `23574122`, con gold `Torus palatinus`. El 99% mide proximidad clínica,
no equivalencia diagnóstica.

## Análisis

Los primeros 25 casos se infirieron de nuevo:

- ejecución original: 21/25 matches y R@1 16/25;
- repetición incluida aquí: 20/25 matches y R@1 15/25;
- 75 casos nuevos: 60/75 matches y R@1 46/75.

La variación de un caso aconseja no interpretar diferencias pequeñas a partir
de una única inferencia.

Por resumen:

- resumidos: 30/32 matches, R@1 21/32 y R@5 29/32;
- no resumidos: 50/68 matches, R@1 40/68 y R@5 49/68.

La asociación no es causal: los grupos difieren en longitud y tipo de caso.
Hace falta una ablación emparejada.

El intervalo Wilson del 95% para la cobertura es aproximadamente 71–87%,
frente a 65–94% en el piloto de 25. La diferencia entre 84% y 80% no demuestra
un empeoramiento.

## Trazabilidad y cautelas

- Manifest: `datasets/processed/medreamm_pilot100/manifest.yaml`.
- Respuestas: `outputs/pilot100_product/responses.jsonl`.
- Strict: `outputs/pilot100_product/evaluation_v4_primary_strict/`.
- Legacy: `outputs/pilot100_product/evaluation_v4_primary_legacy/`.
- Revisión clínica: [../MEDICAL_REVIEW.md](../MEDICAL_REVIEW.md).

Falta revisar fuga, calidad del gold, los 16 matches del juez y los rechazos
clínicamente próximos. Sigue pendiente la comparación emparejada `T` frente a
`T+I`.
