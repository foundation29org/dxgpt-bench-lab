# MedReaMM pilot250 — T+I con gpt56terra, con la frase de imagen

Estado: **provisional; evaluación estricta completada**. Brazo emparejado
del mismo día: [2026-09-24-medreamm-pilot250-t-plus-i-gpt56terra-nophase.md](2026-09-24-medreamm-pilot250-t-plus-i-gpt56terra-nophase.md).

## Condiciones

- Fecha: 2026-09-24, misma sesión que el brazo sin frase.
- Casos: los mismos 250.
- Modelo: `gpt56terra` en 250/250.
- Frase: `DXGPT_EVAL_ADD_IMAGE_CONTEXT=1` la pega al prompt de diagnóstico
  si hay imágenes. Producto sigue sin inyección.

## Resultado técnico

- Respuestas: 250/250. Tres listas vacías, las mismas que sin frase.
- Resumidos: 77/250.
- Latencia media: 30,0 s.

## Resultado strict_equivalence

- R@1: 152/250 — 60,8%.
- R@3: 184/250 — 73,6%.
- R@5: 194/250 — 77,6%.
- Cobertura: 195/250 — 78,0% (un match en P6).
- Posición media entre matches: 1,415.
- MRR: 0,674.

Resolución: 119 SNOMED, 4 ICD-10 exactos, 1 parent, 3 sibling, 18 BERT
autoconfirmados, 13 BERT contrastados y 37 decisiones del juez LLM.

Los 100 anidados: R@1 66%, R@3 76%, R@5 80%, cobertura 80%.

La diferencia frente a sin frase no es significativa. Ver el informe del
brazo sin frase para McNemar y la lectura de producto.

## Trazabilidad

- Respuestas: `outputs/pilot250_gpt56terra_TI_phrase/responses.jsonl`.
- Evaluación: `outputs/pilot250_gpt56terra_TI_phrase/evaluation_v4_primary_strict/`.
