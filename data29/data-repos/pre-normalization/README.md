# Pre-Normalization Data Repository

Este directorio contiene todo el proceso de ETL (Extract, Transform, Load) para la normalización de datasets médicos, con un historial completo y detallado de cada transformación realizada.

## Estructura General

### v1-narrow/
Contiene el trabajo inicial de normalización de datasets médicos:
- **Marzo 2025**: Trabajo realizado por Carlos Bermejo con los datasets originales de RAMEDIS
- **Junio 2025**: Extensiones y mejoras realizadas posteriormente, incluyendo URG Torre

**Características principales:**
- Procesamiento de múltiples fuentes de datos médicos (RAMEDIS, HMS, LIRICAL, MME, PUMCH_ADM, URG Torre)
- ETL organizado por fechas (25.05 y 25.06) con transformaciones incrementales
- Cada transformación está versionada (v2, v3, v4, etc.) con archivos `before` y `after`
- Documentación detallada de cambios en archivos `changes.txt`
- Visualizaciones y análisis estadísticos en `current-data/visualisations/`

### v2-wide/
Expansión del proyecto para incluir datasets adicionales:

**Nuevos datasets incorporados:**
- **medbulltes5op**: MedBulletS – 5-option MCQ de HuggingFace
- **medqausmle4op**: MedQA USMLE – 4-option MCQ de HuggingFace  
- **procheck**: Casos de enfermedades raras de socio interno (MD con 20 años de experiencia)

**Flujo ETL estandarizado:**
1. `0. raw/`: Datos originales sin procesar
2. `1. reduct/`: Reducción de columnas y limpieza inicial
3. `2. crive-diagnosis/`: Clasificación y filtrado de diagnósticos reales
4. `3. augmentation/`: Enriquecimiento con complejidad, severidad y mapeo ICD-10

### v3-merge/
Consolidación y unificación de todos los datasets:
- Fusión de datasets de v1-narrow y v2-wide
- Reducción de duplicados y casos únicos
- Estadísticas finales (997 casos únicos vs 10,538 totales)
- Diagrama Sankey documentando el flujo de datos

## Aspectos Destacados

### Trazabilidad Completa
**CADA paso de ETL está registrado** con:
- Scripts de transformación (`run.py`, `changes.py`)
- Estados antes/después de cada cambio
- Logs de transformación en JSON
- Documentación de decisiones y criterios

### Versionado Sistemático
Ejemplo de nomenclatura:
- `ramedis-v2-added-origin-column/`
- `ramedis-v3-formatting-diagnosis-names/`
- `ramedis-v4-setting-complexity/`
- `ramedis-v6-filtering-actual-diagnosis/`
- `ramedis-v7-icd10sing/`

### Transformaciones Documentadas
Cada carpeta de transformación contiene:
- `before.csv/json`: Estado inicial
- `after.csv/json`: Estado final
- `run.py`: Script de transformación
- `changes.txt`: Descripción detallada de cambios
- Logs adicionales cuando aplica

## Dataset Origins & ETL Synopsis

### 1. Datasets Fuente
| Alias | Nombre Completo | Proveedor / URL |
|-------|-----------------|-----------------|
| `medbullet5op` | MedBulletS – 5-option MCQ | https://huggingface.co/datasets/JesseLiu/medbulltes5op |
| `medqa_usmle4op` | MedQA USMLE – 4-option MCQ | https://huggingface.co/datasets/GBaker/MedQA-USMLE-4-options |
| `procheck` | ProCheck rare-disease cases | Socio interno (MD, 20 años exp.) |

ProCheck cadencia: piloto de 5 casos (`example_split`) + 1 caso raro curado/semana (`case1`, `case2`, …).

### 2. Flujo ETL (MedBulletS & MedQA)
1. Poda de columnas – mantener `{case_text, diagnosis}`; eliminar `explanation`, distractores, keywords
2. Filtro de diagnósticos (GPT-4o) – retener `row_type == condition_diagnosis`; descartar prompts de tratamiento/medicación (`clinical_action`)
3. Augmentación – etiquetar `case_complexity`, `diagnosis_severity`, y mapear diagnóstico → ICD-10 (utils.icd10.ICD10Taxonomy)

### 3. Alineación ProCheck
Misma lógica ETL; bajo volumen permite verificaciones manuales ocasionales vía ChatGPT/Claude.

### 4. Estado
ETL completo – datasets listos para evaluación y benchmarking downstream.

## Importancia del Registro

Lo más valioso de este repositorio no son solo los datos finales, sino el **historial completo de transformaciones**. Cada decisión, cada cambio, cada criterio de filtrado está documentado y es reproducible. Esto permite:

- Auditar decisiones de normalización
- Reproducir exactamente cualquier versión del dataset
- Entender la evolución y refinamiento de los datos
- Validar la calidad y consistencia del proceso ETL

El repositorio representa meses de trabajo meticuloso en limpieza, normalización y enriquecimiento de datos médicos, con un enfoque en mantener la trazabilidad completa del proceso.