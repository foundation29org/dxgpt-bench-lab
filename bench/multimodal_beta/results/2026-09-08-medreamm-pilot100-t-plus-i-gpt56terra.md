# MedReaMM pilot100 — T+I con gpt56terra

Estado: **provisional**. Misma cohorte, texto, imágenes, gold y juez
`strict_equivalence` que el T+I de `gpt5`. Solo cambia el modelo
diagnóstico (override de eval, tenant `dxgpt-local`).

## Condiciones y resultado técnico

- Fecha: 2026-09-08.
- Casos: 100 (`medreamm_pilot100`).
- Entrada: historia saneada e imágenes del mismo caso (`T+I`).
- Tenant: `dxgpt-local`.
- Modelo pedido y final: `gpt56terra` en 100/100 (`gpt-5.6-terra`, WestUS).
- Peticiones completadas: 100/100, sin listas vacías.
- Tres HTTP 429; se reintentaron y acabaron en éxito.
- Resumidos por superar 1.000 caracteres: 32/100 (los mismos umbrales
  de producto).
- Latencia media: 24,3 s. Mediana: 23,5 s. P95: 32,9 s. Rango: 15,2–41,4 s.
- Diferencial: 3 diagnósticos en 28 casos, 4 en 47, 5 en 24 y 6 en 1.

## Resultado strict_equivalence

- R@1: 67/100 — 67%.
- R@3: 82/100 — 82%.
- R@5: 84/100 — 84%.
- Cobertura: 84/100 — 84%.
- Posición media entre matches: 1,310.
- MRR: 0,742.

Resolución: 55 SNOMED, 1 ICD-10 exacto, 1 ICD-10 parent, 1 ICD-10 sibling,
8 BERT autoconfirmados, 3 BERT contrastados y 15 decisiones del juez LLM.

Casos sin match:

- `24174966`: Primary cardiac angiofibroma.
- `25995698`: Extralobar pulmonary sequestration.
- `27656661`: Multiple sclerosis-like disorder.
- `30687305`: Refractory cytopenias with multilineage dysplasia.
- `23509306`: Nodular sclerosis classical Hodgkin lymphoma.
- `case-4402`: Acute acalculous cholecystitis.
- `case0-15940`: Cholecystocolonic fistula.
- `26819809`: Malignant gastrointestinal stromal tumor.
- `23482507`: Cavernous hemangioma of bone.
- `24910386`: Ischaemic scalp lesions.
- `N-10000050`: Cryptococcal pneumonia.
- `24552323`: Congenital babesiosis.
- `19721837`: Acute hypereosinophilic syndrome.
- `25336332`: Squamous cell carcinoma of tonsil.
- `28620010`: Right femoral neck fracture.
- `28706431`: Primary pancreatic T-cell/histiocyte-rich large B-cell lymphoma.

## Frente a gpt5 T+I (mismos 100 casos, mismo juez)

| Modelo | R@1 | R@3 | R@5 | Cobertura | Pos. media | Latencia media |
|---|---:|---:|---:|---:|---:|---:|
| gpt5 | 61% | 74% | 78% | 80% | 1,462 | 40,2 s |
| gpt56terra | 67% | 82% | 84% | 84% | 1,310 | 24,3 s |

Emparejado por cobertura: ambos 74, solo Terra 10, solo gpt5 6, ninguno 10.
McNemar exacto sobre discordantes: `p≈0,45`. Terra apunta mejor y es más
rápido; la diferencia de cobertura **no** es significativa con n=100.

Terra recupera 10 rechazos de gpt5, entre ellos Hodgkin de celularidad
mixta (`27074070`, P2), iododerma (`27332906`, P1), CCR (`32340587`, P1),
torus palatinus (`23574122`, P1) y adenocarcinoma de próstata (`23752113`,
P1). gpt5 gana 6 que Terra pierde, entre ellos hemangioma óseo
(`23482507`, P1 en gpt5) y carcinoma escamoso de amígdala (`25336332`, P1
en gpt5).

## Trazabilidad y cautelas

- Manifest: `datasets/processed/medreamm_pilot100/manifest.yaml`.
- Respuestas: `outputs/pilot100_gpt56terra_TI/responses.jsonl`.
- Strict: `outputs/pilot100_gpt56terra_TI/evaluation_v4_primary_strict/`.
- Terra `T` ya está medido: cobertura 65%, R@1 50%. T+I gana 19 puntos de
  cobertura (24 vs 5; McNemar `p=0,00055`). Terra usa la imagen.
  Informe: [2026-09-08-medreamm-pilot100-t-gpt56terra.md](2026-09-08-medreamm-pilot100-t-gpt56terra.md).
  No se ha corrido shuffled.
- El juez sigue siendo `gemini-2.5-pro` + `strict_equivalence`.
  Provisional hasta la ronda 2 de David.
