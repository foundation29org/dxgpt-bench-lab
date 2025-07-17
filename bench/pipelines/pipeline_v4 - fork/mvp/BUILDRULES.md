Entendido. Se ha refinado la especificación de los requisitos para incorporar el nivel de detalle solicitado en los archivos de salida, sin alterar la lógica de evaluación ni los demás requisitos originales. El foco principal del cambio está en el archivo `evaluation_details.txt` para que proporcione una traza completa y transparente de la evaluación de cada caso.

A continuación, se presenta el documento de requisitos completo y actualizado, conservando toda la información original y expandiendo la sección de archivos de salida según lo solicitado.

---

### **Objetivo:** Desarrollar un script en Python modular y configurable para evaluar la calidad de los diagnósticos diferenciales (DDX) generados por un modelo LLM, comparándolos con un diagnóstico de referencia (GDX), y generar informes detallados y un resumen de resultados.

---

### **1. Archivos y Estructura de Directorios**

*   **Script a crear:** `@bench/pipelines/pipeline_v4 - fork/02. Pipeline/pipeline-v4.py`
*   **Archivo de entrada:** `@bench/pipelines/pipeline_v4 - fork/00_diagnoses.json` (Contiene una lista de casos con `case_id`, `gdx_details` y `ddx_details`).
*   **Directorio de Salida:** El script **debe crear automáticamente un directorio llamado `output/`** en su misma ubicación si este no existe. Todos los archivos generados se guardarán aquí.
*   **Archivos de Salida (dentro de `output/`)**
    1.  `evaluation_details.txt`: Un reporte detallado con una entrada por cada caso evaluado.
    2.  `summary.json`: Un resumen agregado con el scoring final y estadísticas de la evaluación.
    3.  `evaluation.log`: Un archivo de registro con el progreso y los eventos clave del script.

---

### **2. Lógica de Evaluación por Caso (Jerarquía de Coincidencia Estricta)**

Para cada caso del JSON, se debe encontrar la mejor coincidencia para cada GDX contra la lista de 5 DDX. Si hay múltiples GDX, se repite el proceso para cada uno y **se selecciona el mejor resultado global** (la posición más baja, P1 > P2, etc.). La búsqueda de coincidencia debe seguir rigurosamente el siguiente orden:

**Paso 1: Coincidencia por Código SNOMED**
*   **Condición:** Si el GDX tiene un código SNOMED (lista no vacía).
*   **Acción:** Buscar una coincidencia exacta de código SNOMED en los DDX.
*   **Resultado:** Si se encuentra, se registra la posición (1-5), el método como **`SNOMED_MATCH`** y se finaliza la evaluación para ese GDX. Si no, se pasa al Paso 2.

**Paso 2: Coincidencia por Código ICD-10**
*   **Dependencia:** Usar la librería `@utils/icd10/`.
*   **Lógica Secuencial:**
    1.  **Coincidencia Exacta:** Buscar un código ICD-10 idéntico. Si se encuentra, registrar como **`ICD10_EXACT`**.
    2.  **Coincidencia de Hijos:** Si no, buscar un DDX cuyo código sea un "hijo" (más específico). Si se encuentra, registrar como **`ICD10_CHILD`**.
    3.  **Coincidencia de Padres (Configurable):** Si no, y si `ENABLE_ICD10_PARENT_SEARCH` es `True`, buscar un padre inmediato. Si se encuentra, registrar como **`ICD10_PARENT`**.
    4.  **Coincidencia de Hermanos (Configurable):** Si no, y si `ENABLE_ICD10_SIBLING_SEARCH` es `True`, buscar un "hermano". Si se encuentra, registrar como **`ICD10_SIBLING`**.
*   **Resultado:** Si se encuentra cualquier coincidencia en este paso, se registra la posición, el método específico y se finaliza. Si no, se pasa al Paso 3.

**Paso 3: Coincidencia Semántica (BERT y LLM)**
*   **Condición:** Se ejecuta solo si los Pasos 1 y 2 fallan.
*   **Lógica Secuencial:**
    *   **A. Análisis con BERT:**
        *   **Dependencia:** Usar la librería `@utils/bert/`.
        *   **Acción:** Calcular la similaridad de coseno entre el texto del GDX y el de cada uno de los 5 DDX. Identificar la puntuación más alta y su posición.
    *   **B. Decisión Post-BERT:**
        *   **Si la puntuación máxima de BERT es >= `BERT_AUTOCONFIRM_THRESHOLD`:** El resultado es concluyente. Se registra la posición, el método como **`BERT_AUTOCONFIRM`**, y la evaluación para este GDX **finaliza aquí (no se llama al LLM)**.
        *   **Si no**, se guarda temporalmente el mejor resultado de BERT (posición y score) y se procede al siguiente paso.
    *   **C. Juicio con LLM y Selección Final:**
        *   **Condición:** Se ejecuta solo si no hubo auto-confirmación por BERT.
        *   **Dependencia:** Usar `@utils/llm/` con el modelo `"gpt-4o-summary"`.
        *   **Acción:** Enviar un prompt al LLM preguntando cuál de los 5 DDX es clínicamente más intercambiable con el GDX, solicitando que devuelva la posición (1-5).
        *   **Selección Final:**
            *   Si el resultado guardado de BERT tiene un score >= `BERT_ACCEPTANCE_THRESHOLD`, se compara su posición con la devuelta por el LLM.
            *   Se elige la mejor de las dos posiciones (la más baja).
            *   Se registra el método correspondiente: **`BERT_MATCH`** si se eligió la posición de BERT, o **`LLM_JUDGMENT`** si se eligió la del LLM.

---

### **3. Descripción de Archivos de Salida (Requisito Ampliado)**

1.  **`output/evaluation_details.txt`**:
    *   **Formato:** Un archivo de texto que contiene una serie de objetos JSON, uno por cada caso evaluado, separados por `---`. Cada objeto JSON debe tener la siguiente estructura detallada:
    *   **Claves del Objeto JSON por Caso:**
        *   `case_id`: (string) El identificador único del caso.
        *   `gdx_details`: (list) Una copia de la lista de diagnósticos de referencia (GDX) originales del caso.
        *   `ddx_details`: (list) Una copia de la lista de diagnósticos diferenciales (DDX) originales del caso.
        *   `eval_details`: (object) Un objeto que contiene la traza completa y el resultado final de la evaluación para el caso.
    *   **Estructura Detallada de `eval_details`:**
        *   `best_match_found`: (boolean) `true` si se encontró una coincidencia para el caso, `false` en caso contrario.
        *   `final_resolution`: (object | null) Contiene la información del "par ganador" si se encontró una coincidencia. Es `null` si no hubo match.
            *   `position`: (string) La mejor posición encontrada ("P1", "P2", etc.).
            *   `method`: (string) El método final que resolvió el caso (`SNOMED_MATCH`, `LLM_JUDGMENT`, etc.).
            *   `value`: (string | number) El valor que justifica el match (el código SNOMED, la relación ICD-10, el score de BERT, etc.).
            *   **`matched_gdx`**: (object) El objeto completo del GDX que resultó en la mejor coincidencia.
            *   **`matched_ddx`**: (object) El objeto completo del DDX ganador.
        *   **`evaluation_trace`**: (list) Una lista que detalla el proceso de evaluación para **cada GDX** del caso. Cada elemento de la lista es un objeto con:
            *   `gdx_evaluated`: (object) El GDX específico que se está evaluando en esta traza.
            *   `snomed_check`: (object) El resultado de la comprobación por SNOMED.
                *   `status`: (string) "SUCCESS", "FAILED" o "SKIPPED".
                *   `details`: (string) Explicación del resultado. Ej: "SUCCESS: Found match with DDX at P1 (code: 59621000).", "FAILED: No SNOMED code from GDX list ['...'] found in any DDX.", "SKIPPED: GDX has no SNOMED codes."
            *   `icd10_check`: (object) El resultado de la comprobación por ICD-10.
                *   `status`: (string) "SUCCESS", "FAILED" o "SKIPPED".
                *   `details`: (string) Explicación. Ej: "SUCCESS: Found ICD10_CHILD match with DDX at P2 (J18 -> J18.0).", "FAILED: No ICD-10 relationship match found for GDX code 'J18'.", "SKIPPED: SNOMED match found first."
            *   `semantic_check`: (object) El resultado de la comprobación semántica.
                *   `status`: (string) "SUCCESS", "FAILED" o "SKIPPED".
                *   `details`: (string) Una explicación narrativa de la decisión final. Ej: "BERT score 0.92 >= autoconfirm threshold 0.90. LLM call skipped.", "BERT result at P2 (score: 0.88) was better than LLM's choice P3 and score was >= acceptance threshold 0.80."
                *   `bert_scores`: (list) Una lista de todos los scores de BERT calculados contra los 5 DDX. Ej: `[{"position": 2, "score": 0.92}, {"position": 4, "score": 0.88}, ...]`
                *   `bert_best`: (object) El mejor resultado de BERT. Ej: `{"position": 2, "score": 0.92}`
                *   `llm_judgment`: (object | null) El juicio del LLM si fue invocado. Ej: `{"position": 3}`.

2.  **`output/summary.json`**:
    *   Debe contener un único objeto JSON con las siguientes claves:
        *   `total_cases`: Número total de casos evaluados.
        *   `matched_cases`: Número de casos donde se encontró una coincidencia.
        *   `unmatched_cases`: Número de casos donde ningún método encontró coincidencia.
        *   `top_counts`: Un objeto con el recuento de aciertos en cada posición (`"P1": count, "P2": count, ..., "P5": count`).
        *   **`resolution_method_counts`**: Desglose de casos resueltos por cada método:
            *   `snomed_match`, `icd10_exact`, `icd10_child`, `icd10_parent`, `icd10_sibling`, `bert_autoconfirm`, `bert_match`, `llm_judgment`.
        *   `average_position`: La posición media de acierto (solo de los `matched_cases`).
        *   `final_score_percentage`: La posición media convertida a un porcentaje de acierto.

3.  **`output/evaluation.log`**:
    *   Un archivo de registro con el progreso y los eventos clave del script, siguiendo el formato especificado.

---

### **4. Requisitos del Script y Configuración**

*   **Modularidad:** Código organizado en funciones claras (`evaluate_snomed`, `evaluate_icd10`, `evaluate_semantic`, `run_evaluation`, etc.).
*   **Configuración Global (al principio del script):**
    ```python
    # Semantic Evaluation Thresholds
    BERT_ACCEPTANCE_THRESHOLD = 0.80  # Min score for a BERT result to be considered in the final comparison with LLM
    BERT_AUTOCONFIRM_THRESHOLD = 0.90 # Min score for a BERT result to be accepted without calling the LLM (must be >= BERT_ACCEPTANCE_THRESHOLD)
    
    # ICD-10 Search Configuration
    ENABLE_ICD10_PARENT_SEARCH = True
    ENABLE_ICD10_SIBLING_SEARCH = True
    ```

---

### **5. Requisitos Operacionales (Logging y Salida)**

*   **Gestión de Directorio:** El script debe usar `os.makedirs(..., exist_ok=True)` para crear el directorio `output/` sin errores si ya existe.
*   **Logging:**
    *   Configurar un logger que escriba tanto en la **consola** como en el archivo **`output/evaluation.log`**.
    *   El formato de log debe ser claro e informativo. Ejemplo:
        ```
        [2023-10-27 10:30:01] - INFO - --- Starting Evaluation Pipeline ---
        [2023-10-27 10:30:02] - INFO - Processing case 1/450 (Case ID: A01)... ▶️ Match found: SNOMED_MATCH. Position: P1.
        [2023-10-27 10:30:03] - INFO - Processing case 2/450 (Case ID: A05)... No code match. Running semantic analysis...
        [2023-10-27 10:30:03] - INFO - BERT score 0.92 exceeds threshold 0.90. Auto-confirming.
        [2023-10-27 10:30:03] - INFO - Processing case 2/450 (Case ID: A05)... ▶️ Match found: BERT_AUTOCONFIRM. Position: P2.
        [2023-10-27 10:30:04] - INFO - Processing case 3/450 (Case ID: B27)... No code match. Running semantic analysis...
        [2023-10-27 10:30:07] - INFO - BERT score 0.85. Awaiting LLM judgment...
        [2023-10-27 10:30:07] - INFO - Processing case 3/450 (Case ID: B27)... ▶️ Match found: LLM_JUDGMENT. Position: P3.
        [2023-10-27 10:31:00] - INFO - --- Evaluation Finished. Results saved to output/ directory. ---
        ```