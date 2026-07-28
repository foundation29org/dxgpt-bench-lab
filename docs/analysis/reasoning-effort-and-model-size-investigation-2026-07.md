# Investigación: por qué menos modelo o menos reasoning puede rendir mejor

## Objetivo

Este documento introduce el problema para continuar la investigación en este repositorio:

> ¿Por qué algunos modelos pequeños, o configuraciones con menos `reasoning_effort`, obtienen mejores resultados diagnósticos que modelos mayores o configuraciones con más razonamiento?

La evidencia actual no respalda una regla universal del tipo «menos reasoning siempre es mejor» ni «el modelo pequeño siempre gana». El comportamiento es **no monótono**, depende del modelo y cambia según prompt, dataset, presupuesto de tokens y métrica.

## Estado actual de producción

- Modo normal: `gpt-5.4-mini low`
- Modo avanzado: `gemini-3-pro-preview low`
- Prompt de producción: `bench/candidate-prompts/juanjo_classic_v2.txt`
- Juez del benchmark actual: `gemini-2.5-pro`

No confundir `gpt-5-mini low`, que fue producción anteriormente, con el modelo normal actual.

## Cómo se mide

### Narrativa clínica

Dataset principal: `bench/datasets/all_256_clean.json` (`n=256`).

Métricas:

- `avg_pos`: posición media del diagnóstico aceptado; menor es mejor.
- R@1: diagnóstico aceptado en primera posición.
- R@3 / R@5: diagnóstico aceptado dentro de las primeras posiciones.
- Coverage: casos con algún match aceptado.
- Empty responses / parsing failures: fallos operativos, no fallos clínicos.
- Latencia, tokens y coste.

El evaluador intenta resolver cada caso por SNOMED, relaciones ICD-10, BERT y finalmente juicio LLM. Por ello, cambios en la longitud o formulación del nombre pueden cambiar la ruta de evaluación aunque la intención clínica sea similar.

### Enfermedades raras HPO

Se usan seis datasets del paper DeepRare: DDD, RAMEDIS, LIRICAL, MME, HMS y MyGene2 (`n=3.017` agregado).

Estos resultados son importantes porque permiten comprobar si una mejora narrativa se generaliza a síntomas HPO y no es sobreajuste a `all_256_clean`.

## Evidencia acumulada

### GPT-5.2: medium mejora el ranking, high falla por dos causas

Fuente: [comparison-gpt52-reasoning-effort.md](comparison-gpt52-reasoning-effort.md).

Dataset histórico `all_150`:

| Effort | Avg pos | Coverage | Lectura |
|---|---:|---:|---|
| low | 1.727 | 100.0% | Mejor cobertura |
| medium | **1.664** | 99.3% | Mejor ranking |
| high | 1.781 | 91.3% | 13 respuestas vacías a 12k |

La conclusión correcta es que `medium` gana si el objetivo primario es `avg_pos`; `low` gana si se exige cobertura total. El documento histórico llama a low «mejor» en algunos apartados, pero sus propios datos muestran que medium tiene el mejor `avg_pos`.

High no debe interpretarse únicamente como peor capacidad: 13 casos consumieron los 12.000 tokens en reasoning y produjeron `response=0`. La cobertura raw mezcla calidad con un límite técnico.

### GPT-5.6 Luna: low es el mejor punto

| Effort | Avg pos | R@1 | Coverage | Incidencias |
|---|---:|---:|---:|---|
| low | **1.540** | **69.1%** | 97.7% | 0 vacíos |
| high | 1.564 | 68.8% | 97.7% | 0 vacíos |
| medium | 1.584 | 66.0% | 97.7% | 0 vacíos |
| xhigh | 1.594 | 62.9% raw | 89.5% raw | 22 vacíos a 12k |

Medium y high empeoran sin truncación, por lo que aquí sí existe una señal de peor priorización con más reasoning. Xhigh añade un problema operativo grave.

### GPT-5.6 Terra: low gana globalmente; xhigh concentra más P1

| Effort | Avg pos | R@1 | R@3 | Coverage |
|---|---:|---:|---:|---:|
| low | **1.382** | 74.6% | **94.9%** | **98.1%** |
| high | 1.426 | 71.9% | 93.0% | 97.3% |
| xhigh corregido a 20k | 1.427 | **76.2%** | 91.0% | 96.9% |
| medium | 1.516 | 71.1% | 91.0% | 97.7% |

El run xhigh original tuvo cuatro respuestas vacías a 12k. Se reejecutaron solo esos casos con 20k:

- `R176` → P2
- `R193` → P4
- `R254` → P1
- `R549` → P1

Después de corregirlos, xhigh logra el mejor R@1, pero low sigue ganando en `avg_pos`, coverage y recall acumulado. Esto demuestra que un effort puede mejorar una métrica y empeorar otras.

### GPT-5.6 Sol: medium y un prompt específico sí ayudan

| Configuración | Avg pos | R@1 | Coverage |
|---|---:|---:|---:|
| Sol low, prompt histórico | 1.619 | 68.4% | 98.4% |
| Sol medium, prompt histórico | 1.584 | 69.9% | 97.7% |
| **Sol medium, rank-first v1** | **1.476** | **71.9%** | 97.7% |
| Sol medium, rank-first canonical v2 | 1.593 | 65.2% | 96.9% |

Sol medium mejora a low, así que más reasoning no siempre perjudica. La mejora mayor proviene de corregir un comportamiento específico: Sol generaba `4.69` candidatos por caso y tendía a rellenar la lista; rank-first v1 lo reduce a `3.89` y mejora la priorización.

La misma variante empeora Terra low (`1.382` → `1.414`). No es una mejora universal del prompt: es una corrección específica para Sol.

### Gemini 3 Pro: low supera a medium

En narrativa, `gemini-3-pro-preview medium` queda casi empatado pero ligeramente peor que low (`1.315` vs `1.299`).

En cuatro datasets HPO independientes (`n=644`), medium degrada de forma consistente:

- R@1 ponderado: `-5.1 pp`
- R@3 ponderado: `-8.8 pp`
- latencia: aproximadamente `+50%`

Producción avanzada mantiene `gemini-3-pro-preview low`.

## Conclusión empírica

El effort óptimo observado es específico de cada modelo:

| Familia | Mejor configuración observada |
|---|---|
| GPT-5.2 | medium por ranking; low por cobertura |
| GPT-5.6 Luna | low |
| GPT-5.6 Terra | low globalmente; xhigh solo gana R@1 |
| GPT-5.6 Sol | medium; rank-first v1 mejora más |
| Gemini 3 Pro | low |

No existe una relación monotónica entre más reasoning y mejor diagnóstico.

Tampoco puede concluirse que «el modelo más pequeño gana». Terra supera tanto a Luna como a Sol en este benchmark; `gpt-5.4-mini` supera a varias alternativas mayores, pero no a Terra ni a los Gemini líderes. La hipótesis correcta es que existe un **punto de calibración entre capacidad, estilo de salida y tarea**.

## Hipótesis explicativas

### 1. Sobre-razonamiento y expansión del diferencial

Más reasoning puede generar:

- más diagnósticos plausibles;
- variantes solapadas del mismo síndrome;
- alternativas raras antes del diagnóstico más directo;
- mayor atención a excepciones que desplaza la respuesta principal.

Como `avg_pos` premia priorización, una lista clínicamente rica puede puntuar peor si entierra el diagnóstico correcto.

### 2. Calibración y estilo de salida

El modelo no solo debe «saber» el diagnóstico: debe asignarle la probabilidad relativa correcta y ponerlo primero. Terra low produce listas más cortas (`3.60` DDX/caso) que Luna y Sol históricos (`4.5–4.7`), y obtiene más P1.

### 3. Interacción modelo × prompt

El mismo prompt produce políticas de listado distintas según el modelo:

- Terra ya es conciso con el prompt histórico.
- Sol interpreta `N possible diagnoses` como una invitación a rellenar.
- Rank-first corrige Sol pero perturba Terra.

Por tanto, un prompt puede ser globalmente estable sin ser óptimo para todas las familias.

### 4. Presupuesto oculto de reasoning

`max_tokens` incluye reasoning oculto y respuesta visible. En high/xhigh algunos modelos consumen todo el presupuesto antes de emitir JSON.

Hay que distinguir:

- calidad operativa al límite configurado;
- calidad clínica condicionada a una respuesta válida;
- capacidad con presupuesto suficiente.

Los tres resultados son útiles, pero responden preguntas diferentes.

### 5. Sensibilidad del evaluador

Nombres más largos o específicos pueden:

- recibir códigos SNOMED/ICD distintos;
- pasar de una ruta automática al juez LLM;
- ser rechazados aunque sean clínicamente próximos;
- producir falsos positivos taxonómicos en otras ocasiones.

El benchmark mide el sistema modelo + labeler + taxonomía + juez, no una verdad clínica independiente.

### 6. Complejidad de tarea

Muchos casos narrativos contienen una pista discriminante clara. Un modelo calibrado para responder directamente puede superar a otro que explore muchas alternativas. En tareas HPO más abiertas, la relación puede cambiar; por eso la validación multi-dataset es obligatoria.

## Riesgos metodológicos

### Comparaciones históricas no equivalentes

GPT-5.2 usa `all_150` y un estado histórico del pipeline. No comparar su valor absoluto directamente con `all_256_clean` actual. Solo usarlo para estudiar la forma de la curva de effort dentro del mismo run.

### Truncaciones

No declarar que un effort tiene peor capacidad solo por coverage raw cuando existen `EMPTY_RESPONSE`. Publicar:

1. resultado operativo con el límite real;
2. resultado corregido o condicionado a respuesta válida;
3. cantidad de truncaciones.

### Sobreajuste

`all_256_clean` ya se ha usado para inspeccionar errores y diseñar rank-first. No crear más variantes basadas en esos mismos casos y usar luego el mismo dataset como prueba definitiva.

### Varianza

Aunque `temperature=0.1`, modelo y juez no son necesariamente deterministas. Diferencias pequeñas deben confirmarse con repetición o análisis pareado, no solo con una décima de `avg_pos`.

### Métricas en conflicto

Terra xhigh tiene mejor R@1 que low, pero peor coverage y R@3. La decisión debe declarar de antemano qué métrica es primaria y qué pérdidas son aceptables.

## Protocolo recomendado para continuar

### 1. Congelar el diseño

Para cada comparación:

- mismo dataset;
- mismo prompt;
- mismo juez;
- mismos umbrales;
- misma traducción;
- mismo presupuesto de tokens suficiente;
- cambiar una sola variable: modelo o effort.

### 2. Definir endpoints antes del run

Reportar como mínimo:

- `avg_pos`;
- R@1, R@3 y R@5;
- coverage;
- respuestas vacías y parsing;
- DDX/caso;
- latencia y tokens;
- distribución por método de resolución.

### 3. Separar dos escenarios de tokens

- **Operativo:** presupuesto real de producción; las truncaciones cuentan como fallos.
- **Capacidad:** presupuesto que garantice respuesta visible; reparar quirúrgicamente truncaciones o ejecutar el run completo con techo mayor.

No mezclar ambos en una única cifra sin etiqueta.

### 4. Usar análisis pareado

Comparar por `case_id`:

- casos donde A mejora;
- casos donde B mejora;
- empates;
- cambios P1↔P2/P3;
- aparición/desaparición del diagnóstico;
- cambios en longitud y especificidad de lista.

Aplicar bootstrap pareado o intervalos de confianza para evitar interpretar ruido como mejora.

### 5. Validar fuera de muestra

Prioridades:

1. Validar Sol medium + rank-first v1 en un dataset no usado para diseñar el prompt.
2. Mantener Terra low como candidato normal y comprobarlo en A/B de producto.
3. No seguir afinando prompts contra `all_256_clean`.
4. Si se mantiene la comparación GPT-5.2 high, reparar sus 13 truncaciones con presupuesto mayor y etiquetar el resultado como histórico.

### 6. Añadir revisión clínica ciega

Seleccionar discordancias relevantes y pedir a clínicos que comparen ambas listas sin conocer modelo ni configuración. Esto permite detectar:

- matches del juez incorrectos;
- diagnósticos más específicos clínicamente preferibles;
- listas exhaustivas útiles aunque penalizadas por `avg_pos`;
- diferencias que podrían cambiar decisiones reales.

## Preguntas abiertas

1. ¿La ventaja de Terra low se mantiene en tráfico real y reduce escalados al modo avanzado?
2. ¿Sol rank-first v1 generaliza a HPO o es una mejora específica de narrativa?
3. ¿La menor longitud de lista explica causalmente la mejora o solo está correlacionada?
4. ¿Qué parte del resultado cambia al usar otro juez o revisión humana?
5. ¿Cuál es el presupuesto de reasoning óptimo por familia bajo límites reales de latencia y coste?
6. ¿Existe una política adaptativa que use low por defecto y aumente effort solo en casos inciertos?

## Mapa de artefactos

- Estado operativo: `docs/evaluation-refresh-plan-2026-07.md`
- Informe HTML: `docs/benchmark-report.html`
- GPT-5.2 reasoning: `docs/analysis/comparison-gpt52-reasoning-effort.md`
- GPT-5.6 y rank-first: `docs/analysis/gpt56-luna-terra-sol-case-analysis-2026-07.md`
- Ranking maestro: `bench/pipelines/pipeline_v4 - fork/main/output/rankingV2.txt`
- Prompt histórico: `bench/candidate-prompts/juanjo_classic_v2.txt`
- Prompt experimental Sol: `bench/candidate-prompts/juanjo_classic_v2_rank_first.txt`
- Terra xhigh corregido: `bench/pipelines/pipeline_v4 - fork/main/output/all_256_clean/juanjo_classic_v2/gpt_5_6_terra_xhigh_translated_en/20260727185344/summary_corrected_20k_retry.json`

## Resumen para el investigador

La observación es real, pero la explicación no es «menos siempre gana». El benchmark muestra varios óptimos:

- low gana en Luna, Terra y Gemini 3 Pro;
- medium gana en GPT-5.2 por ranking y en Sol;
- xhigh Terra concentra más P1, pero sacrifica cobertura y recall acumulado;
- un prompt anti-relleno mejora mucho Sol y empeora Terra.

La línea de trabajo más prometedora es estudiar **calibración, longitud de diferencial, interacción prompt-modelo y presupuesto de reasoning**, con validación fuera de muestra y revisión clínica. No seguir buscando una regla única basada solo en tamaño o effort.
