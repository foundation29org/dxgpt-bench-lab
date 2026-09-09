# MedReaMM pilot100 — T con gpt56terra

Estado: **provisional**. Mismo modelo, historias, gold y juez
`strict_equivalence` que Terra T+I. Solo se quitan las imágenes.

## Condiciones y resultado técnico

- Fecha: 2026-09-08.
- Casos: los mismos 100 de Terra T+I.
- Entrada: historia saneada; imágenes y documentos eliminados (`T`).
- Tenant: `dxgpt-local`.
- Modelo pedido y final: `gpt56terra` en 100/100 (`gpt-5.6-terra`, WestUS).
- Peticiones completadas: 100/100. Una lista vacía (`32340587`, 2,2 s).
- Resumidos por superar 1.000 caracteres: 32/100.
- Latencia media: 20,1 s. Mediana: 19,0 s. P95: 27,1 s. Rango: 2,2–59,6 s.
- Diferencial: 3 diagnósticos en 7 casos, 4 en 28, 5 en 63, 6 en 1 y lista
  vacía en 1.

## Resultado strict_equivalence

- R@1: 50/100 — 50%.
- R@3: 60/100 — 60%.
- R@5: 65/100 — 65%.
- Cobertura: 65/100 — 65%.
- Posición media entre matches: 1,477.
- MRR: 0,554.

Resolución: 45 SNOMED, 1 ICD-10 exacto, 1 ICD-10 parent, 1 ICD-10 sibling,
5 BERT autoconfirmados, 4 BERT contrastados y 8 decisiones del juez LLM.

## Frente a Terra T+I (mismos 100, mismo juez)

| Condición | R@1 | R@3 | R@5 | Cobertura | Pos. media | Latencia media |
|---|---:|---:|---:|---:|---:|---:|
| T | 50% | 60% | 65% | 65% | 1,477 | 20,1 s |
| T+I | 67% | 82% | 84% | 84% | 1,310 | 24,3 s |

Emparejado por cobertura: ambos 60, solo T+I 24, solo T 5, ninguno 11.
McNemar exacto sobre discordantes: `p=0,00055`. R@1: 21 solo T+I vs 4
solo T, `p=0,00091`.

Terra **usa la imagen**. La ganancia (+19 cobertura, +17 R@1) es del mismo
orden que gpt5 T → T+I (+16 / +18; `p=0,00154`). No hace falta shuffled
para afirmar que no es un artefacto de «llevar archivos»: el control es el
mismo modelo sin fotos.

T+I recupera, entre otros, torus palatinus (`23574122`, P1), iododerma
(`27332906`, P1), CCR (`32340587`, P1; T devolvió lista vacía), Hodgkin de
celularidad mixta (`27074070`, P2) y adenocarcinoma de próstata
(`23752113`, P1). T gana 5 que T+I pierde, entre ellos hipereosinofilia
aguda (`19721837`, P1 en T).

## Frente a gpt5 T (mismos 100, mismo juez)

Terra T 65% vs gpt5 T 64%. Emparejado: ambos 59, solo Terra 6, solo gpt5 5,
ninguno 30. McNemar `p≈1`. En texto solo son indistinguibles; la diferencia
entre modelos aparece con imágenes (T+I 84% vs 80%, aún no significativa).

## Trazabilidad y cautelas

- Manifest: `datasets/processed/medreamm_pilot100/manifest.yaml`.
- Respuestas: `outputs/pilot100_gpt56terra_T/responses.jsonl`.
- Strict: `outputs/pilot100_gpt56terra_T/evaluation_v4_primary_strict/`.
- No se ha corrido Terra shuffled. La comparación T vs T+I del mismo modelo
  ya basta para la pregunta de si usa la foto.
- El juez sigue siendo `gemini-2.5-pro` + `strict_equivalence`.
  Provisional hasta la ronda 2 de David (sobre gpt5, no sobre estos
  unmatched de Terra).
