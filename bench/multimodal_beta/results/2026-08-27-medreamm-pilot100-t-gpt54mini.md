# MedReaMM pilot100 — T con gpt54mini

Estado: **provisional; evaluación estricta completada**.

## Condiciones

- Fecha: 2026-08-27.
- Casos: los mismos 100 de `pilot100 T+I`.
- Entrada: historia clínica sin imágenes ni documentos.
- Tenant: `dxgpt-local`.
- Modelo realmente utilizado: `gpt54mini`.
- Flujo: comportamiento de producto sin imágenes.

## Resultado técnico

- Respuestas completadas: 100/100 tras reanudar el rate limit.
- Latencia media: 14,3 segundos.
- Mediana: 13,1 segundos.
- Casos resumidos: 32/100.
- Diferencial: 5 diagnósticos en 55 casos, 4 en 36, 3 en 5, 6 en 3 y lista
  vacía en 1.

El caso `32340587` fue clasificado como consulta no médica y devolvió una lista
vacía. En la evaluación end-to-end cuenta como caso sin match, no como error
que invalide el resto de la cohorte.

## Resultado strict_equivalence

- R@1: 43/100 — 43%.
- R@3: 56/100 — 56%.
- R@5 y cobertura: 58/100 — 58%.
- Posición media entre matches: 1,397.
- MRR: 0,493.
- Casos sin match: 42, incluida la lista vacía.

Resolución: 40 SNOMED, 1 ICD-10 exacto, 1 ICD-10 parent, 1 ICD-10 sibling, 8
BERT autoconfirmados, 4 BERT contrastados y 3 decisiones del juez LLM.

## Puente legacy_similarity

Sobre las mismas respuestas y códigos:

- R@1: 55%.
- R@3: 82%.
- R@5 y cobertura: 93%.
- Posición media entre matches: 1,774.
- MRR: 0,697.
- Decisiones del juez LLM: 38, frente a 3 con strict.

El cambio de juez eleva la cobertura de 58% a 93%, sin modificar una sola
respuesta de `gpt54mini`. Esto explica buena parte de la aparente distancia
respecto al 98,1% del benchmark narrativo histórico y confirma que cobertura
legacy no equivale a exactitud diagnóstica estricta.

Frente al flujo de producto `T+I` con `gpt5`, la cobertura baja de 80% a 58%.
Esta diferencia de 22 puntos no mide únicamente el valor de las imágenes:
también cambia el modelo. La comparación causal será `gpt5 T` frente a
`gpt5 T+I`.

## Incidencias

El fichero de respuestas se creó originalmente con un nombre `gpt5`, pero el
servidor utilizó `gpt54mini` en las 100 respuestas. El contenedor había
arrancado antes de cargar el código de override. La evidencia guardada en cada
respuesta (`final_response.model`) permite identificar el modelo real.

También se produjeron 75 errores HTTP 429 en el primer intento. La reanudación
añadió una respuesta correcta para esos 75 casos. El evaluador consolida ambos
intentos por identificador.

## Trazabilidad

- Manifest: `datasets/processed/medreamm_pilot100/manifest.yaml`.
- Respuestas históricamente nombradas:
  `outputs/pilot100_gpt5_T/responses.jsonl`.
- Evaluación:
  `outputs/pilot100_gpt54mini_T/evaluation_v4_primary_strict/`.
