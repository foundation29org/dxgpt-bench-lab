# Final Datasets Overview

This repository contains 7 medical case datasets that have been processed and normalized for diagnostic analysis. Each dataset contains structured medical cases with associated diagnoses, complexity ratings (C0-C10), and unique identifiers. The datasets total 9,677 medical cases covering a wide range of clinical scenarios.

## Dataset Descriptions

• **MedBulltes5op & MedQAUSMLE4op**: These educational datasets contain 141 and 7,075 medical cases respectively, derived from medical board examinations and educational resources. Each case has exactly one diagnosis and covers a broad spectrum of complexity levels, making them valuable for training and evaluation purposes.

• **RAMEDIS**: A specialized dataset of 852 cases focused on rare diseases and complex medical conditions. Cases can have up to 7 diagnoses (average 1.6 per case), with complexity heavily weighted towards higher levels (C7-C10), reflecting the challenging nature of rare disease diagnosis.

• **URGTorre**: An emergency medicine dataset containing 1,398 cases from urgent care settings. Cases include up to 5 diagnoses (average 1.4 per case) and additional metadata, with complexity distribution centered around moderate levels (C3-C6), typical of emergency department presentations.

• **Rare Synthetic**: A curated collection of 200 synthetic cases designed to represent uncommon medical scenarios. Each case has a single diagnosis with complexity concentrated in the C5-C7 range, providing balanced coverage of moderately complex rare conditions.

• **Ukrainian**: A small specialized dataset of 9 multi-diagnosis cases (average 2.9 diagnoses per case) with varied complexity levels, likely representing region-specific medical cases or conditions.

• **New England Medical Journal**: A minimal dataset of 2 cases extracted from medical literature, both at complexity level C5, serving as reference examples of well-documented clinical presentations.

![Flujo de datos](../../../bench/__conceptual-model-and-research-notes/imgs/etl_visualized_as_sankey_at_20250708.png)

# SERVE.py - Guía del Algoritmo de Selección de Casos

## 📋 ¿Qué hace este script?

El script `serve.py` crea datasets de evaluación de alta calidad seleccionando casos médicos de múltiples fuentes de datos. Su objetivo es maximizar la diversidad diagnóstica mientras respeta reglas específicas de muestreo.

## 🎯 Objetivo Principal

Crear un dataset balanceado que:
- Incluya casos de múltiples fuentes
- Maximice la diversidad de diagnósticos
- Represente diferentes capítulos ICD-10
- Respete límites configurados por fuente

## 📁 Fuentes de Datos

El script trabaja con estos archivos JSON:
- **B**: `medbulltes5op.json` - Casos médicos generales
- **Q**: `medqausmle4op.json` - Preguntas médicas de USMLE
- **R**: `ramedis.json` - Enfermedades raras
- **S**: `rare_synthetic.json` - Casos sintéticos de enfermedades raras
- **U**: `ukranian.json` - Casos de Ucrania
- **T**: `urgtorre.json` - Casos de urgencias
- **J**: `new_england_med_journal.json` - Casos del NEJM

## ⚙️ Configuración Principal

```python
TARGET_DATASET_SIZE = 150  # Número total de casos deseados

SAMPLING_RULES = {
    'U': {'min': 'all', 'max': 'all'},  # Incluir TODOS los casos ucranianos
    'R': {'min': 50, 'max': 100},       # Mínimo 50, máximo 100 de RAMEDIS
    'T': {'min': 0, 'max': 50},         # Máximo 50 de urgencias
    'S': {'min': 0, 'max': 25},         # Máximo 25 sintéticos
    'B': {'min': None, 'max': None},    # Sin restricciones
    'Q': {'min': None, 'max': None},    # Sin restricciones
}
```

## 🔄 Fases del Algoritmo

### **FASE 0: Carga y Preparación**

1. **Lee todos los archivos JSON** disponibles
2. **Extrae información clave** de cada caso:
   - ID y fuente (primera letra del ID)
   - Complejidad (C1-C10)
   - Severidad (S1-S10)
   - Códigos ICD-10 de diagnósticos
   - Capítulos ICD-10 (primera letra del código)

### **FASE 1: Selección Prioritaria**

Esta fase garantiza que se cumplan los requisitos mínimos:

1. **Regla 'all'**: 
   - Si una fuente tiene `min: 'all'`, incluye TODOS sus casos
   - Ejemplo: Los 9 casos ucranianos siempre se incluyen

2. **Regla 'min'**:
   - Selecciona los mejores N casos de esa fuente
   - Prioriza casos que:
     - Introducen nuevos capítulos ICD-10
     - Tienen alta complejidad
     - Son multi-diagnóstico

### **FASE 2: Llenado Iterativo Inteligente**

Completa el dataset hasta alcanzar el tamaño objetivo:

1. **Para cada caso restante calcula una puntuación**:
   ```
   Puntuación = 5 × (nuevos capítulos ICD-10)
              + 3 × (bonus fuente subrepresentada)
              + 2 × (complejidad/10)
              + 1 × (si es multi-diagnóstico)
              + 0.5 × (severidad/10)
   ```

2. **Selecciona el caso con mayor puntuación** que:
   - No exceda el límite máximo de su fuente
   - Introduzca al menos un diagnóstico nuevo
   - No esté ya incluido

3. **Repite hasta**:
   - Alcanzar el tamaño objetivo
   - O no quedar candidatos válidos

### **FASE 3: Generación de Reportes**

Crea tres archivos en `/served/YYYYMMDD_HHMMSS_cN/`:
- `aggregated_*.json`: El dataset seleccionado
- `report_*.json`: Estadísticas detalladas (ordenadas alfabéticamente)
- `report_*.txt`: Reporte legible para humanos

## 📊 Métricas de Diversidad

El algoritmo optimiza para:

1. **Diversidad de Capítulos ICD-10**: Intenta cubrir A-Z
2. **Balance de Fuentes**: Evita sobre-representación
3. **Diagnósticos Únicos**: Maximiza códigos ICD-10 diferentes
4. **Complejidad Variada**: Incluye casos simples y complejos

## 🎲 Decisiones Clave del Algoritmo

### ¿Por qué prioriza nuevos capítulos ICD-10?
- Garantiza cobertura amplia de tipos de enfermedades
- Evita sesgo hacia enfermedades comunes

### ¿Por qué el bonus de fuente subrepresentada?
- Mantiene balance entre fuentes
- Evita que una fuente grande domine el dataset

### ¿Por qué considera la complejidad?
- Los casos complejos son más desafiantes para evaluar
- Pero también incluye casos simples para balance

### ¿Qué pasa si no puede alcanzar el tamaño objetivo?
- Se detiene cuando no hay más candidatos válidos
- Reporta el número real de casos seleccionados
- Común cuando hay muchas restricciones 'max'

## 💡 Ejemplo de Uso

Para crear un dataset de 500 casos con 100% de RAMEDIS:
```python
TARGET_DATASET_SIZE = 500
SAMPLING_RULES = {
    'R': {'min': 'all', 'max': 'all'},
    # ... resto con min: 0, max: 0
}
```

Para crear un dataset balanceado de 200 casos:
```python
TARGET_DATASET_SIZE = 200
# Dejar todas las reglas con min: None, max: None
```

## 📁 Estructura de Salida

```
/served/
  └── 20250702_160145_c150/         # Timestamp + número de casos
      ├── aggregated_*.json          # Dataset final
      ├── report_*.json              # Métricas en JSON
      └── report_*.txt               # Reporte legible
```

## 🔍 Interpretación del Reporte

- **Composición por fuente**: Muestra balance y cumplimiento de reglas
- **Capítulos ICD-10**: Indica cobertura diagnóstica (ideal: 22/22)
- **Diagnósticos únicos**: Mayor número = mayor diversidad
- **Casos multi-diagnóstico**: Indica complejidad del dataset

## ⚠️ Limitaciones

1. **Dependencia de ICD-10**: Casos sin códigos ICD-10 son menos prioritarios
2. **Sesgo de disponibilidad**: Fuentes pequeñas pueden agotarse rápido
3. **Trade-offs**: Maximizar diversidad puede sacrificar representatividad

## 🚀 Conclusión

El algoritmo balancea múltiples objetivos:
- Cumplir restricciones estrictas (min/max)
- Maximizar diversidad diagnóstica
- Mantener balance entre fuentes
- Incluir casos de diferente complejidad

Esto resulta en datasets de evaluación robustos y diversos, ideales para probar sistemas de diagnóstico médico.