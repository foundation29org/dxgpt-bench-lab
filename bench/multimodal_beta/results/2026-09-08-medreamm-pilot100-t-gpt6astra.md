# MedReaMM pilot100 — T con gpt6astra

Estado: **provisional**. Mismo modelo, historias, gold y juez
`strict_equivalence` que Astra T+I. Solo se quitan las imágenes.

## Condiciones y resultado técnico

- Fecha: 2026-09-08.
- Casos: los mismos 100 de Astra T+I.
- Entrada: historia saneada; imágenes y documentos eliminados (`T`).
- Tenant: `dxgpt-local`.
- Modelo pedido y final: `gpt6astra` en 100/100 (`gpt-6-astra`, WestUS).
- Peticiones completadas: 100/100. Una lista vacía.
- Resumidos por superar 1.000 caracteres: 32/100.
- Latencia media: 47,3 s. Mediana: 48,4 s. P95: 62,3 s. Rango: 2,1–65,3 s.
- Diferencial: 1 diagnóstico en 2 casos, 3 en 3, 4 en 6, 5 en 76, 6 en 9,
  7 en 3 y lista vacía en 1.

## Resultado strict_equivalence

- R@1: 54/100 — 54%.
- R@3: 66/100 — 66%.
- R@5: 67/100 — 67%.
- Cobertura: 67/100 — 67%.
- Posición media entre matches: 1,313.
- MRR: 0,594.

Resolución: 41 SNOMED, 1 ICD-10 exacto, 1 ICD-10 parent, 1 ICD-10 sibling,
6 BERT autoconfirmados, 4 BERT contrastados y 13 decisiones del juez LLM.

## Frente a Astra T+I (mismos 100, mismo juez)

| Condición | R@1 | R@3 | R@5 | Cobertura | Pos. media | Latencia media |
|---|---:|---:|---:|---:|---:|---:|
| T | 54% | 66% | 67% | 67% | 1,313 | 47,3 s |
| T+I | 76% | 87% | 88% | 88% | 1,205 | 55,1 s |

Emparejado por cobertura: ambos 66, solo T+I 22, solo T 1, ninguno 11.
McNemar exacto: `p=0,00001`. R@1: 26 solo T+I vs 4 solo T, `p=0,00006`.

Astra **usa la imagen**. La ganancia (+21 cobertura, +22 R@1) es del mismo
orden, o mayor, que Terra T → T+I (+19 / +17). El único caso que T gana y
T+I pierde es endocarditis (`34134621`, P1 en T).

No se ha corrido shuffled. T vs T+I del mismo modelo ya responde si usa
la foto; shuffled diría si tiene que ser la foto **correcta**.

## Frente a gpt5 T y Terra T

Astra T 67% vs Terra T 65% (7 vs 5, `p=0,77`) y vs gpt5 T 64% (8 vs 5,
`p=0,58`): en cobertura de texto solo son indistinguibles. El R@1 de Astra
T vs gpt5 T sí es significativo (54% vs 43%; 13 vs 2, `p=0,007`). Parte
de la ventaja T+I de Astra frente a gpt5 ya está en el texto; el resto es
la foto.

## Trazabilidad y cautelas

- Manifest: `datasets/processed/medreamm_pilot100/manifest.yaml`.
- Respuestas: `outputs/pilot100_gpt6astra_T/responses.jsonl`.
- Strict: `outputs/pilot100_gpt6astra_T/evaluation_v4_primary_strict/`.
- El juez sigue siendo `gemini-2.5-pro` + `strict_equivalence`.
  Provisional hasta la ronda 2 de David (sobre gpt5, no sobre Astra).
