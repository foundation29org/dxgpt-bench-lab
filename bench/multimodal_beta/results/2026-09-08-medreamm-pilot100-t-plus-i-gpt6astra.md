# MedReaMM pilot100 — T+I con gpt6astra

Estado: **provisional**. Misma cohorte, texto, imágenes, gold y juez
`strict_equivalence` que gpt5 y Terra T+I. Solo cambia el modelo
diagnóstico (override de eval, tenant `dxgpt-local`).

## Condiciones y resultado técnico

- Fecha: 2026-09-08.
- Casos: 100 (`medreamm_pilot100`).
- Entrada: historia saneada e imágenes del mismo caso (`T+I`).
- Tenant: `dxgpt-local`.
- Modelo pedido y final: `gpt6astra` en 100/100 (`gpt-6-astra`, WestUS).
- Peticiones completadas: 100/100, sin listas vacías. Todas con ≥1 imagen.
- Resumidos por superar 1.000 caracteres: 32/100.
- Latencia media: 55,1 s. Mediana: 55,3 s. P95: 71,5 s. Rango: 26,6–76,4 s.
- Diferencial: 1 diagnóstico en 3 casos, 3 en 18, 4 en 27 y 5 en 52.

La corrida se partió por el rate limiter interno (100/15 min por IP de
Docker) y se reanudó tras desactivarlo en `NODE_ENV=local`.

## Resultado strict_equivalence

- R@1: 76/100 — 76%.
- R@3: 87/100 — 87%.
- R@5: 88/100 — 88%.
- Cobertura: 88/100 — 88%.
- Posición media entre matches: 1,205.
- MRR: 0,811.

Resolución: 58 SNOMED, 1 ICD-10 exacto, 1 ICD-10 sibling, 7 BERT
autoconfirmados, 7 BERT contrastados y 14 decisiones del juez LLM.

Casos sin match:

- `24174966`: Primary cardiac angiofibroma.
- `27656661`: Multiple sclerosis-like disorder.
- `30687305`: Refractory cytopenias with multilineage dysplasia.
- `N-10000083`: Intralobar bronchopulmonary sequestration.
- `34134621`: Infective endocarditis.
- `24054536`: Peripheral air embolism.
- `29748223`: Oesophageal cancer.
- `26819809`: Malignant gastrointestinal stromal tumor.
- `23482507`: Cavernous hemangioma of bone.
- `24910386`: Ischaemic scalp lesions.
- `19721837`: Acute hypereosinophilic syndrome.
- `28104685`: Bicondylar tibial plateau fracture.

## Frente a gpt5 y Terra T+I (mismos 100, mismo juez)

| Modelo | R@1 | R@3 | R@5 | Cobertura | Pos. media | Latencia media |
|---|---:|---:|---:|---:|---:|---:|
| gpt5 | 61% | 74% | 78% | 80% | 1,462 | 40,2 s |
| gpt56terra | 67% | 82% | 84% | 84% | 1,310 | 24,3 s |
| gpt6astra | 76% | 87% | 88% | 88% | 1,205 | 55,1 s |

Cobertura emparejada Astra vs gpt5: ambos 77, solo Astra 11, solo gpt5 3,
ninguno 9. McNemar `p=0,057`. R@1: 21 solo Astra vs 6 solo gpt5,
`p=0,0059`.

Cobertura Astra vs Terra: ambos 79, solo Astra 9, solo Terra 5, ninguno 7.
McNemar `p=0,42`. R@1: 17 vs 8, `p=0,11`.

Astra gana de forma clara el **R@1 frente a gpt5**. La cobertura +8 pp no
llega a 0,05. Frente a Terra ni cobertura ni R@1 son significativos; Astra
es más lento (~2× Terra) y más caro.

Astra recupera, entre otros, torus palatinus (`23574122`, P1), iododerma
(`27332906`, P1), CCR (`32340587`, P1) y Hodgkin de celularidad mixta
(`27074070`, P1) que gpt5 rechazó. gpt5 gana 3, entre ellos hemangioma
óseo (`23482507`, P1).

## Trazabilidad y cautelas

- Manifest: `datasets/processed/medreamm_pilot100/manifest.yaml`.
- Respuestas: `outputs/pilot100_gpt6astra_TI/responses.jsonl`.
- Strict: `outputs/pilot100_gpt6astra_TI/evaluation_v4_primary_strict/`.
- No se ha corrido Astra shuffled. Astra `T` ya está: cobertura 67%,
  R@1 54%. T+I gana 21 puntos (22 vs 1; McNemar `p=0,00001`). Astra usa
  la imagen. Informe:
  [2026-09-08-medreamm-pilot100-t-gpt6astra.md](2026-09-08-medreamm-pilot100-t-gpt6astra.md).
- No enviar a David los unmatched de Astra: su ronda 2 calibra el juez
  sobre gpt5.
- El juez sigue siendo `gemini-2.5-pro` + `strict_equivalence`.
