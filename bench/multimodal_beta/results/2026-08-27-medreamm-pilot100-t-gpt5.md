# MedReaMM pilot100 — T con gpt5

Estado: **provisional; evaluación estricta completada**.

## Condiciones

- Fecha: 2026-08-27.
- Casos: los mismos 100 de `pilot100 T+I`.
- Entrada: las mismas historias; imágenes y documentos eliminados.
- Tenant: `dxgpt-local`.
- Modelo forzado: `gpt5`.
- Objetivo: aislar el valor incremental de las imágenes.

## Verificación previa

La ejecución anterior que pretendía usar `gpt5` empleó realmente `gpt54mini`
porque el contenedor no había recargado el código de override. Se conserva como
baseline de producto en
[2026-08-27-medreamm-pilot100-t-gpt54mini.md](2026-08-27-medreamm-pilot100-t-gpt54mini.md).

Tras reiniciar el contenedor se ejecutó un caso de control:

- condición registrada: `T`;
- imágenes enviadas: 0;
- modelo solicitado: `gpt5`;
- modelo final: `gpt5`;
- diferencial: 7 diagnósticos.

La cohorte completa se lanzó después de esta comprobación. El runner conservó
la protección frente a rate limit y respetó `Retry-After`.

## Resultado técnico

- Respuestas completadas: 100/100.
- Modelo final: `gpt5` en 100/100.
- Casos resumidos: 32/100.
- Latencia media: 35,6 segundos.
- Mediana: 35,0 segundos.
- Diferencial: 7 diagnósticos en 15 casos, 6 en 27, 5 en 54, 4 en 3 y lista
  vacía en 1.

## Resultado strict_equivalence

- R@1: 43/100 — 43%.
- R@3: 58/100 — 58%.
- R@5: 63/100 — 63%.
- Cobertura: 64/100 — 64%.
- Posición media entre matches: 1,641.
- MRR: 0,512.

Resolución: 40 SNOMED, 1 ICD-10 exacto, 1 ICD-10 parent, 2 ICD-10 sibling, 5
BERT autoconfirmados, 2 BERT contrastados y 13 decisiones del juez LLM.

## Puente legacy_similarity

Sobre las mismas respuestas y códigos:

- R@1: 54%.
- R@3: 75%.
- R@5: 92%.
- Cobertura: 95%.
- Posición media entre matches: 2,105.
- MRR: 0,674.
- Decisiones del juez LLM: 43, frente a 13 con strict.

Cambiar solo el juez eleva la cobertura de 64% a 95%. Esta diferencia de 31
puntos confirma que la cobertura legacy histórica está dominada en parte por
aceptación de diagnósticos relacionados.

## Comparación emparejada con T+I

Manteniendo los mismos 100 casos, historias, modelo y evaluador:

- cobertura `T`: 64%;
- cobertura `T+I`: 80%;
- ganancia absoluta: 16 puntos;
- R@1: 43% → 61%, ganancia de 18 puntos;
- R@3: 58% → 74%, ganancia de 16 puntos;
- R@5: 63% → 78%, ganancia de 15 puntos.

Por caso:

- match solo con `T+I`: 20;
- match solo con `T`: 4;
- match en ambas condiciones: 60;
- sin match en ninguna: 16.

Entre los 60 matches compartidos, `T+I` mejoró la posición en 9, `T` la mejoró
en 5 y 46 mantuvieron la misma posición. La prueba exacta de McNemar sobre los
24 casos discordantes da `p=0,00154`.

El control `T+shuffled-I` ya está medido: cobertura 62%, indistinguible de
`T` y 18 puntos por debajo de `T+I`. La ganancia depende de la imagen
correcta. El juez y los golds siguen pendientes de revisión clínica.

## Trazabilidad

- Manifest: `datasets/processed/medreamm_pilot100/manifest.yaml`.
- Respuestas: `outputs/pilot100_gpt5_T_v2/responses.jsonl`.
- Evaluación prevista:
  `outputs/pilot100_gpt5_T_v2/evaluation_v4_primary_strict/`.
