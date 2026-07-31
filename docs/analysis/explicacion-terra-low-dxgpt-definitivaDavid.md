# Por qué seleccionamos GPT-5.6 Terra low dentro de GPT-5.6

**Explicación fundamentada de la selección frente a Sol, Luna y niveles superiores de razonamiento.**

> **Estado de producto:** Terra low es el candidato seleccionado dentro de la familia GPT-5.6, pero no es el modelo normal desplegado actualmente. Producción usa `gpt-5.4-mini low` en modo normal y `gemini-3-pro-preview low` en modo avanzado.

## Outcome de esta investigación

El resultado esperado es poder responder de forma breve, verificable y honesta a esta pregunta:

> ¿Por qué elegiríamos GPT-5.6 Terra low en vez de Sol o de aumentar el nivel de reasoning?

La respuesta debe:

1. distinguir resultados propios, explicaciones respaldadas e hipótesis;
2. justificar la decisión con las métricas relevantes para una lista diagnóstica;
3. declarar las excepciones y limitaciones;
4. indicar qué evidencia obligaría a reconsiderarla.

## Respuesta ejecutiva

La elección está medida sobre `all_256_clean` (`n=256`) con prompt, juez y umbrales congelados.

| Configuración | avg_pos ↓ | R@1 | R@3 | Coverage |
|---|---:|---:|---:|---:|
| **Terra low** | **1,382** | 74,6% | **94,9%** | **98,1%** |
| Terra high | 1,426 | 71,9% | 93,0% | 97,3% |
| Terra xhigh, corregido a 20k | 1,427 | **76,2%** | 91,0% | 96,9% |
| Terra medium | 1,516 | 71,1% | 91,0% | 97,7% |
| Luna low | 1,540 | 69,1% | — | 97,7% |
| Sol medium + rank-first v1 | 1,476 | 71,9% | — | 97,7% |
| Sol medium, prompt histórico | 1,584 | 69,9% | — | 97,7% |
| Sol low, prompt histórico | 1,619 | 68,4% | — | 98,4% |

Tres observaciones sostienen la decisión:

1. **Terra supera a Sol en todas las configuraciones probadas.** Incluso Sol medium con un prompt diseñado para corregir su tendencia a rellenar listas queda en `1,476`, por detrás de Terra low (`1,382`).
2. **Dentro de Terra, low ofrece el mejor resultado global** en `avg_pos`, R@3 y coverage. Xhigh es la excepción que debe declararse: gana en R@1.
3. **Ni el tier comercial ni el esfuerzo tienen una relación monotónica con esta tarea.** Terra supera a Luna y Sol; además, el effort óptimo cambia según la familia.

No afirmamos que menos razonamiento sea siempre mejor. GPT-5.2 y Sol mejoraron de low a medium. El óptimo debe medirse para cada modelo y tarea.

### Respuesta en una frase

> Elegimos Terra low dentro de GPT-5.6 porque, con el mismo benchmark, prioriza mejor el diagnóstico correcto y mantiene mayor cobertura y R@3 que Sol y que los esfuerzos superiores de Terra; aumentar capacidad o reasoning añade coste y, en esta tarea, no mejora el resultado global.

## 1. Marco epistémico

| Etiqueta | Significado |
|---|---|
| **[HECHO INTERNO]** | Medido en este repositorio bajo una configuración identificable |
| **[EVIDENCIA EXTERNA]** | Resultado publicado; puede proceder de otra tarea o familia y no demuestra causalidad en DxGPT |
| **[EXPLICACIÓN]** | Interpretación compatible con evidencia interna y externa |
| **[HIPÓTESIS]** | Mecanismo plausible todavía no validado |

## 2. Hechos internos

### 2.1 Terra low gana globalmente, pero no en todas las métricas

**[HECHO INTERNO]** Terra low obtiene el mejor `avg_pos` (`1,382`), R@3 (`94,9%`) y coverage (`98,1%`) de la escalera de esfuerzo Terra.

**[HECHO INTERNO]** Terra xhigh corregido a 20k obtiene el mejor R@1: `76,2%` frente a `74,6%` de low. Al mismo tiempo, baja a `91,0%` en R@3 y `96,9%` de coverage.

Esto obliga a declarar la métrica primaria. DxGPT devuelve una lista priorizada, no una respuesta única; por ello se valora el conjunto `avg_pos` + R@3 + coverage y no R@1 de forma aislada. Si el producto pasara a mostrar solo una hipótesis, habría que revisar esta decisión.

### 2.2 Comparación entre tiers GPT-5.6

**[HECHO INTERNO]**

- Luna low: `1,540`
- Terra low: **`1,382`**
- Sol low: `1,619`

Terra, el tier comercial intermedio, gana en la comparación equivalente.

**[HECHO INTERNO]** Sol se acerca con `medium + rank-first v1` (`1,476`), pero sigue detrás de Terra low. Ese prompt empeora Terra (`1,382` → `1,414`), por lo que corrige un comportamiento específico de Sol y no constituye una mejora universal.

**[EVIDENCIA EXTERNA]** Los precios oficiales por millón de tokens de contexto corto son:

- Luna: `$1` entrada / `$6` salida
- Terra: `$2,50` / `$15`
- Sol: `$5` / `$30`

Sol cuesta el doble que Terra por token. Frente a Sol, Terra es mejor en los resultados medidos y más barata; no existe en estas pruebas un intercambio calidad-coste favorable a Sol.

### 2.3 El effort óptimo depende del modelo

| Familia | Mejor configuración observada |
|---|---|
| GPT-5.2 | medium por ranking; low por cobertura |
| GPT-5.6 Luna | low |
| GPT-5.6 Terra | low globalmente; xhigh solo gana R@1 |
| GPT-5.6 Sol | medium; rank-first v1 mejora más |
| Gemini 3 Pro | low |

**[HECHO INTERNO]** GPT-5.2 sobre el dataset histórico `all_150`: low `1,727` con 100% de cobertura; medium `1,664`; high `1,781` con 13 respuestas vacías a 12k.

**[HECHO INTERNO]** Gemini 3 Pro: low obtiene `1,299` y medium `1,315` en narrativa. En cuatro datasets HPO (`n=644`), medium degrada de forma consistente: `−5,1 pp` en R@1, `−8,8 pp` en R@3 y aproximadamente `+50%` de latencia.

La conclusión defendible es específica: **más reasoning no garantiza mejores resultados y debe evaluarse por modelo y tarea**.

### 2.4 Fallo operativo del esfuerzo alto

`max_tokens` incluye reasoning oculto y respuesta visible. Algunos runs agotaron el presupuesto antes de emitir JSON:

- GPT-5.2 high: 13 respuestas vacías a 12k.
- Luna xhigh: 22 respuestas vacías a 12k.
- Terra xhigh: 4 respuestas vacías a 12k.

Los cuatro casos Terra se reejecutaron a 20k:

- `R176` → P2
- `R193` → P4
- `R254` → P1
- `R549` → P1

No se debe confundir truncación con peor capacidad clínica. Hay que publicar por separado:

1. el resultado operativo con el límite real;
2. el resultado corregido o condicionado a respuesta válida;
3. el número de truncaciones.

### 2.5 Longitud y priorización del diferencial

**[HECHO INTERNO]** Terra low produce `3,60` diagnósticos por caso. Luna y Sol históricos producen aproximadamente `4,5–4,7`; Sol medium produce `4,69`.

**[HECHO INTERNO]** Rank-first v1 reduce Sol a `3,89` diagnósticos por caso y mejora su `avg_pos` de `1,584` a `1,476`.

**[EXPLICACIÓN]** Terra parece estar mejor calibrada para comprometerse con una lista corta y ordenada. Cuando la cobertura ronda el 98%, añadir alternativas puede desplazar el diagnóstico correcto sin recuperar muchos casos nuevos.

**[HIPÓTESIS]** La longitud podría mediar causalmente la mejora, pero los datos actuales solo prueban asociación. Habría que controlar longitud y contenido para demostrar causalidad.

## 3. Evidencia externa

La literatura apoya que aumentar el cómputo de inferencia puede tener rendimientos decrecientes o negativos, pero no demuestra por sí sola el mecanismo de DxGPT.

### 3.1 Calibración y reasoning

**[EVIDENCIA EXTERNA]** *Calibration Drift Under Reasoning* (arXiv:2606.11211) describe una relación no monotónica entre presupuesto y calibración en preguntas diseñadas como trampas de razonamiento. La evidencia principal procede de Llama 3.1 8B; los resultados para 70B son inconclusos. Es una analogía útil, no una validación directa de Terra.

**[EVIDENCIA EXTERNA]** Lacombe et al. (arXiv:2508.15050) observan que aumentar el presupuesto deteriora la calibración en una tarea de confianza experta, mientras que incorporar búsqueda mejora el resultado (`89,3%` vs `48,7%`). La tarea no es diagnóstico diferencial.

**[EXPLICACIÓN]** La posición en una lista está relacionada con confianza relativa, pero no equivale a una métrica formal de calibración como ECE. Esta literatura respalda la plausibilidad de la no monotonía, no prueba que sea su causa aquí.

### 3.2 Inverse scaling en cómputo de inferencia

**[EVIDENCIA EXTERNA]** Gema et al. (arXiv:2507.14417) construyen tareas donde razonar durante más tiempo reduce la precisión. Identifican distracción por información irrelevante, sobreajuste al encuadre y desplazamiento desde priores razonables hacia correlaciones espurias.

**[HIPÓTESIS]** Los hallazgos incidentales de una narrativa clínica podrían actuar como distractores y reordenar el diferencial con efforts altos. Hay que confirmarlo mediante revisión de casos.

### 3.3 Diagnóstico diferencial

**[EVIDENCIA EXTERNA]** Rao et al., JAMA Network Open 2026, evaluaron 21 LLMs con PrIME-LLM. Los modelos tuvieron tasas de fallo superiores al 80% en diagnóstico diferencial y menores en diagnóstico final. También encontraron una ventaja global de los modelos optimizados para razonamiento.

Esto aporta dos ideas:

- diagnóstico final y diferencial no deben tratarse como la misma capacidad;
- la literatura no permite concluir que el razonamiento sea perjudicial en general.

Nuestros resultados son más estrechos: dentro de Terra y bajo este prompt, low presenta el mejor balance global.

**[EVIDENCIA EXTERNA]** Un estudio de DeepSeek R1 en razonamiento médico encontró respuestas incorrectas más largas que las correctas (`8.118` vs `3.648` caracteres; `n=7` errores). Es una señal compatible con sobre-razonamiento, pero la muestra de errores es pequeña y no demuestra causalidad.

### 3.4 Los benchmarks generales miden otras capacidades

**[EVIDENCIA EXTERNA]** El Artificial Analysis Coding Agent Index v1.1 ordena Sol `80,0`, Terra `77,4` y Luna `74,6`. Evalúa coding agéntico, terminal y coordinación de herramientas.

DxGPT hace una llamada de generación diagnóstica sin herramientas ni estado. Que ambos rankings sean distintos muestra que la elección depende de la tarea; no demuestra que el índice externo sea incorrecto.

**[EVIDENCIA EXTERNA]** METR encontró un nivel excepcional de *evaluation gaming* al evaluar Sol en tareas de software de horizonte largo. El hallazgo afecta a la robustez de esa medición concreta y no debe extrapolarse como defecto clínico. Sí refuerza la necesidad de usar evaluaciones propias y específicas.

## 4. Revisión clínica pendiente

Este es el principal hueco del argumento y el área donde una revisión biomédica aporta más valor.

El benchmark mide el sistema completo:

`modelo + labeler + SNOMED/ICD + similitud semántica + juez LLM`

Un nombre más específico puede tomar otra ruta de evaluación y ser rechazado aunque resulte clínicamente razonable.

### Hipótesis que debe descartarse primero

Parte del deterioro de high/xhigh podría proceder del evaluador y no del razonamiento clínico. Si una revisión ciega confirma este patrón de forma sustancial, habría que corregir el labeler y repetir la comparación.

### Taxonomía propuesta

| Código | Patrón |
|---|---|
| F1 | El diagnóstico correcto baja de posición y una alternativa peor sube |
| F2 | La lista se expande con variantes solapadas o alternativas de relleno |
| F3 | Un hallazgo incidental domina la priorización |
| F4 | El modelo ofrece un diagnóstico clínicamente válido, pero el evaluador no lo reconoce |
| F5 | La respuesta queda vacía por agotar tokens |

### Protocolo recomendado

1. Comparar por `case_id` Terra low frente a high y xhigh.
2. Seleccionar 15–20 discordancias de mayor magnitud.
3. Presentar las listas de forma ciega, sin modelo ni effort.
4. Revisar corrección clínica, especificidad, priorización y utilidad del diferencial.
5. Clasificar cada diferencia en F1–F5.
6. Documentar ejemplos representativos y frecuencias, sin convertir un umbral arbitrario en prueba causal.

Para cuantificar incertidumbre:

- usar bootstrap pareado sobre casos para estimar sensibilidad a la muestra de pacientes;
- repetir ejecuciones para estimar variabilidad del modelo y del juez.

El bootstrap de una única ejecución no mide la no determinación entre runs.

## 5. Respuestas a objeciones

### «Terra xhigh tiene mejor R@1. ¿No demuestra que más reasoning es mejor?»

Solo en R@1: `76,2%` frente a `74,6%`. Es peor en R@3 (`91,0%` vs `94,9%`), coverage (`96,9%` vs `98,1%`) y `avg_pos`. Si DxGPT mostrara una única respuesta, habría que reconsiderar qué métrica manda.

### «¿Se está eligiendo lo barato y justificándolo después?»

Frente a Sol, Terra es más barata y obtiene mejores métricas internas. La decisión no exige sacrificar calidad medida. Esto no sustituye la validación fuera de muestra ni el A/B de producto.

### «Sol mejora con rank-first. ¿Tuvo una comparación justa?»

Su mejor resultado registrado es `1,476`, todavía detrás de Terra low (`1,382`). Además, rank-first se diseñó inspeccionando `all_256_clean`, por lo que debe validarse fuera de muestra antes de tratarlo como definitivo.

### «¿Y si el problema es el evaluador?»

Es la hipótesis F4 y debe comprobarse mediante revisión clínica ciega. Si explica una parte sustancial del efecto, habrá que reparar el pipeline y repetir el benchmark.

### «¿Una sola ejecución permite afirmar que 1,382 es mejor que 1,426?»

La diferencia observada favorece low, pero falta publicar incertidumbre. El bootstrap pareado estudia sensibilidad a los casos; los runs repetidos estudian variabilidad del sistema. Hasta entonces, las diferencias pequeñas deben describirse como evidencia provisional.

## 6. Cuándo reconsiderar

| Disparador | Acción |
|---|---|
| Terra low y high resultan indistinguibles con análisis pareado y runs repetidos | Elegir por coste, latencia y estabilidad |
| Sol rank-first valida fuera de muestra y supera Terra low | Reevaluar Sol declarando coste y latencia |
| La revisión clínica atribuye el deterioro al evaluador | Corregir labeler y repetir la comparación |
| El A/B de producto no reproduce la ventaja | Rediseñar endpoint o selección |
| DxGPT pasa a mostrar una sola hipótesis | Convertir R@1 en métrica primaria |
| El flujo incorpora herramientas, búsqueda o varios pasos | Reevaluar Sol y los efforts superiores |
| Cambian precios o límites de tokens | Recalcular coste, latencia y truncaciones |

Desde el punto de vista regulatorio, cualquier cambio de modelo o configuración debe pasar por el control de cambios e impacto definido por el QMS. No puede afirmarse sin revisar el expediente que cada cambio exija automáticamente una nueva evaluación de conformidad.

## 7. Trabajo pendiente

1. Ejecutar el análisis pareado Terra low ↔ high/xhigh.
2. Añadir intervalos de confianza y, si el coste lo permite, runs repetidos.
3. Realizar la revisión clínica ciega de discordancias.
4. Validar Sol medium + rank-first v1 fuera de `all_256_clean`.
5. Ejecutar el A/B Terra low frente al modelo normal actual.
6. No seguir ajustando prompts usando `all_256_clean` como desarrollo y prueba final.

## 8. Limitaciones

1. Una ejecución por configuración, sin incertidumbre publicada.
2. Un único dataset narrativo para la escalera Terra.
3. Riesgo de sobreajuste de rank-first a `all_256_clean`.
4. GPT-5.2 usa otro dataset y una versión histórica del pipeline.
5. El benchmark mide el sistema de evaluación completo, no una verdad clínica independiente.
6. La revisión clínica sigue pendiente.
7. La evidencia externa procede de tareas y modelos distintos.
8. Un ranking técnico no representa resultados sobre pacientes ni una evaluación de conformidad.

## Fuentes internas

- `docs/analysis/reasoning-effort-and-model-size-investigation-2026-07.md`
- `docs/analysis/comparison-gpt52-reasoning-effort.md`
- `docs/analysis/gpt56-luna-terra-sol-case-analysis-2026-07.md`
- `docs/benchmark-report.html`
- `bench/pipelines/pipeline_v4 - fork/main/output/rankingV2.txt`
- `bench/candidate-prompts/juanjo_classic_v2.txt`
- `bench/candidate-prompts/juanjo_classic_v2_rank_first.txt`

## Fuentes externas verificadas

- OpenAI, [precios de API](https://developers.openai.com/api/docs/pricing)
- OpenAI, [presentación de GPT-5.6 Sol, Terra y Luna](https://openai.com/index/previewing-gpt-5-6-sol/)
- Hiremath & Hiremath, [*Calibration Drift Under Reasoning*](https://arxiv.org/abs/2606.11211)
- Lacombe, Wu & Dilworth, [*Don't Think Twice! Over-Reasoning Impairs Confidence Calibration*](https://arxiv.org/abs/2508.15050)
- Gema et al., [*Inverse Scaling in Test-Time Compute*](https://arxiv.org/abs/2507.14417)
- Rao et al., [*Large Language Model Performance and Clinical Reasoning Tasks*](https://doi.org/10.1001/jamanetworkopen.2026.4003)
- Moëll, Sand Aronsson & Akbar, [*Medical reasoning in LLMs: an in-depth analysis of DeepSeek R1*](https://doi.org/10.3389/frai.2025.1616145)
- METR, [evaluación de GPT-5.6 Sol](https://metr.org/blog/2026-06-26-gpt-5-6-sol/)

