# Datasets - Datos Procesados para Evaluación 🗂️

Este directorio contiene los datasets médicos procesados que se utilizan para evaluar modelos de diagnóstico diferencial. Los datos provienen del pipeline de procesamiento `data29` y están organizados según diferentes propósitos de testing y validación.

## 📊 Datasets Disponibles

### Validación de Funcionalidad
- **`ukranian.json`** (21KB, 437 casos) - Dataset pequeño de prueba para validación on/off de funcionalidad de pipelines

### Testing de Funciones de Producción
- **`largest_summarized_demo.json`** (201KB, 4147 líneas) - Para probar reacción del prompt dxgpt ante extensión de prompt
- **`largest_extended.json`** (621KB, 4047 líneas) - Para validar función resumidora en producción

### Datasets Principales (Módulo Reciente)
- **`all_150.json`** (304KB, 6818 líneas) - Dataset diverso de 150 casos seleccionados
- **`all_250.json`** (449KB, 10297 líneas) - Dataset diverso de 250 casos seleccionados  
- **`all_450.json`** (728KB, 14651 líneas) - Dataset diverso completo de 450 casos seleccionados

## 🔄 Pipeline de Generación

### Datasets Principales (all_150, all_250, all_450)
Estos datasets fueron generados con un módulo más reciente que:
1. Parte de un conjunto final de **9,582 casos** obtenidos del procesamiento completo
2. Aplica criterios de diversidad para crear subsets representativos
3. Optimiza la distribución de casos para benchmarking efectivo

### Datasets de Testing Específico
- Los datasets `largest_*` sirven para probar funcionalidades específicas del prompt dxgpt
- El dataset `ukranian` es ideal para testing rápido de funcionalidad pipeline

## 🎯 Uso Recomendado

- **Desarrollo/Debug**: `ukranian.json`
- **Testing de Prompts**: `largest_summarized_demo.json`, `largest_extended.json`
- **Evaluación Completa**: `all_150.json`, `all_250.json`, `all_450.json`
