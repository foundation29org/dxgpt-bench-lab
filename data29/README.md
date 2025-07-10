# Data29 - Procesamiento y Gestión de Datos Médicos 📊

Este módulo es el núcleo de procesamiento de datos del proyecto, donde casos médicos de múltiples fuentes se transforman mediante pipelines ETL en datasets estructurados y validados para evaluación de modelos de IA médica.

## 🎯 Propósito

Gestionar el ciclo completo de datos médicos: desde fuentes heterogéneas hasta datasets normalizados listos para benchmarking, garantizando trazabilidad, calidad y diversidad.

## 🏗️ Estructura

```
data29/
├── data-repos/
│   ├── pre-normalization/      # Datos crudos y proceso ETL
│   │   ├── v1-narrow/         # ETL para RAMEDIS y URGTorre
│   │   ├── v2-wide/           # ETL para MedBulltes, MedQA-USMLE
│   │   └── v3-merge/          # Fusión y deduplicación
│   └── post-normalization/    # Datasets finales procesados
│       ├── *.json             # 7 datasets normalizados
│       └── serve.py           # Servidor de datasets con diversidad
```

## 🔄 Pipeline ETL

### Etapa 1: Pre-normalización
Transformación progresiva de datos crudos mediante pipelines versionados:

- **v1-narrow**: Procesamiento de casos clínicos tradicionales (RAMEDIS, URGTorre)
- **v2-wide**: Procesamiento de datasets educativos y sintéticos (MedBulltes, MedQA-USMLE)
- **v3-merge**: Fusión inteligente y eliminación de duplicados

Cada pipeline incluye:
- Normalización de formatos
- Asignación de complejidad (C0-C10)
- Mapeo a códigos ICD-10
- Evaluación de severidad

### Etapa 2: Post-normalización
Datasets finales estructurados con esquema unificado:
- ID único por fuente
- Descripción del caso clínico
- Diagnósticos con severidad
- Nivel de complejidad

## 🚀 Servidor de Datasets

`serve.py` permite crear subconjuntos balanceados con:
- Control de tamaño total
- Reglas de muestreo por fuente
- Maximización de diversidad (capítulos ICD-10, complejidad, severidad)
- Generación de reportes y visualizaciones

Ejemplo de uso:
```bash
python serve.py  # Genera dataset de 450 casos con diversidad óptima
```

## 📊 Datasets Disponibles

7 fuentes normalizadas totalizando ~9,600 casos médicos:
- Casos clínicos reales anonimizados
- Casos educativos de exámenes médicos
- Casos sintéticos para enfermedades raras
- Casos de urgencias hospitalarias

## 🔗 Integración

Los datasets procesados aquí alimentan directamente los experimentos de benchmarking en `bench/`.