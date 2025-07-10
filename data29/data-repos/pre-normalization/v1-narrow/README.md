# v1-narrow - Datasets Médicos Iniciales

Pipeline ETL para normalización de datasets médicos de emergencias y casos académicos.

## Datasets Fuente

1. **URG_TORRE_DIC_IAGEN**: 6,272 casos de urgencias hospitalarias
2. **Ramebench Paper Collection**: Casos médicos académicos de múltiples fuentes (MME, LIRICAL, HMS, RAMEDIS, PUMCH_ADM)

## Flujo de Transformaciones

### RAMEDIS (v2 → v7)

#### v2: Consolidación de fuentes
- Fusión de 5 CSVs separados
- Adición de columna 'origin' para trazabilidad
- Renumeración secuencial de IDs

#### v3: Normalización de diagnósticos
- Limpieza de texto (split por "also known as", "or", "due to")
- Formato semicolon-separated para múltiples nombres
- Eliminación de duplicados y puntuación

#### v4: Asignación de complejidad
- Sistema P0-P10 usando GPT-4o
- P0-P2: Simple | P3-P4: Moderado | P5-P6: Significativo | P7-P8: Alto | P9-P10: Extremo
- Procesamiento batch (5 casos/vez)

#### v6: Filtrado de diagnósticos confirmados
- Retención solo de casos con diagnóstico real
- Generación de estadísticas de selección

#### v7: Integración ICD10
- Adición de códigos ICD10 a diagnósticos individuales
- Migración de códigos diagnósticos (OMIM/ORPHA/CCRD) a campo 'ooc'
- Conversión CSV → JSON

### URG Torre (v2 → v8)

#### v2: Agregación de criticidad
- Indicadores: +death, +critical, +pediatric, +severity
- Eliminación de columna variant

#### v3: Estandarización
- diagnosis → golden-diagnosis
- Mapeo jerárquico ICD10 (category/block/sub_block)
- Selección de código diagnóstico más largo

#### v4: Limpieza con LLM
- Extracción de terminología médica limpia
- Eliminación de jerga ("unspecified", "other")
- Combinación diagnóstico original + ICD10

#### v5: Complejidad P0-P10
- Mismo sistema que RAMEDIS
- Batch processing con GPT-4o

#### v7-v8: Reestructuración final
- Filtrado de diagnósticos reales
- Reubicación de códigos ICD10

## Categorización URG (6,272 casos)

- **test_death**: 7 casos (fallecimientos)
- **test_critical**: 43 casos (UCI >2-3 días)
- **test_severe**: 82 casos (1 día UCI o >5 días planta)
- **test_pediatrics**: 1,654 casos (edad <15 años)
- **moderate**: 4,486 casos (resto no-severos)

## Estructura Final

```json
{
  "case": "Narrativa clínica estructurada",
  "golden_diagnosis": "Diagnóstico ground truth",
  "complexity": "P0-P10",
  "icd10_code": "Código clasificación internacional",
  "metadata": "origin, severity, etc."
}
```

## Características Clave

- Trazabilidad completa con archivos before/after
- Procesamiento batch con manejo de errores
- Validación incremental
- UTF-8 encoding consistente