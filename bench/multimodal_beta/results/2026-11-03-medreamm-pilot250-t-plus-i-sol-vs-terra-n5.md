# MedReaMM pilot250 — T+I, gpt-6.1-sol frente a Terra 5.6 con el prompt «5»

Estado: **provisional; evaluación estricta completada**. Brazo de
referencia: [2026-09-24-medreamm-pilot250-t-plus-i-gpt56terra-phrase.md](2026-09-24-medreamm-pilot250-t-plus-i-gpt56terra-phrase.md)
(Terra «N», 24-sep).

## Preguntas

1. ¿Sol diagnostica mejor que Terra cuando el caso trae imágenes? Es una de
   las cosas que hay que saber antes de decidir si Sol pasa a producción.
2. ¿Pedir exactamente 5 diagnósticos (v0.00196) resta algo en el flujo con
   imágenes? En `narrative_v2` no restaba, pero allí no hay imágenes.

## Condiciones

- Fecha: 2026-11-03. Los dos brazos se ejecutaron a la vez.
- Casos: los mismos 250 de `medreamm_pilot250`, condición `T+I`.
- Servidor: Server en local (`NODE_ENV=local`, tenant `dxgpt-local`, base
  `test` de Cosmos), código de `develop` en `ed999bc` (v0.00196). Incluye el
  prompt «5» y la frase de imagen (`withImageContext`), que ya está en
  producción.
- Cambio solo de prueba, no subido: en producción el camino de visión usa
  siempre el modelo por defecto (`isVisionDiagnoseModel` y el despliegue
  `gpt-5.6-terra` fijo en `buildVisionDiagnoseRequest`). Para que Sol
  recibiera las imágenes, la copia de prueba acepta también `gpt61sol` y usa
  el despliegue `gpt-6.1-sol`. En la prueba previa con un caso, el log del
  servidor mostró `model gpt61sol` en la llamada de diagnóstico y los mismos
  9.550 tokens de entrada que Terra: recibe lo mismo, imágenes incluidas.
- Modelo: `DXGPT_EVAL_MODEL=gpt56terra` o `gpt61sol`. Con el Server actual,
  `requested_model` sale vacío en `responses.jsonl` porque la respuesta ya no
  devuelve el modelo. El modelo de cada llamada queda en `costtrackings`
  (base `test`).
- Evaluador: el mismo que el 24-sep. `evaluate_v4.py`, `strict_equivalence`,
  solo el diagnóstico principal, juez `gemini-2.5-pro` (thinking `low`) y 8
  workers. Todas las llamadas las contestó `gemini-2.5-pro`.

## Resultado técnico

| Brazo | Éxitos | Listas vacías | Latencia media | Mediana | p95 | Máx. |
|---|---:|---:|---:|---:|---:|---:|
| Terra «5» | 250/250 | 3 | 23,1 s | 22,3 s | 32,0 s | 43,8 s |
| Sol «5» | 250/250 | 3 | 29,2 s | 28,3 s | 38,1 s | 73,0 s |
| Terra «N» (24-sep) | 250/250 | 3 | 30,0 s | 29,5 s | 41,9 s | 66,0 s |

Las 3 listas vacías son los mismos casos en los tres brazos (`20052363`,
`32340587`, `28232322`). Los para el filtro clínico previo (gpt-5.4-mini),
que los clasifica como pregunta general o con datos del paciente
insuficientes. No llegan al modelo de diagnóstico.

## Resultado strict_equivalence

| Brazo | R@1 | R@3 | R@5 | Cobertura | Pos. media |
|---|---:|---:|---:|---:|---:|
| Sol «5» | 66,4 % | 80,4 % | 83,6 % | 83,6 % | 1,349 |
| Terra «5» | 58,8 % | 73,2 % | 78,8 % | 78,8 % | 1,503 |
| Terra «N» (24-sep) | 60,8 % | 73,6 % | 77,6 % | 78,0 % | 1,415 |

Resolución:

- Sol: 130 SNOMED, 5 ICD-10 exactos, 3 sibling, 20 BERT autoconfirmados,
  16 BERT contrastados y 35 decisiones del juez.
- Terra «5»: 117 SNOMED, 5 ICD-10 exactos, 1 parent, 5 sibling, 21 BERT
  autoconfirmados, 17 BERT contrastados y 31 decisiones del juez.

McNemar exacto sobre los mismos 250 casos:

| Comparación | R@1 gana / pierde | p | R@5 gana / pierde | p |
|---|---:|---:|---:|---:|
| Sol «5» frente a Terra «5» | 39 / 20 | 0,018 | 26 / 14 | 0,081 |
| Sol «5» frente a Terra «N» (24-sep) | 36 / 22 | 0,087 | 28 / 13 | 0,028 |
| Terra «5» frente a Terra «N» (24-sep) | 16 / 21 | 0,51 | 15 / 12 | 0,70 |

Los 100 casos del piloto anterior (anidados):

| Brazo | R@1 | R@3 | R@5 |
|---|---:|---:|---:|
| Sol «5» | 76 % | 86 % | 88 % |
| Astra (8-sep) | 76 % | 87 % | 88 % |
| Terra «5» | 66 % | 77 % | 79 % |
| Terra «N» (24-sep) | 66 % | 76 % | 80 % |

Sol frente a Astra: 5 / 5 en R@1 y 3 / 3 en R@5 (p = 1,0).

## Lectura

- **Con imágenes, Sol acierta en P1 más que Terra:** +7,6 puntos con el
  mismo código de Server y los mismos casos (39 / 20, p = 0,018). En R@5
  también va por delante (+4,8 puntos), pero sin significación (p = 0,08).
  Es el mismo sentido que en `narrative_v2` y en HPO v2.
- **En los 100 casos anidados, Sol empata con Astra**, que era el mejor
  brazo con imágenes del 8-sep, y Astra tardaba 55 s por caso.
- **Pedir 5 tampoco resta con imágenes:** Terra «5» frente a la «N» del
  24-sep queda en 16 / 21 en R@1 (p = 0,51) y 15 / 12 en R@5 (p = 0,70).
  Esa comparación mezcla el prompt con seis semanas de cambios del Server y
  con la variación entre ejecuciones, así que vale como comprobación, no
  como medida del efecto del prompt.
- **Latencia:** Sol tarda unos 6 s más por caso (mediana 28,3 s frente a
  22,3 s). En la cola, los dos pasan de los 30 s de corte de SWA (p95 38 s y
  32 s). Terra ya va por la ruta asíncrona (`isLongDiagnoseModel`), así que
  Sol en producción necesita lo mismo.
- **Coste:** no se ha medido por caso en este brazo. Con imágenes, la
  entrada (unos 9.500 tokens) pesa más que la salida, y Sol tiene el mismo
  precio de entrada que Terra (2 $ por millón) y una salida más barata (10
  frente a 12 $ por millón). La diferencia por caso debería ser pequeña.

## Qué haría falta para Sol en producción (no hecho)

- Añadir `gpt61sol` a `isLongDiagnoseModel` y a `MODEL_PROCESSING_TIMES`.
- Que el camino de visión use el despliegue del modelo elegido y no
  `gpt-5.6-terra` fijo.
- Revisar el modo `direct` (síncrono), que no pasa por la ruta asíncrona.

## Trazabilidad

- Respuestas: `outputs/pilot250_gpt61sol_TI_n5/responses.jsonl` y
  `outputs/pilot250_gpt56terra_TI_n5/responses.jsonl`.
- Evaluación: `evaluation_v4_primary_strict/` dentro de cada carpeta.
- Comparación: McNemar con `paired` de
  `bench/pipelines/pipeline_v5/main/build_report.py`, la misma que el
  informe V5 (sección «Con imágenes»).
