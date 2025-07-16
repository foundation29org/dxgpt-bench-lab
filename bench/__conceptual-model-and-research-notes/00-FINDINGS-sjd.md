### **Análisis Metodológico y Conclusiones del Estudio Comparativo IA vs. Clínicos**

#### **1. Objetivo General del Estudio**

El propósito fundamental del estudio fue realizar una evaluación comparativa rigurosa entre la capacidad diagnóstica de una herramienta de inteligencia artificial (DxGPT, basada en GPT-4) y la de un equipo de 78 médicos clínicos del Hospital Sant Joan de Déu. El objetivo era determinar si la IA podía funcionar como una herramienta de apoyo diagnóstico fiable en un entorno pediátrico de alta complejidad.

#### **2. Metodología y Marco de Evaluación**

El estudio se diseñó como un análisis **transversal y unicéntrico**, utilizando un marco de evaluación multidimensional para medir no solo la precisión, sino también la calidad, la consistencia y la usabilidad de las herramientas.

**A. Material de Evaluación (Casos Clínicos):**
*   Se seleccionaron **50 casos clínicos reales y anonimizados** de pacientes pediátricos.
*   La selección incluyó una mezcla equilibrada de **enfermedades comunes y raras** para evaluar el rendimiento en distintos niveles de dificultad.
*   Para analizar el impacto de la información adicional, se crearon **70 escenarios de diagnóstico**:
    *   **50 casos simples:** Con información clínica básica (historia, síntomas, examen físico).
    *   **20 casos extendidos:** A 20 de los casos anteriores se les añadieron resultados de pruebas complementarias (analíticas, radiografías).

**B. Proceso Comparativo:**
*   **Equipo Humano (MDT):** 78 médicos voluntarios (residentes, pediatras y especialistas) diagnosticaron 3 casos cada uno, proponiendo una lista de hasta 5 diagnósticos diferenciales.
*   **Inteligencia Artificial (DxGPT):** El mismo texto de los 70 escenarios se introdujo en la herramienta, que también generó una lista de 5 diagnósticos.

**C. Métricas y Escalas de Evaluación (El "Cómo" se midió):**

Para garantizar una evaluación exhaustiva, se utilizaron cuatro métricas clave:

1.  **Precisión Diagnóstica (Criterio Dicotómico - Acierto/Fallo):**
    *   **Escala:** Binaria (1 = Acierto, 0 = Fallo).
    *   **Definición:** Un panel de 5 pediatras expertos evaluó a ciegas cada lista de diagnósticos. Se consideraba un "acierto" (1) si el diagnóstico final correcto del paciente se encontraba en la lista de 5 diagnósticos propuestos. Esta fue la principal métrica cuantitativa de rendimiento.

2.  **Calidad del Razonamiento Diagnóstico (Escala Likert de 4 Puntos):**
    *   **Escala:** Ordinal de 4 niveles.
    *   **Definición:** Esta métrica cualitativa fue diseñada para evaluar la coherencia y la relevancia clínica del razonamiento, especialmente en los casos de fallo. Los niveles eran:
        1.  **Incoherente:** La lista de diagnósticos no tenía relación con el caso.
        2.  **Coherente, pero no lleva al diagnóstico:** La lista era plausible, pero las pruebas sugeridas no conducirían al diagnóstico correcto.
        3.  **Coherente y lleva al diagnóstico:** Aunque el diagnóstico final no estaba en la lista, el enfoque propuesto era tan acertado que habría llevado a él (considerado un fallo de alta calidad).
        4.  **Lista coherente que incluye el diagnóstico correcto:** Acierto total (equivalente al "1" en la escala dicotómica).

3.  **Consistencia de la IA (Índice de Jaccard y Análisis de Variabilidad):**
    *   **Escala:** Índice de Jaccard (mide la similitud de 0 a 1).
    *   **Definición:** Para evaluar la robustez y consistencia de la IA, cada caso se introdujo 3 veces en la herramienta. La similitud entre las 3 listas de diagnósticos generadas se midió con el **Índice de Jaccard**, que calcula la proporción de palabras exactas compartidas entre las listas. Una puntuación alta indica alta consistencia léxica.

4.  **Experiencia de Usuario (UX - Escala de 5 Puntos):**
    *   **Escala:** Numérica de 1 a 5.
    *   **Definición:** Un subgrupo de 48 médicos evaluó su experiencia directa con la herramienta DxGPT en tres dimensiones: experiencia general, utilidad percibida y facilidad de uso.

---

#### **3. Conclusiones Principales del Estudio y la Discusión del Equipo**

**A. Resultados Cuantitativos y Cualitativos:**

1.  **Precisión Diagnóstica Comparable:** La precisión global de **DxGPT (60% de aciertos) no fue estadísticamente diferente a la de los médicos (65%)**. Esto estableció a la IA como una herramienta con un rendimiento comparable al de los clínicos en esta tarea.
2.  **Rendimiento Superior en Enfermedades Comunes:** Tanto los humanos (79%) como la IA (71%) demostraron ser significativamente más precisos en enfermedades comunes que en enfermedades raras (50% y 49%, respectivamente).
3.  **Alta Calidad de Razonamiento:** La evaluación con la **escala Likert** reveló que, incluso cuando fallaban, tanto los médicos como la IA solían proponer listas de diagnósticos coherentes y con un razonamiento clínico sólido (puntuaciones mayoritarias de 2 y 3).
4.  **Experiencia de Usuario Muy Positiva:** Los médicos valoraron la herramienta con notas altas, destacando su **facilidad de uso (4.5/5)** y su **utilidad potencial (4.1/5)** como un asistente rápido y eficaz.

**B. Hallazgo Clave: La Interpretación de la Variabilidad de la IA**

El análisis de consistencia reveló un hallazgo crucial que requirió una interpretación profunda por parte del equipo:

*   **Observación Inicial:** Los modelos de IA más avanzados, a pesar de su alta precisión, mostraban una **alta variabilidad léxica** (un bajo Índice de Jaccard) en las respuestas generadas para un mismo caso. A primera vista, esto podría interpretarse como inestabilidad o falta de fiabilidad.

*   **Análisis Crítico y Conclusión Refinada:** El equipo concluyó que esta variabilidad no era un defecto, sino una característica ligada a dos factores:
    1.  **La Métrica Utilizada:** El **Índice de Jaccard** mide la similitud de palabras exactas (léxica), no de significados (semántica). Por lo tanto, el modelo podía generar respuestas clínicamente idénticas usando sinónimos (ej. "Enfermedad de Kawasaki" vs. "Síndrome mucocutáneo linfonodular"), que la métrica interpretaba incorrectamente como una gran diferencia.
    2.  **El Comportamiento Exploratorio de la IA:** Se hipotetizó que la arquitectura del modelo (muestreo estocástico, función de entrenamiento) fomentaba un comportamiento "exploratorio", permitiéndole navegar por el espacio diagnóstico de manera más flexible que un razonamiento humano lineal.

*   **Conclusión Final sobre la Consistencia:** La "variabilidad léxica" observada **no implicaba una inconsistencia clínica o semántica**. La alta calidad del razonamiento, confirmada por la **escala Likert (evaluada por expertos humanos)**, demostró que el modelo mantenía una coherencia diagnóstica robusta a pesar de la diversidad en su formulación. Este hallazgo fue fundamental para entender que la IA no solo replica el razonamiento humano, sino que puede llegar a conclusiones correctas a través de rutas cognitivas diferentes y más exploratorias.