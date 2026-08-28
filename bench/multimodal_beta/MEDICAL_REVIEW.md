# Revisión médico-técnica de MedReaMM

## Objetivo para David

Determinar si la evaluación automática mide equivalencia diagnóstica real y si
las imágenes aportan información clínica útil.

El resultado esperado es:

1. identificar falsos positivos y falsos negativos del juez strict;
2. detectar golds ambiguos, incompletos o con granularidad inadecuada;
3. comprobar que texto e imágenes no revelan explícitamente el diagnóstico;
4. revisar de forma ciega los casos donde `T` y `T+I` discrepan;
5. recomendar una política clínica de equivalencia.

No hay que ejecutar código ni calcular métricas manualmente.

## Contexto mínimo

Sobre las mismas 100 respuestas `T+I + gpt5`:

- strict encontró match en 80/100;
- legacy encontró match en 99/100.

Legacy acepta proximidad clínica; strict exige la misma entidad diagnóstica.
Por ejemplo, legacy llegó a aceptar Burkitt frente a un gold de Hodgkin
clásico. La revisión debe decidir si strict rechaza correctamente y si sus
matches aceptados son verdaderas equivalencias.

Con el mismo `gpt5`:

- texto solo: cobertura strict 64%;
- texto más imágenes: cobertura strict 80%;
- 20 casos hicieron match solo con `T+I`;
- 4 hicieron match solo con `T`.

Esta señal no se considerará ganancia visual definitiva hasta revisar los casos
discordantes y ejecutar el control con imágenes intercambiadas.

## Material que debe recibir

Este Markdown no basta por sí solo. David necesita un paquete local con:

- `datasets/processed/medreamm_pilot25/`;
- `datasets/processed/medreamm_pilot100/`;
- los paquetes `clinical_review.md` indicados abajo;
- manifests y `audit.yaml`;
- historias e imágenes asociadas.

Los datos y outputs están ignorados por git. No deben publicarse ni añadirse al
repositorio sin revisar licencia y condiciones del dataset.

`RESULTS.md` aporta contexto agregado, pero su lectura es opcional: los paquetes
locales contienen los casos concretos.

## Paquetes clínicos preparados

### Calibración inicial de 25 casos

`outputs/pilot25_product/evaluation_v4_primary_strict/clinical_review.md`

Contiene:

- 4 casos sin match;
- 3 matches decididos por el juez LLM;
- gold, diferencial completo, BERT y formulario de adjudicación.

### T+I con gpt5, 100 casos

`outputs/pilot100_product/evaluation_v4_primary_strict/clinical_review.md`

Contiene:

- 20 casos sin match;
- 16 matches decididos por el juez LLM;
- pretriaje técnico para priorizar posibles problemas de equivalencia.

### T con gpt5, 100 casos

`outputs/pilot100_gpt5_T_v2/evaluation_v4_primary_strict/clinical_review.md`

Contiene:

- 36 casos sin match;
- 13 matches decididos por el juez LLM.

### T con gpt54mini, 100 casos

`outputs/pilot100_gpt54mini_T/evaluation_v4_primary_strict/clinical_review.md`

Contiene:

- 42 casos sin match, incluida una lista vacía;
- 3 matches decididos por el juez LLM.

### Comparación ciega T frente a T+I

`outputs/comparisons/pilot100_gpt5_T_vs_TI/clinical_review.md`

Contiene los 24 casos discordantes como listas A y B. No entregar a David:

`outputs/comparisons/pilot100_gpt5_T_vs_TI/coordinator_key.md`

## Orden de trabajo recomendado

### Tarea 1 — Auditoría de fuga

Revisar los diez primeros casos de
`datasets/processed/medreamm_pilot25/audit.yaml`.

Para cada caso:

- leer `history.txt`;
- revisar todas las imágenes;
- buscar diagnóstico, sinónimo inequívoco, leyenda o desenlace posterior;
- distinguir evidencia clínica legítima de una etiqueta que revela la solución;
- decidir `mantener`, `sanear` o `excluir`.

Registrar fuente exacta y justificación.

### Tarea 2 — Calibración del juez

Completar primero el paquete de 25 casos. Para cada uno:

- indicar la primera posición equivalente o `0`;
- clasificar el juez como `correcto`, `falso_positivo`, `falso_negativo` o
  `gold_ambiguo`;
- justificar en 1–3 frases;
- asignar confianza alta, media o baja.

Si aparecen dos o más errores del juez, ampliar la revisión al paquete `T+I`
de 100 casos.

### Tarea 3 — Calidad del gold

En los casos revisados:

- confirmar que el gold es el diagnóstico final;
- comprobar que `primary` representa el objetivo principal;
- distinguir enfermedad de síntoma, hallazgo, fenotipo o complicación;
- revisar granularidad y correspondencia con ICD-11;
- indicar diagnósticos secundarios que también deberían aceptarse.

Clasificar como `gold_valido`, `demasiado_amplio`, `demasiado_especifico`,
`no_es_entidad_diagnostica`, `rol_incorrecto` o `segunda_opinion`.

### Tarea 4 — Comparación ciega de modalidad

Revisar primero una muestra equilibrada de ocho casos del paquete A/B:

- seis casos ganados por una condición;
- dos casos ganados por la otra;
- sin consultar la clave del coordinador.

Para cada caso:

- elegir A, B, empate o ninguna;
- indicar si la imagen aporta evidencia útil, distrae o no cambia la decisión;
- verificar los matches automáticos;
- justificar y asignar confianza.

Si dos o más decisiones contradicen la evaluación automática, ampliar la
revisión a los 24 casos discordantes.

### Tarea 5 — Política de equivalencia

Responder:

1. ¿Debe aceptarse una propuesta más específica que el gold?
2. ¿Cuándo son equivalentes síndrome, causa y manifestación?
3. ¿Pueden aceptarse subtipos histológicos diferentes?
4. ¿Cómo tratar golds fenotípicos o morfológicos?
5. ¿Debe evaluarse solo el gold primario o cualquier diagnóstico final?
6. ¿Conviene publicar dos métricas: equivalencia y utilidad clínica?

## Entregable

Un documento breve con:

- veredicto y justificación de cada caso revisado;
- fugas y acciones recomendadas;
- problemas de gold;
- resultado de la comparación ciega;
- política de equivalencia propuesta;
- confianza y casos que requieren segunda opinión;
- decisión sobre si 80/100 y la ganancia visual pueden publicarse.

El responsable técnico incorporará las adjudicaciones y regenerará las
métricas.
