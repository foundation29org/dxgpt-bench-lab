# Pipeline v3 - Full LLM

Pipeline de evaluación semántica para comparar la precisión diagnóstica de diferentes modelos de IA (GPT-4o, O1, O3, O3-Pro) en casos médicos utilizando LLMs.

## Descripción General

Este pipeline implementa un sistema de evaluación que compara semánticamente los diagnósticos generados por diferentes modelos de IA contra diagnósticos de referencia (ground truth), utilizando GPT-4o-summary como evaluador semántico.

## Componentes Principales

### 1. `llm-semantic-evaluator.py`

Script principal que realiza la evaluación semántica de diagnósticos médicos.

**Funcionalidades:**
- Carga archivos JSON con diagnósticos de diferentes modelos
- Extrae listas GDX (Gold standard DiaGnosis X - diagnóstico de referencia) y DDX (Differential Diagnosis X - diagnósticos del modelo)
- Evalúa la similitud semántica entre diagnósticos usando GPT-4o-summary
- Implementa un sistema de puntuación de confianza detallado (escala 1-10)
- Utiliza procesamiento por lotes (batching) del sistema `utils.llm` para eficiencia
- Genera logs detallados con marcas de tiempo (`O3DIFF_evaluation_{timestamp}.txt`)
- Incluye fallback a evaluación individual si el batch falla

**Sistema de Puntuación Detallado:**
- `1`: Not confident at all (términos completamente diferentes, error grave si se usan indistintamente)
- `2`: Very little confidence (términos mayormente diferentes con relación mínima)
- `3`: Little confidence (términos relacionados pero con diferencias significativas)
- `4`: Somewhat unsure (términos con alguna relación pero diferencias importantes)
- `5`: Moderately confident (términos relacionados pero con matices distintos)
- `6`: Quite confident (términos similares con algunas diferencias menores)
- `7`: Confident (términos muy similares, intercambiables en muchos contextos)
- `8`: Very confident (términos casi idénticos con diferencias sutiles)
- `9`: Extremely confident (términos prácticamente idénticos)
- `10`: Completely confident (términos completamente intercambiables)

**Ejemplos de Evaluación:**
- 'Left circumflex artery ischemia' ↔ 'Acute lateral ST‑elevation myocardial infarction' = 10/10
- 'Systemic Lupus Erythematosus with Libman-Sacks endocarditis' ↔ 'Systemic lupus erythematosus' = 9/10
- 'IgA deficiency' ↔ 'Anaphylactic transfusion reaction due to selective IgA deficiency' = 8/10

### 2. Estructura de los JSON de Diagnósticos

Los archivos `diagnoses-{modelo}.json` tienen una estructura anidada donde las claves son los nombres de los diagnósticos:

```json
{
  "section_letter": [
    {
      "case_id": "identificador_único",
      "case_description": "descripción del escenario clínico",
      "gdx_details": {
        "Nombre del diagnóstico 1": {
          "origin": "fuente del diagnóstico",
          "code": "código médico",
          "classification": "sistema de clasificación (ICD10/ORPHA/OMIM/SNOMED)"
        },
        "Nombre del diagnóstico 2": {
          "origin": "fuente",
          "code": "código",
          "classification": "sistema"
        }
      },
      "ddx_details": {
        "Diagnóstico diferencial 1": {
          "origin": "modelo",
          "code": "código médico si está disponible",
          "classification": "sistema de clasificación"
        },
        "Diagnóstico diferencial 2": {
          "origin": "modelo",
          "code": "código",
          "classification": "sistema"
        }
      }
    }
  ]
}
```

**Campos Clave:**
- `gdx_details`: Diccionario donde las claves son los nombres de los diagnósticos de referencia (ground truth)
- `ddx_details`: Diccionario donde las claves son los nombres de los diagnósticos diferenciales generados por el modelo
- El script extrae las claves de estos diccionarios para obtener las listas de diagnósticos a comparar

### 3. `consolidated_results.txt`

Archivo que consolida los resultados de evaluación de todos los modelos con un formato detallado.

**Estructura del archivo:**
- Encabezado con timestamp de generación
- Casos organizados con puntuaciones agregadas entre corchetes [o3-pro, o3, o1, 4o]
- Para cada caso muestra:
  - Lista GDX completa (diagnósticos de referencia)
  - Para cada modelo: mejor coincidencia GDX, lista DDX completa con diagnóstico principal marcado con **

**Formato real del archivo:**
```
Case J1 - [10, 10, 10, 10]
  GDX: [
    Hepatocellular Carcinoma
    Metabolic dysfunction–associated steatohepatitis (MASH) (IIII)
  ]
  o3-pro:
    Best match GDX: Metabolic dysfunction–associated steatohepatitis (MASH) (2)
    DDX list: [
      **METABOLIC DYSFUNCTION–ASSOCIATED STEATOHEPATITIS (MASH)**
      Cirrhosis secondary to MASH
      Hepatocellular carcinoma
      Metabolic syndrome
      Post-transplant diabetes mellitus
    ]
  o3:
    Best match GDX: Metabolic dysfunction–associated steatohepatitis (MASH) (2)
    DDX list: [
      **METABOLIC DYSFUNCTION–ASSOCIATED STEATOHEPATITIS (MASH)**
      Cirrhosis secondary to MASH
      Hepatocellular carcinoma
      Post-transplant diabetes mellitus
      Atrial arrhythmia requiring pacemaker implantation
    ]
```

**Interpretación:**
- Los números entre corchetes (ej: [10, 10, 10, 10]) representan las puntuaciones de confianza para cada modelo en orden
- El diagnóstico con ** es el que mejor coincide con el GDX según la evaluación semántica
- Se muestra la lista completa de DDX para entender el contexto diagnóstico de cada modelo

## Flujo de Evaluación

1. **Extracción**: Lee archivos JSON y extrae listas GDX y DDX usando las claves de los diccionarios
2. **Comparación por pares**: Crea todas las combinaciones posibles GDX-DDX para cada caso
3. **Evaluación semántica**: 
   - Intenta primero procesamiento por lotes usando `llm.generate()` con `batch_items`
   - Si falla, recurre a evaluación individual de cada par
   - Utiliza GPT-4o-summary con temperatura 0.3 para consistencia
4. **Selección de mejor coincidencia**: Identifica el par GDX-DDX con mayor puntuación
5. **Agregación**: Calcula puntuaciones promedio por modelo y genera logs detallados

### Prompt de Evaluación Semántica

El pipeline utiliza el siguiente prompt para evaluar la similitud entre diagnósticos. Nota importante: este prompt está diseñado para procesamiento por lotes con el sistema `utils.llm`, por lo que no contiene placeholders para casos individuales:

```
For each pair of diagnostic terms below, rate how confident you would feel using them interchangeably in a clinical setting.

Scale from 1 to 10:
- 1 = Not confident at all (completely different terms, using one for the other would be a serious error)
- 2 = Very little confidence (mostly different terms with minimal relationship)
- 3 = Little confidence (related terms but with significant differences)
- 4 = Somewhat unsure (terms with some relationship but important differences)
- 5 = Moderately confident (related terms but with distinct nuances)
- 6 = Quite confident (similar terms with some minor differences)
- 7 = Confident (very similar terms, interchangeable in many contexts)
- 8 = Very confident (almost identical terms with subtle differences)
- 9 = Extremely confident (practically identical terms)
- 10 = Completely confident (terms that are fully interchangeable)

Examples:
- 'Left circumflex artery ischemia' <-> 'Acute lateral ST‑elevation myocardial infarction (left circumflex artery occlusion)' = 10/10 (because DDX includes GDX)
- 'Ectopic pregnancy due to pelvic inflammatory disease' <-> 'Ruptured ectopic pregnancy' = 9/10 (it captures the same core condition but misses the causal detail while adding a severity aspect)
- 'Systemic Lupus Erythematosus (SLE) with Libman-Sacks endocarditis' <-> 'Systemic lupus erythematosus' = 9/10 (captures the primary diagnosis but omits a key associated complication)
- 'IgA deficiency' <-> 'Anaphylactic transfusion reaction due to selective IgA deficiency' = 8/10 (represents the underlying condition but not the clinical consequence that arises from it)
- 'Ischemic colitis with transmural infarction' <-> 'Ischemic colitis' = 9/10 (includes the core condition but excludes the extent of tissue damage)

For each pair, respond with:
- GDX: [the GDX diagnosis]
- DDX: [the DDX diagnosis]  
- Score: [number from 1 to 10]
```

**Procesamiento por lotes**: El sistema `utils.llm` inyecta automáticamente los pares de diagnósticos en el prompt usando el parámetro `batch_items`, permitiendo evaluar múltiples pares en una sola llamada al LLM para mayor eficiencia.

## Uso

```bash
python llm-semantic-evaluator.py
```

**Configuración en el script:**
```python
PROCESS_4O = True
PROCESS_O1 = True
PROCESS_O3_PRO = False
PROCESS_O3 = False
```

El script genera:
- Logs detallados en `O3DIFF_evaluation_{timestamp}.txt` con análisis caso por caso
- Resumen con puntuaciones promedio por modelo
- Información de progreso en consola

## Integración con el Sistema

- Utiliza el sistema de LLM unificado de `utils.llm.get_llm()`
- Soporta batching nativo para procesamiento eficiente de múltiples pares
- Maneja errores gracefully con fallback a procesamiento individual
- Los archivos JSON de diagnósticos deben estar en el mismo directorio que el script

## Propósito

Este pipeline permite:
- **Benchmarking cuantitativo**: Comparar capacidades diagnósticas de diferentes modelos de IA
- **Análisis semántico**: Evaluar qué tan bien los diagnósticos diferenciales se alinean con ground truth
- **Validación clínica**: Entender si los modelos capturan la esencia de los diagnósticos más allá de coincidencias exactas
- **Mejora iterativa**: Identificar fortalezas y debilidades de cada modelo en contextos médicos específicos