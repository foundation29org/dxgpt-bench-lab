# Guía de Evaluación - Pipeline V4

Esta guía explica paso a paso cómo ejecutar la evaluación completa de diagnósticos diferenciales usando el Pipeline V4.

## 📋 Tabla de Contenidos

1. [Prerequisitos](#prerequisitos)
2. [Configuración Inicial](#configuración-inicial)
3. [Pasos de la Evaluación](#pasos-de-la-evaluación)
4. [Configuración del Pipeline](#configuración-del-pipeline)
5. [Ejecución](#ejecución)
6. [Interpretación de Resultados](#interpretación-de-resultados)
7. [Troubleshooting](#troubleshooting)

---

## Prerequisitos

### 1. Variables de Entorno

Crea un archivo `.env` en la **raíz del proyecto** (`C:\repo\DxGPT\eval\.env`) con las siguientes variables:

```env
# Azure Text Analytics (para atribución de códigos médicos)
AZURE_LANGUAGE_ENDPOINT=https://tu-endpoint.cognitiveservices.azure.com
AZURE_LANGUAGE_KEY=tu_clave_azure

# Azure OpenAI (para modelos LLM)
AZURE_OPENAI_ENDPOINT=https://tu-endpoint.openai.azure.com
AZURE_OPENAI_API_KEY=tu_clave_azure_openai
AZURE_OPENAI_API_VERSION=2024-02-15-preview

# Google Gemini (para modelos Gemini)
GOOGLE_GENAI_API_KEY=tu_clave_gemini
# O alternativamente:
GEMINI_API_KEY=tu_clave_gemini

# Azure Translator (opcional, para traducción de casos)
AZURE_TRANSLATOR_KEY=tu_clave_translator
AZURE_TRANSLATOR_ENDPOINT=https://api.cognitive.microsofttranslator.com
AZURE_TRANSLATOR_REGION=tu_region

# Hugging Face (para BERT similarity)
HF_TOKEN=tu_token_huggingface
SAPBERT_ENDPOINT_URL=tu_endpoint_sapbert
```

### 2. Dependencias Python

Instala las dependencias necesarias:

```bash
pip install -r requirements.txt
```

O usando `uv`:

```bash
uv pip install -r requirements.txt
```

### 3. Dataset

Asegúrate de tener el dataset en la ruta especificada en `config.yaml`. Por defecto:
- `bench/datasets/all_275.json`  
  (también disponible `all_150.json` para pruebas más rápidas)

---

## Configuración Inicial

### 1. Navegar al Directorio del Pipeline

```bash
cd "bench/pipelines/pipeline_v4 - fork/main"
```

### 2. Validar Configuración

Antes de ejecutar, valida que todo esté correcto:

```bash
py validate.py
```

Esto verificará:
- ✅ Variables de entorno configuradas
- ✅ Archivos de configuración válidos
- ✅ Dataset accesible
- ✅ Dependencias instaladas

---

## Pasos de la Evaluación

El pipeline ejecuta **3 pasos principales** en secuencia:

### **PASO 1: Emulator (Generación de DDX)**

**¿Qué hace?**
- Lee cada caso del dataset
- Envía el caso al modelo LLM configurado (GPT-5, Gemini, etc.)
- El LLM genera diagnósticos diferenciales (DDX) basados en el caso clínico
- Opcionalmente traduce el caso si `TRANSLATE_CASE.ENABLED: true`

**Entrada:**
- Dataset JSON con casos clínicos (`all_150.json`)

**Salida:**
- Archivo JSON con DDX generados por el LLM
- Ubicación: `output/<dataset>/<prompt>/<model>/ddxs_from_emulator.json`

**Tiempo estimado:**
- Depende del modelo y número de casos
- Gemini 2.5 Pro: ~75 segundos para 150 casos (con tier 1)
- GPT-5.1: ~13-14 segundos por caso

---

### **PASO 2: Medical Labeler (Atribución de Códigos Médicos)**

**¿Qué hace?**
- Toma los DDX generados en el Paso 1
- Para cada diagnóstico diferencial, llama a Azure Text Analytics
- Azure identifica entidades médicas y extrae códigos:
  - **ICD-10**: Códigos de clasificación internacional
  - **SNOMED**: Terminología clínica estandarizada
  - **OMIM**: Base de datos de genes y fenotipos
  - **ORPHA**: Enfermedades raras

**Entrada:**
- Archivo JSON con DDX del Paso 1

**Salida:**
- Archivo JSON con DDX + códigos médicos asignados
- Ubicación: `output/<dataset>/<prompt>/<model>/ddxs_from_labeler.json`

**Tiempo estimado:**
- ~5-10 minutos para 150 casos (depende de Azure Text Analytics)

**Nota:** El archivo del emulator se elimina automáticamente después de este paso.

---

### **PASO 3: Evaluator (Evaluación de Calidad)**

**¿Qué hace?**
- Compara los DDX generados con los diagnósticos de referencia (GDX)
- Usa **3 métodos de evaluación** en orden de prioridad:

  1. **SNOMED Match**: Coincidencia exacta de códigos SNOMED
  2. **ICD-10 Match**: Coincidencia de códigos ICD-10 (exacta, padre, hijo, hermano)
  3. **Semantic Match**: Similaridad semántica usando BERT + juicio de LLM

**Criterios de aceptación:**
- **BERT_AUTOCONFIRM_THRESHOLD** (0.90): Si BERT score ≥ 0.90, acepta automáticamente (no llama al LLM)
- **BERT_ACCEPTANCE_THRESHOLD** (0.80): Si BERT score ≥ 0.80, requiere confirmación del LLM juez
- Si BERT < 0.80, el **LLM juez** decide si hay match (ver sección [Modelo Juez](#modelo-juez-judge_model) más abajo)

**Entrada:**
- Archivo JSON con DDX + códigos del Paso 2
- Dataset original con GDX (diagnósticos de referencia)

**Salida:**
- `evaluation.log`: Log detallado del proceso
- `evaluation_details.txt`: Detalles de cada caso evaluado
- `summary.json`: Resumen estadístico de resultados
- Ubicación: `output/<dataset>/<prompt>/<model>/<timestamp>/`

**Tiempo estimado:**
- ~5-10 minutos para 150 casos

---

## Configuración del Pipeline

Edita el archivo `config.yaml` para personalizar la evaluación:

### Modelo LLM

```yaml
DXGPT_EMULATOR:
  MODEL: "gemini-2.5-pro"  # Opciones: "gpt-5.1", "gpt-5-mini", "gemini-2.5-pro", "gemini-2.0-flash", etc.
```

**Modelos disponibles:**
- **Azure OpenAI**: `gpt-5.1`, `gpt-5-mini`, `gpt-4o-summary`, `o3-mini`
- **Google Gemini**: `gemini-2.5-pro`, `gemini-2.0-flash`, `gemini-3-pro-preview`

### Parámetros del Modelo

```yaml
PARAMS:
  temperature: 0.1          # Creatividad (0.0 = determinista, 1.0 = creativo)
  max_tokens: 12000         # Máximo de tokens en la respuesta
  reasoning_effort: "low"   # Para O3/GPT-5: "low", "medium", "high"
  thinking_level: "low"     # Para Gemini 2.5/3: "low", "medium", "high"
```

### Traducción de Casos

```yaml
TRANSLATE_CASE:
  ENABLED: true             # Activar/desactivar traducción
  TARGET_LANGUAGE: "en"     # Idioma objetivo ("en" = inglés, "es" = español)
```

**¿Cuándo usar traducción?**
- Si tu dataset tiene casos en español y quieres evaluar el modelo en inglés
- Puede mejorar el rendimiento si el modelo está mejor entrenado en inglés

### Thresholds de Evaluación

```yaml
EVALUATOR:
  BERT_ACCEPTANCE_THRESHOLD: 0.80   # Score mínimo para considerar match (0.0-1.0)
  BERT_AUTOCONFIRM_THRESHOLD: 0.90 # Score para aceptar automáticamente (0.0-1.0)
  ENABLE_ICD10_PARENT_SEARCH: true  # Buscar códigos padre en ICD-10
  ENABLE_ICD10_SIBLING_SEARCH: true # Buscar códigos hermanos en ICD-10
  JUDGE_MODEL: null  # Modelo LLM para juzgar matches semánticos (opcional)
```

**Recomendaciones:**
- **BERT_ACCEPTANCE_THRESHOLD**: 0.80 es conservador, 0.70 es más permisivo
- **BERT_AUTOCONFIRM_THRESHOLD**: 0.90 es estándar, no cambiar a menos que haya problemas
- **JUDGE_MODEL**: Modelo usado para juzgar si hay match semántico cuando BERT < 0.80

### Modelo Juez (JUDGE_MODEL)

El modelo juez es el LLM que decide si hay match semántico cuando el score BERT está por debajo del threshold.

**Configuración recomendada** (según resultados de benchmark interno):

```yaml
EVALUATOR:
  JUDGE_MODEL: "gemini-2.5-pro"  # Mejor juez observado en los runs actuales
```

Puedes sustituirlo por cualquier modelo disponible:

```yaml
JUDGE_MODEL: "gemini-2.5-pro"  # Recomendado — más preciso en los benchmarks del equipo
JUDGE_MODEL: "normalcalls"     # GPT-4o (deployment Azure) — alternativa para entornos sin Gemini
JUDGE_MODEL: "gpt-5-mini"      # Más barato/rápido, algo menos preciso
# JUDGE_MODEL: null             # Lógica automática (ver nota abajo)
```

**Si no se especifica (JUDGE_MODEL: null), lógica automática del código:**
- Modelo **Gemini** evaluado → juez: **el mismo modelo Gemini**
- Modelo **OpenAI / o3 / gpt-5** evaluado → juez: **`normalcalls`** (GPT-4o en Azure)

> ⚠️ **Recomendación basada en experiencia:** fija siempre `JUDGE_MODEL` explícitamente en lugar de depender de la lógica automática. Así los resultados son comparables entre runs independientemente del modelo emulador.  
> **`gemini-2.5-pro` como juez** ha mostrado los mejores resultados en los benchmarks del equipo (posición media más baja, mayor % de match).

**¿Importa el juez para la comparabilidad?**  
Sí, mucho. Dos runs con distinto juez no son directamente comparables aunque el resto de config sea igual. El juez afecta cuántos casos resuelve el paso semántico (en los runs actuales, ~34% de los casos pasan por el juez). Un juez más permisivo sube el % de match pero puede introducir falsos positivos.

### Control del Pipeline

```yaml
MAIN:
  SHOULD_EMULATE: true   # Paso 1: Generar DDX usando el modelo LLM
  SHOULD_LABEL: true     # Paso 2: Asignar códigos médicos usando Azure Text Analytics
  SHOULD_EVALUATE: true  # Paso 3: Evaluar DDX contra GDX
```

**Casos de uso comunes:**

| Escenario | SHOULD_EMULATE | SHOULD_LABEL | SHOULD_EVALUATE | Descripción |
|-----------|----------------|--------------|-----------------|-------------|
| **Ejecución completa desde cero** | `true` | `true` | `true` | Ejecuta todos los pasos (o omite estos valores) |
| **Solo re-evaluar** | `false` | `false` | `true` | Usa DDX y códigos existentes, solo re-evalúa |
| **Solo generar DDX** | `true` | `false` | `false` | Genera diagnósticos pero no asigna códigos ni evalúa |
| **Generar DDX + códigos** | `true` | `true` | `false` | Genera DDX y asigna códigos, sin evaluar |
| **Solo asignar códigos** | `false` | `true` | `false` | Si ya tienes DDX, solo asigna códigos médicos |

**Nota:** Si omites estos valores, el pipeline asume `true` por defecto (ejecuta todos los pasos).

---

## Ejecución

### Ejecución Completa

```bash
# Desde el directorio del pipeline
cd "bench/pipelines/pipeline_v4 - fork/main"

# Ejecutar pipeline completo
py main.py
```

### Ejecución por Pasos

Si quieres ejecutar pasos individuales:

```bash
# Solo Paso 1: Generar DDX
py emulator.py

# Solo Paso 2: Asignar códigos médicos
py medlabeler.py

# Solo Paso 3: Evaluar
py evaluator.py
```

### Gestión de Estado

El pipeline detecta automáticamente si ya existen resultados:

**Si existen DDX del Paso 1:**
```
⚠️  DDX results already exist at output/...

1. Re-run DDX generation (will overwrite existing results)
2. Continue with medical code labeling using existing DDX
3. ❌ Abort operation

Enter your choice (number):
```

**Si existen códigos del Paso 2:**
```
⚠️  Labeled results already exist at output/...

1. Re-run medical code labeling (will overwrite existing results)
2. Continue with evaluation using existing labeled results
3. ❌ Abort operation

Enter your choice (number):
```

---

## Interpretación de Resultados

### Archivo `summary.json`

Contiene las métricas principales:

```json
{
  "configuration": {
    "judge_model": "gemini-2.5-pro",
    "dataset_path": "bench/datasets/all_275.json",
    "timestamp": "2026-03-24T13:15:52.994256"
  },
  "global": {
    "total_cases": 275,
    "matched_cases": 271,
    "unmatched_cases": 4,
    "top_counts": {
      "P1": 212,
      "P2": 33,
      "P3": 22,
      "P4": 4
    },
    "resolution_method_counts": {
      "snomed_match": 121,
      "icd10_exact": 20,
      "icd10_sibling": 20,
      "bert_autoconfirm": 11,
      "bert_match": 4,
      "llm_judgment": 94
    },
    "average_position": 1.328,
    "final_score_percentage": 98.55
  }
}
```

**Métricas clave:**
- **final_score_percentage**: Porcentaje de casos donde se encontró el diagnóstico correcto (matched_cases/total)
- **matched_cases / unmatched_cases**: Conteo absoluto de casos con/sin match
- **P1, P2, P3, P4…**: Distribución de posiciones donde se encontró el diagnóstico correcto (P1 = mejor)
- **average_position**: Posición promedio del diagnóstico correcto entre los matched (menor es mejor)
- **resolution_method_counts**: Cómo se resolvió cada match (SNOMED, ICD10, BERT, LLM)

### Archivo `evaluation.log`

Log detallado con el resultado de cada caso:

```
[1/150] BERT_AUTOCONFIRM → GDX[1]: Systemic lupus erythematosus | DDX[1]: Systemic Lupus Erythematosus → **P1**
[2/150] SEMANTIC → NO_MATCH → **REJECTED**
[3/150] BERT_AUTOCONFIRM → GDX[1]: POEMS syndrome | DDX[2]: POEMS Syndrome → **P2**
```

**Códigos de resultado:**
- `BERT_AUTOCONFIRM`: Match encontrado con score BERT ≥ 0.90
- `BERT_ACCEPTANCE`: Match encontrado con score BERT ≥ 0.80 (confirmado por LLM)
- `SNOMED`: Match encontrado por código SNOMED
- `ICD10_EXACT`: Match encontrado por código ICD-10 exacto
- `ICD10_PARENT`: Match encontrado por código ICD-10 padre
- `ICD10_SIBLING`: Match encontrado por código ICD-10 hermano
- `SEMANTIC`: Match encontrado por similaridad semántica (LLM)
- `NO_MATCH` / `REJECTED`: No se encontró match

### Archivo `evaluation_details.txt`

Contiene información detallada de cada caso, incluyendo:
- GDX evaluado (diagnóstico de referencia)
- DDX generados (diagnósticos diferenciales)
- Scores BERT para cada DDX
- Traza completa de la evaluación (SNOMED → ICD-10 → Semantic)

---

## Troubleshooting

### Error: "Azure Language service credentials not found"

**Solución:**
- Verifica que el archivo `.env` esté en la raíz del proyecto (`C:\repo\DxGPT\eval\.env`)
- Verifica que las variables `AZURE_LANGUAGE_ENDPOINT` y `AZURE_LANGUAGE_KEY` estén configuradas

### Error: "Module not found"

**Solución:**
```bash
pip install -r requirements.txt
```

### Error: "429 RESOURCE_EXHAUSTED" (Gemini)

**Causa:** Límite de rate limit excedido

**Solución:**
- El código ya incluye delays automáticos según el modelo
- Para tier gratuito, los delays son más largos (30s para 2.5-pro)
- Con facturación (tier 1), los delays son más cortos (0.5s para 2.5-pro)
- Si persiste, aumenta el delay en `emulator.py`

### Muchos casos "REJECTED"

**Posibles causas:**
1. **Medlabeler no asignó códigos**: Revisa `medlabeler.log` para ver si Azure devolvió códigos
2. **Threshold de BERT demasiado estricto**: Considera bajar `BERT_ACCEPTANCE_THRESHOLD` a 0.70
3. **LLM demasiado conservador**: El LLM puede estar rechazando matches válidos

**Solución:**
- Revisa `evaluation_details.txt` para casos específicos
- Verifica los scores BERT en los casos rechazados
- Si los scores son altos (>0.65) pero no alcanzan el threshold, considera bajarlo

### El pipeline se detiene en medio de la ejecución

**Solución:**
- El pipeline guarda el estado automáticamente
- Puedes reanudar desde donde se quedó ejecutando `py main.py` de nuevo
- Elige la opción "Continue" cuando te pregunte sobre archivos existentes

### Resultados diferentes entre ejecuciones

**Causa:** Los modelos LLM pueden tener variabilidad incluso con `temperature: 0.1`

**Solución:**
- Esto es normal, especialmente con modelos no deterministas
- Para comparaciones justas, usa el mismo `seed` si el modelo lo soporta
- Ejecuta múltiples veces y promedia los resultados

---

## Estructura de Archivos de Salida

```
output/
└── all_275/                          # Nombre del dataset
    └── juanjo_classic_v2/            # Nombre del prompt
        └── gemini_2_5_pro_low_translated_en/  # Nombre del modelo (con sufijos)
            ├── juanjo_classic_v2___gemini_2_5_pro_low_translated_en___ddxs_from_labeler.json
            ├── juanjo_classic_v2___gemini_2_5_pro_low_translated_en___config.yaml
            ├── emulator.log
            ├── medlabeler.log
            └── 20251204151832/        # Timestamp de la evaluación
                ├── evaluation.log
                ├── evaluation_details.txt
                ├── summary.json
                └── juanjo_classic_v2___gemini_2_5_pro_low_translated_en___config.yaml
```

**Nota sobre nombres de modelos:**
- Si `TRANSLATE_CASE.ENABLED: true`, se añade el sufijo `_translated_<idioma>`
- Para Gemini se añade `_<thinking_level>` (ej: `_low`); para O3/GPT-5 se añade `_<reasoning_effort>` (ej: `_high`)
- Los espacios y caracteres especiales se reemplazan por `_`

**Nota sobre DDX translation (medlabeler):**  
El labeler envía los textos DDX directamente a Azure Text Analytics con `language="en"`. No hay traducción intermedia de DDX: se asume inglés dado que el emulador traduce el caso y el prompt es en inglés. La opción `TRANSLATE_CASE` del emulador no afecta al labeler.

---

**Última actualización:** Marzo 2026

## Consejos y Mejores Prácticas

1. **Empieza con un dataset pequeño**: Prueba con 5-10 casos antes de ejecutar 150
2. **Revisa los logs**: Los archivos `.log` contienen información valiosa sobre errores
3. **Compara modelos**: Ejecuta la misma configuración con diferentes modelos para comparar
4. **Guarda configuraciones**: El pipeline guarda automáticamente una copia del `config.yaml` en cada ejecución
5. **Monitorea los rate limits**: Especialmente con modelos Gemini en tier gratuito
6. **Revisa casos específicos**: Usa `evaluation_details.txt` para entender por qué un caso fue rechazado

---

## Siguiente Paso

Una vez completada la evaluación, puedes:
- Comparar resultados entre diferentes modelos
- Analizar casos específicos en `evaluation_details.txt`
- Ajustar thresholds si hay muchos falsos negativos/positivos
- Generar visualizaciones de los resultados

---

**Última actualización:** Marzo 2026