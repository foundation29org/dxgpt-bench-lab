# v2-wide - Expansión con Datasets Externos

Pipeline ETL estandarizado de 3 fases para procesamiento de datasets médicos de Q&A.

## Datasets Procesados

- **medbulltes5op**: MedBulletS - 5-option MCQ (HuggingFace)
- **medqausmle4op**: MedQA USMLE - 4-option MCQ (HuggingFace)
- **procheck**: Casos de enfermedades raras (socio interno)

## Pipeline de 3 Fases

### Fase 1: Reduct - Extracción y Estandarización
```python
# process_*.py
Input: JSONL crudo con Q&A médico
Process:
  - Extrae pregunta → "case"
  - Extrae respuesta → "diagnosis"
  - Normaliza espacios y saltos de línea
  - Asigna IDs secuenciales
Output: JSON estandarizado {id, case, diagnosis}
```

### Fase 2: Crive-Diagnosis - Clasificación
```python
# classify_medical_cases.py
Input: JSON de Fase 1
Process:
  - GPT-4o clasifica cada diagnóstico:
    * condition_diagnostic: Condiciones médicas, enfermedades, síndromes
    * clinical_action: Tratamientos, medicamentos, procedimientos, tests
  - Batch processing (5-20 items)
  - Resume capability para interrupciones
Output: JSON con campo 'classification' añadido
```

### Fase 3: Augmentation - Enriquecimiento
```python
# augment_diagnoses.py
Input: Solo casos 'condition_diagnostic' de Fase 2
Process:
  - GPT-4o enriquece cada diagnóstico con:
    * name: Nombre específico del diagnóstico
    * severity: S0 (leve) → S10 (severo)
    * icd10: Código ICD-10 más específico
    * complexity: C0 (simple) → C10 (complejo)
  - Batch processing con tracking
Output: JSON con diagnósticos enriquecidos
```

## Estructura de Directorios

```
dataset/
├── 0. raw/           # Datos originales sin procesar
├── 1. reduct/        # Datos estandarizados
├── 2. crive-diagnosis/   # Datos clasificados
└── 3. augmentation/  # Datos enriquecidos
```

## Características Clave

- **Estandarización**: Formato uniforme para todos los datasets
- **Procesamiento Incremental**: Cada fase construye sobre la anterior
- **Tolerancia a Fallos**: Capacidad de resumir procesamiento interrumpido
- **Eficiencia**: Batch processing para optimizar uso de LLM
- **Metadatos**: Estadísticas y logs de cada transformación

## Ejemplo de Transformación

```json
// Raw
{"question": "Patient with fever...", "answer": "Pneumonia"}

// Fase 1
{"id": 1, "case": "Patient with fever...", "diagnosis": "Pneumonia"}

// Fase 2
{"id": 1, "case": "...", "diagnosis": "Pneumonia", "classification": "condition_diagnostic"}

// Fase 3
{
  "id": 1,
  "case": "...",
  "diagnosis": {
    "name": "Pneumonia",
    "severity": 6,
    "icd10": "J18.9",
    "complexity": 4
  }
}
```

Pipeline diseñado para convertir datos Q&A médicos no estructurados en casos médicos estructurados, clasificados y enriquecidos para evaluación y benchmarking.