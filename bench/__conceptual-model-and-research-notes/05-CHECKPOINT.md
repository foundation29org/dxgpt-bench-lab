
### **Tabla 1. Comparación de Modelos (ICD10+BERT vs. LLM como Juez)**

Esta tabla resume la mejora de desempeño cuando se introduce un LLM (GPT-4-O) como evaluador externo (*Judge*) respecto al sistema base ICD10+BERT. Se reportan los porcentajes de acierto de cada sistema, junto con la mejora absoluta y relativa obtenida por cada modelo evaluado.

| Modelo | ICD10+BERT (%) | LLM as Judge (%) | Mejora Absoluta (%) | Mejora Relativa (%) |
| ------ | -------------- | ---------------- | ------------------- | ------------------- |
| 4o     | 78.78%         | 81.70%           | +2.92%              | +3.71%              |
| 4-1    | 74.22%         | 77.50%           | +3.28%              | +4.42%              |
| o1     | 76.33%         | 84.10%           | +7.77%              | +10.18%             |
| o3     | 80.46%         | 84.30%           | +3.84%              | +4.77%              |
| o3-pro | 79.89%         | 83.90%           | +4.01%              | +5.02%              |

**Notas analíticas:**

* La **mejora absoluta** indica el incremento directo en la tasa de acierto (%), mientras que la **mejora relativa** expresa ese incremento respecto al punto de partida (ICD10+BERT).
* El modelo **o1** destaca con una mejora relativa superior al 10%, sugiriendo una fuerte sinergia entre su arquitectura y el juicio clínico simulado por el LLM evaluador.
* Todos los modelos muestran una mejora consistente, validando el uso de un *Juez* basado en LLM como mecanismo de refuerzo evaluativo.

---

### **Tabla 2. Evaluación Semántica y de Severidad por Modelo**

Esta tabla presenta los resultados de dos dimensiones de evaluación para modelos clínicos de diagnóstico diferencial: **similitud semántica** (medida por SAPBERT) y **distancia de severidad clínica** (evaluada por GPT-4-O como *JUEZ*). Se reportan las medias y desviaciones estándar para cada métrica.

| Modelo   | Evaluación Semántica (Media) | Evaluación Semántica (Desv. Est.) | Evaluación de Severidad (Media) | Evaluación de Severidad (Desv. Est.) |
| -------- | ---------------------------- | --------------------------------- | ------------------------------- | ------------------------------------ |
| Sakura   | 0.6521                       | 0.2171                            | 0.2813                          | 0.2076                               |
| OpenBio  | 0.6439                       | 0.2696                            | 0.3979                          | 0.3109                               |
| JonSnow  | 0.5971                       | 0.2450                            | 0.5052                          | 0.3640                               |
| MedGemma | 0.5782                       | 0.2294                            | 0.4318                          | 0.2118                               |

**Notas analíticas:**

* Una **mayor puntuación semántica** indica que el modelo produce diagnósticos diferenciales más cercanos al diagnóstico objetivo en términos de significado médico.
* Una **menor puntuación de severidad** representa una menor distancia respecto a la severidad del diagnóstico objetivo (idealmente 0).
* El modelo **Sakura** obtiene el mejor balance general, con alta similitud semántica y baja distancia de severidad.
* **JonSnow**, en cambio, tiene la peor media en severidad (0.5052), lo que sugiere una tendencia a generar diagnósticos clínicamente más discordantes respecto al nivel de gravedad esperado.
| Modelo   | **SEMÁNTICA** · ICD-10-BERT (%) | **SEMÁNTICA** · LLMAAJ (%) | **SEMÁNTICA** · BERT (Media) | **SEMÁNTICA** · BERT (Desv. Est.) | **SEVERIDAD** · Dist. Abs. (Media) | **SEVERIDAD** · Dist. Abs. (Desv. Est.) | 
| -------- | ------------------------------- | ------------------------- | --------------------------- | -------------------------------- | ---------------------------------- | --------------------------------------- | 
| 4o       | 78.78                           | 81.70 †                   | ―                           | ―                                | 0.183*                             | 0.817*                                  |
| 4-1      | 74.22                           | 77.50 †                   | ―                           | ―                                | 0.225*                             | 0.775*                                  |
| o1       | 76.33                           | 84.10 †                   | ―                           | ―                                | 0.159*                             | 0.841*                                  |
| o3       | 80.46                           | 84.30 †                   | ―                           | ―                                | 0.157*                             | 0.843*                                  |
| o3-pro   | 79.89                           | 83.90 †                   | ―                           | ―                                | 0.161*                             | 0.839*                                  |
| Sakura   | ―                               | ―                         | 0.6521                      | 0.2171                           | 0.2813                             | 0.2076                                  |
| OpenBio  | ―                               | ―                         | 0.6439                      | 0.2696                           | 0.3979                             | 0.3109                                  |
| JonSnow  | ―                               | ―                         | 0.5971                      | 0.2450                           | 0.5052                             | 0.3640                                  |
| MedGemma | ―                               | ―                         | 0.5782                      | 0.2294                           | 0.4318                             | 0.2118                                  |


*Los valores marcados con asterisco corresponden a una "severidad artificial" derivada como (1 - Rendimiento) y Rendimiento, respectivamente. Se incluyen únicamente a modo ilustrativo.*


# DxGPT New About

### 1. ¿Por qué dicen que DxGPT es mejor que ChatGPT?

Según el texto, DxGPT se considera superior a una IA generalista como ChatGPT para el diagnóstico clínico por las siguientes razones clave:

*   **Enfoque Especializado vs. Generalista:** DxGPT es una herramienta **diseñada por y para el entorno clínico**. A diferencia de ChatGPT que da respuestas abiertas y libres, DxGPT ofrece un **análisis estructurado de cinco hipótesis diagnósticas**, que están razonadas y clasificadas.
*   **Marco de Control Médico:** Funciona dentro de un **marco de control médico** que garantiza que los resultados sean relevantes y seguros, aplicando la IA avanzada en un entorno supervisado y orientado al diagnóstico.
*   **Claridad y Utilidad Clínica:** La interfaz y los resultados están optimizados para la toma de decisiones médicas. Cada hipótesis incluye **síntomas compatibles e incompatibles explícitos**, lo que aporta una gran claridad.
*   **Reducción de Sesgos:** Ayuda a disminuir el **sesgo de disponibilidad** (la tendencia a pensar en diagnósticos comunes), asegurando que no se olviden enfermedades raras.
*   **Consistencia y Validación:** El mismo caso siempre recibe un análisis igual de riguroso, y la herramienta se valida continuamente con un **benchmark clínico propio (DxGPT-bench)**.

En resumen, DxGPT no es un chatbot para conversar, sino una **herramienta de apoyo cognitivo** que transforma la información en un formato estructurado, validado y directamente útil para un médico, ahorrándole tiempo y mejorando la calidad del razonamiento clínico.

---

### 2. Todo sobre la sección de Benchmarking (Datos, Resultados, etc.)

Aquí tienes un resumen completo de toda la información relacionada con el benchmarking de DxGPT.

#### **¿Qué es DxGPT-bench?**

Es el **banco de pruebas propio** de la Fundación 29, creado para evaluar con el máximo rigor la precisión de los modelos de IA en escenarios clínicos realistas. Se compone de un conjunto de **997 casos clínicos**, estadísticamente representativo y diverso, para garantizar que la evaluación de DxGPT se base en evidencia sólida y transparente.

#### **Creación y Datos del Benchmark (DxGPT-bench)**

*   **Fuentes de los Datos:** Se utilizaron cinco fuentes complementarias para crear una base de datos inicial de más de 9.500 casos:
    1.  Casos de **urgencias reales** del sistema hospitalario HM de Madrid.
    2.  Datos de formación de preguntas tipo **USMLE** para exámenes médicos.
    3.  Casos sintéticos de **enfermedades raras** del sistema RAMEDIS.
    4.  Registros médicos reales de **pacientes ucranianos** con patologías poco frecuentes.
    5.  Casos de la comunidad médica general.

*   **Procesamiento y Selección:**
    1.  **Normalización:** Se corrigieron inconsistencias en los datos.
    2.  **Filtrado:** Se usó GPT-4 para eliminar casos no evaluables (por ejemplo, aquellos con diagnósticos implícitos).
    3.  **Etiquetado:** Todos los diagnósticos se codificaron con el estándar **ICD-10** para medir la diversidad.
    4.  **Selección Final:** De los más de 9.500 casos, se utilizó un **algoritmo de selección estratificada** para escoger los **997 casos finales**. Este algoritmo maximiza la cobertura de diagnósticos diferentes y garantiza una distribución uniforme de complejidad y severidad.

#### **Validación Estadística del Benchmark**

*   **¿Por qué 997 casos y no los 9.583 originales?**
    La reducción fue intencionada para **eliminar la redundancia** (por ejemplo, había 2.373 casos de "dolor"). La muestra final de 997 casos (el 10.4% del total) es mucho más eficiente, ya que logra capturar:
    *   El **31.8% de los diagnósticos únicos** (908 códigos ICD-10).
    *   El **43.3% de los síntomas únicos** (1.210).
    De este modo, se preserva la diversidad esencial a un coste computacional razonable.

*   **¿Es suficiente para evaluar la dificultad?**
    Sí. La selección estratificada asegura que el benchmark represente todo el espectro de dificultad, desde casos simples (C0/S0) hasta los más complejos y severos (C10/S10).

#### **Proceso de Evaluación y Resultados**

*   **¿Cómo se evalúa un modelo?**
    El proceso es automático y sigue estos pasos:
    1.  El modelo de IA genera diagnósticos para cada uno de los 997 casos.
    2.  Estos diagnósticos se comparan con el diagnóstico correcto usando **similitud semántica** (con un modelo BERT clínico o un LLM de razonamiento).
    3.  Se asigna un **nivel de severidad** a cada diagnóstico.
    4.  Se calcula la **distancia entre las severidades** del diagnóstico generado y el correcto.

*   **Resultados y Validación Clínica**
    Sí, DxGPT ha sido validado en un estudio clínico.
    *   **Estudio:** Realizado por el **Hospital Sant Joan de Déu**.
    *   **Resultado Principal:** El estudio concluyó que DxGPT alcanza una **precisión diagnóstica comparable a la de expertos clínicos**.
    *   **Publicación:** El trabajo se ha publicado como preprint y está en revisión por pares. Se puede leer en: **Evaluación de la utilidad clínica de DxGPT | medRxiv**.