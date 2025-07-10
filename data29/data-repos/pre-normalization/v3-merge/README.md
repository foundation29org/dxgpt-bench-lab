# v3-merge - Consolidación y Reducción Inteligente

Pipeline de fusión y reducción de datasets médicos de 9,583 a 997 casos representativos.

## Flujo de Datos

### Datasets de Entrada
- **MedBulletes5op**: 308 casos
- **MedQA-USMLE-4op**: 12,724 casos  
- **ProCheck**: 7 casos
- **URG_TORRE**: 6,272 casos
- **Ramebench**: 1,195 casos

### Proceso de Fusión (`merge_datasets.py`)
**Total fusionado**: 9,583 casos

**Distribución**:
- ausmle4: 7,075 casos (73.8%)
- urgtorre: 1,398 casos (14.6%)
- ramedis: 961 casos (10.0%)
- bulltes5: 141 casos (1.5%)
- procheck: 8 casos (0.1%)

**Campos estandarizados**:
```json
{
  "id": "identificador único",
  "case": "descripción clínica",
  "complexity": "P0-P10",
  "diagnoses": [{
    "name": "nombre diagnóstico",
    "severity": "S0-S10",
    "icd10": "código ICD-10"
  }],
  "dataset": "origen"
}
```

## Reducción en 2 Etapas

### Etapa 1: Filtro de Unicidad (`v1-uniques.py`)
**Objetivo**: Una sola aparición por enfermedad

**Algoritmo**:
1. Agrupa enfermedades por frecuencia (n=1, n=2, etc.)
2. Selecciona un caso representativo por enfermedad
3. Prioriza datasets minoritarios: procheck > ramedis > bulltes5 > urgtorre > ausmle4

### Etapa 2: Balanceo por Capítulos ICD-10 (`v2-crived.py`)
**Objetivo**: 997 casos con representación equilibrada

**Sistema de Deuda**:
- Meta: 10 casos/dataset/capítulo (máx 50/capítulo)
- Si un dataset no puede cumplir cuota, transfiere deuda al siguiente
- Procesamiento de minoritario a mayoritario

**Selección Equidistante**:
1. Ordena casos alfabéticamente por ICD-10
2. Divide en segmentos iguales
3. Selecciona casos en puntos medios para diversidad

## Resultados Clave

### Reducción: 9,583 → 997 casos (89.6%)

### Métricas Preservadas:
- **Cobertura ICD-10**: Todos los capítulos representados
- **Diversidad de Enfermedades**: Sin sobre-representación
- **Balance de Complejidad**: P0-P10 distribuido
- **Espectro de Severidad**: S0-S10 mantenido
- **Representación de Datasets**: Prioridad a minoritarios

## Archivos Clave

```
merge/
├── all.json          # 9,583 casos fusionados
├── all_997.json      # Dataset final reducido
└── merge_summary.json # Estadísticas de fusión

reduce/
├── v1-uniques.json   # Etapa 1: filtro unicidad
├── v2-crived.json    # Etapa 2: balanceo ICD-10
└── explained.md      # Explicación detallada
```

## Principios de Diseño

1. **Prioridad Minoritaria**: Garantiza representación de datasets pequeños
2. **Unicidad de Enfermedades**: Evita sesgo hacia condiciones comunes
3. **Balance por Capítulos**: Cobertura completa del espectro médico
4. **Selección Equidistante**: Maximiza diversidad intra-capítulo
5. **Sistema de Deuda**: Distribución justa cuando hay casos limitados

Pipeline diseñado para crear un dataset de evaluación compacto pero representativo, manteniendo la diversidad clínica y la calidad de los datos originales.