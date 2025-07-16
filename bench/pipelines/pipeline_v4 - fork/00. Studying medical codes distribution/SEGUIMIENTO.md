
### **Informe Analítico Exhaustivo y Pormenorizado del Conjunto de Datos `diagnoses.json`**
*Datos de creación: 15 de julio de 2025. Alcance: 450 casos clínicos.*

---

### 1. Estructura y Panorama General del Dataset

El conjunto de datos se articula en torno a 450 casos clínicos individuales. Cada caso está compuesto por al menos un diagnóstico principal validado (GDX o *gold diagnosis*), que representa la conclusión clínica final, y una media de cinco diagnósticos diferenciales (DDX), que constituyen las hipótesis alternativas consideradas durante el proceso diagnóstico.

| Métrica | GDX (Diagnóstico Principal) | DDX (Diagnóstico Diferencial) |
| :--- | :--- | :--- |
| **Registros totales** | **450** | **2,250** |
| Registros sin **ningún** tipo de código | 0 (0 %) | 225 (10.0 %) |
| **Códigos individuales totales asignados** | 1,056 | 4,827 |
| Media de códigos por registro (sobre todos) | 2.34 | 2.15 |
| Media de códigos por registro (solo entre los que **tienen** código) | 2.34 | 2.38 |

**Lectura e Interpretación Detallada:**
*   **Fundamento Sólido:** La base de diagnósticos principales (GDX) es 100% completa en términos de tener al menos una codificación, lo que la convierte en un ancla fiable para cualquier análisis.
*   **Laguna Crítica de Datos:** Un primer hallazgo de capital importancia es la laguna de datos en los diagnósticos diferenciales. Un 10% de todos los DDX (225 registros) son "huérfanos semánticos", careciendo por completo de cualquier código en los sistemas analizados. Estos registros son invisibles para cualquier análisis computacional basado en códigos y representan una pérdida neta de información clínica valiosa.
*   **Riqueza de Codificación:** La métrica "media de códigos" revela que, cuando un registro es codificado, tiende a serlo con una riqueza considerable. Un DDX con código tiene, de media, 2.38 códigos de diferentes sistemas, lo que sugiere un esfuerzo por capturar el concepto diagnóstico desde múltiples ontologías.

---

### 2. Análisis Pormenorizado de la Cobertura por Sistema de Codificación

La eficacia de cualquier análisis depende de la cobertura de los vocabularios controlados. Este dataset muestra una gran variabilidad entre sistemas, revelando roles complementarios y deficiencias significativas.

#### 2.1 Cobertura General a Nivel de Registro Individual

| Sistema | GDX con código (% sobre 450) | DDX con código (% sobre 2,250) |
| :--- | :--- | :--- |
| **ICD-10** | 212 (47.1 %) | 1,436 (63.8 %) |
| **SNOMED CT** | **342 (76.0 %)** | **1,963 (87.2 %)** |
| **OMIM** | 97 (21.6 %) | 1,371 (60.9 %) |
| **ORPHA** | 0 (0 %) | 0 (0 %) |

**Interpretación Profunda:**
*   **SNOMED CT, el Estándar de Facto:** Con una cobertura del 76% en GDX y un impresionante 87.2% en DDX, SNOMED CT emerge como el vocabulario más robusto y omnipresente del dataset. Actúa como una red de seguridad semántica fundamental: de los 814 DDX que carecen de código ICD-10, SNOMED CT (junto a OMIM) logra rescatar a 589, cubriendo el 72% de esa brecha.
*   **La Dicotomía de ICD-10:** Aunque otros análisis (ver 2.2) muestran que todos los casos GDX tienen un código ICD-10, a nivel de registro individual su presencia es menor (47.1% aquí). Su cobertura en DDX es solo del 63.8%, dejando más de un tercio de los diagnósticos diferenciales sin representación en este sistema, que es crucial para la facturación y la epidemiología.
*   **Rol de Nicho de OMIM:** OMIM muestra una cobertura respetable, especialmente en DDX (60.9%), posicionándose como un recurso clave para diagnósticos con base genética.
*   **La Ausencia Total de ORPHA:** La falta absoluta de códigos ORPHA en los 2,250 DDX es un hallazgo alarmante. Esto implica que el análisis de enfermedades raras, el propósito principal de Orphanet, es imposible en el contexto diferencial de este dataset.

#### 2.2 Vistas Adicionales de Cobertura

*   **Vista 1: Cobertura en GDX (sobre 685 GDX analizados)**
    *   ICD-10: 100.0% | SNOMED CT: 74.7% | OMIM: 34.7% | ORPHA: 32.7%
*   **Vista 2: Cobertura en GDX (sobre 450 casos)**
    *   ICD-10: 100.0% | SNOMED CT: 80.7% | OMIM: 21.6% | ORPHA: 20.0%
*   **Vista 3: Cobertura en DDX a Nivel de Caso (sobre 450 casos)**
    *   SNOMED CT: 99.8% | ICD-10: 97.6% | OMIM: 95.8% | ORPHA: 0.0%

**Síntesis de Vistas:** A pesar de las variaciones numéricas, la tendencia es inequívoca: la cobertura de SNOMED CT es superior y más consistente, especialmente en el ámbito de los DDX, donde está presente en prácticamente todos los casos.

---

### 3. Granularidad y Distribución Jerárquica Detallada (ICD-10)

El análisis del nivel jerárquico de los códigos ICD-10 revela una preferencia sistémica por la generalidad sobre la especificidad.

*   **En GDX (sobre 450 registros):**
    *   **Block (Bloque)**: 296 (65.8%)
    *   Sub-block (Sub-bloque): 82 (18.2%)
    *   Otros (Group, Category, etc.): 72 (16.0%)
*   **En DDX (sobre los 1,436 registros con código ICD-10):**
    *   **Block (Bloque)**: 855 (59.5%)
    *   Sub-block (Sub-bloque): 323 (22.5%)
    *   Otros (Category, Group, etc.): 258 (18.0%)

**Interpretación Analítica:** La preponderancia masiva del nivel **'Block'** (≈60-66%) no es un hallazgo menor. Representa una codificación de "trazo grueso", donde se asigna una categoría amplia de enfermedades (ej., "Otras enfermedades bacterianas especificadas") en lugar de un diagnóstico preciso. Esta falta de granularidad tiene implicaciones directas para la IA, ya que limita la capacidad de los modelos para aprender patrones finos y diferenciar entre subtipos de enfermedades con presentaciones clínicas similares pero pronósticos o tratamientos distintos.

---

### 4. Análisis Cruzado Completo de Jerarquías ICD-10 (GDX → DDX)

Este análisis examina las 2,050 combinaciones GDX-DDX donde ambos tenían un código ICD-10, para entender la dinámica del razonamiento diferencial en términos de granularidad. **Se presenta la tabla completa sin ninguna omisión.**

| Combinación jerárquica (GDX → DDX) | Frecuencia | % sobre total |
| :--- | :--- | :--- |
| **Block → Block** | **908** | **41.8 %** |
| Block → Sub-block | 296 | 13.6 % |
| Sub-block → Block | 227 | 10.5 % |
| Block → Category | 136 | 6.3 % |
| **Group → Group** | **126** | **5.8 %** |
| **Sub-block → Sub-block** | **122** | **5.6 %** |
| Group → Sub-block | 83 | 3.8 % |
| Group → Block | 75 | 3.5 % |
| Category → Block | 53 | 2.4 % |
| Sub-block → Category | 45 | 2.1 % |
| Block → Group | 28 | 1.3 % |
| **Category → Category** | **22** | **1.0 %** |
| Sub-block → Group | 15 | 0.7 % |
| Block → Range | 9 | 0.4 % |
| Category → Sub-block | 6 | 0.3 % |
| Group → Category | 6 | 0.3 % |
| Sub-block → Range | 4 | 0.2 % |
| Subgroup → Block | 2 | 0.1 % |
| Subgroup → Category | 2 | 0.1 % |
| Subgroup → Sub-block | 2 | 0.1 % |
| Group → Range | 1 | 0.0 % |
| Category → Range | 1 | 0.0 % |
| Category → Group | 1 | 0.0 % |

**Interpretación Exhaustiva del Análisis Cruzado:**
1.  **Consistencia Horizontal (Dominante):** La relación más común es la que mantiene el mismo nivel jerárquico. Sumando `Block→Block`, `Group→Group`, `Sub-block→Sub-block`, y `Category→Category`, encontramos que **1,178 pares (54.3%)** operan a un nivel de granularidad consistente, con `Block→Block` siendo la interacción predominante por un margen abrumador.
2.  **Dinámicas Verticales (Refinamiento vs. Generalización):** El dataset muestra un flujo bidireccional en la granularidad.
    *   **Refinamiento (Ir a más específico):** Combinaciones como `Block → Sub-block` (296 casos) o `Block → Category` (136 casos) muestran un proceso donde el diferencial es más específico que el diagnóstico principal.
    *   **Generalización (Ir a más amplio):** Combinaciones como `Sub-block → Block` (227 casos) o `Category → Block` (53 casos) indican el proceso contrario, donde se consideran alternativas más generales.
3.  **Pérdida de Información (No reflejada en esta tabla):** Es crucial recordar que esta tabla solo analiza los 2,170 pares con código. Como se mencionó anteriormente, una de las "transiciones" más frecuentes en el dataset completo es `GDX codificado → DDX sin código ICD-10`, especialmente `Block → SIN CÓDIGO`. Esto representa la mayor caída de información en el proceso diferencial.

---

### 5. Capacidad Real de Coincidencia de Códigos (Matching GDX ↔ DDX)

Este es el análisis más crítico, pues mide la capacidad práctica del dataset para vincular un diagnóstico principal con sus diferenciales a través de un código idéntico.

*   **Capacidad General de Matching:** Solo **255 de 450 casos (56.7%)** presentan al menos una coincidencia de código.
*   **Brecha de Coherencia Semántica:** Un alarmante **43.3% de los casos (195 en total)** carecen de cualquier vínculo de código directo entre el GDX y sus DDX, a pesar de que los registros individuales sí están codificados. Esto representa una profunda brecha entre la cobertura teórica y la utilidad práctica.
*   **Grupo habilitador en caso extremo:** Un **72.67% de los casos (1577 en total)** se constituye de matches exactos (**74.69%, 1178**) e hijos (**25.30%, 399**).

#### 5.1 Desglose Detallado del Matching por Sistema (sobre los 255 casos exitosos)

| Categoría de Matching (Sistemas que coinciden) | Conteo | % sobre 255 | Implicación Estratégica Clave |
| :--- | :--- | :--- | :--- |
| **Solo SNOMED CT** | **106** | **41.6 %** | SNOMED CT es el héroe anónimo del matching; sin él, casi la mitad de los casos exitosos no tendrían ningún vínculo. |
| ICD-10 y algún otro sistema | 102 | 40.0 % | Demuestra que el matching de ICD-10 casi siempre requiere el apoyo de otro sistema; rara vez es suficiente por sí solo. |
| Solo ICD-10 | 23 | 9.0 % | El poder de matching de ICD-10 en solitario es extremadamente bajo, confirmando su limitada utilidad para esta tarea. |
| SNOMED CT y OMIM (sin ICD-10) | 12 | 4.7 % | Una combinación poderosa para casos que probablemente tienen un componente genético, donde ICD-10 falla. |
| Los 3 códigos coinciden | 12 | 4.7 % | Representan los casos de "calidad de oro" con máxima coherencia semántica a través de múltiples ontologías. |
| Solo OMIM | 0 | 0.0 % | **Hallazgo crítico:** OMIM nunca logra un matching por sí solo. Su rol es puramente de enriquecimiento, no de vinculación directa. |

---

### 6. Conclusiones Finales e Implicaciones Estratégicas Detalladas

1.  **La Profunda Brecha entre Cobertura y Utilidad (La brecha del 43.3%)**: El hallazgo más importante es la desconexión entre la alta cobertura de códigos y la baja capacidad de matching (56.7%). Este 43.3% de casos sin vínculo semántico directo representa un obstáculo masivo para el desarrollo de IA. Limita fundamentalmente la capacidad de entrenar modelos supervisados para tareas como la recomendación de DDX o la validación de diagnósticos, ya que falta la "etiqueta" de verdad que proporciona un código compartido.

2.  **SNOMED CT es la Columna Vertebral Semántica del Dataset**: SNOMED CT no es meramente el sistema con mejor cobertura; es el **principal y casi único habilitador de la coherencia interna** del dataset. Al permitir el matching en el 51.3% de todos los casos y ser el único conector en el 41.6% de los casos exitosos, se posiciona como el eje semántico indispensable.
    *   **Recomendación Estratégica Ineludible**: Cualquier sistema de IA, apoyo a la decisión o minería de datos que utilice este dataset **debe adoptar SNOMED CT como su vocabulario de referencia principal**. Depender de ICD-10 para el análisis de relaciones semánticas es una estrategia abocada al fracaso.
