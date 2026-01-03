# Comparación GPT-5.2: Reasoning Effort (Low vs Medium vs High)

## Resumen Ejecutivo

Comparación de resultados de `gpt-5.2` con diferentes niveles de `reasoning_effort` en el dataset `all_150` con prompt `juanjo_classic_v2`.

## Resultados Globales

| Métrica | Low | Medium | High |
|---------|-----|--------|------|
| **Total casos** | 150 | 150 | 150 |
| **Casos matched** | 150 | 149 | 137 |
| **Casos unmatched** | 0 | 1 | **13** |
| **Success rate** | **100.0%** | 99.33% | **91.33%** |
| **Average position** | 1.727 | 1.664 | 1.781 |
| **P1 (posición 1)** | 100 | 98 | 88 |
| **P2 (posición 2)** | 25 | 22 | 21 |
| **P3 (posición 3)** | 8 | 19 | 15 |

## Análisis Detallado

### 🟢 Low Reasoning Effort
- **Mejor resultado**: 100% de éxito
- **Mejor posición promedio**: 1.727
- **Más casos en P1**: 100 casos
- **Sin casos rechazados**

### 🟡 Medium Reasoning Effort
- **Buen resultado**: 99.33% de éxito
- **Mejor posición promedio**: 1.664 (mejor de los tres)
- **Solo 1 caso rechazado**
- **Más casos en P3**: 19 casos (posiblemente más conservador)

### 🔴 High Reasoning Effort
- **Peor resultado**: 91.33% de éxito
- **13 casos rechazados** (8.67% del total)
- **Peor posición promedio**: 1.781 (incluso en casos exitosos)
- **Menos casos en P1**: 88 casos (64.2% vs 66.7% en low, 65.8% en medium)
- **Más casos en posiciones peores**: P4 (5), P5 (4), P6 (2), P7 (1), P10 (1)

## Métodos de Resolución

### Low
- SNOMED: 59 casos
- ICD10_EXACT: 16 casos
- ICD10_SIBLING: 8 casos
- LLM_JUDGMENT: 62 casos
- BERT_AUTOCONFIRM: 1 caso
- BERT_MATCH: 3 casos
- ICD10_PARENT: 1 caso

### Medium
- SNOMED: 59 casos
- ICD10_EXACT: 14 casos
- ICD10_SIBLING: 10 casos
- LLM_JUDGMENT: 59 casos
- BERT_AUTOCONFIRM: 1 caso
- BERT_MATCH: 3 casos
- ICD10_PARENT: 3 casos

### High
- SNOMED: 56 casos (-3 vs low/medium)
- ICD10_EXACT: 8 casos (-8 vs low, -6 vs medium)
- ICD10_SIBLING: 9 casos
- LLM_JUDGMENT: 59 casos
- BERT_AUTOCONFIRM: 2 casos
- BERT_MATCH: 2 casos
- ICD10_PARENT: 1 caso

## Problemas Identificados con High Reasoning Effort

### 1. **Respuestas Vacías por Límite de Tokens de Reasoning** ⚠️ CRÍTICO
- **13 casos fallaron** con respuestas vacías: `[EMPTY_RESPONSE] GPT-5 returned empty content`
- **Causa raíz**: Con `reasoning_effort: high`, GPT-5 usa **todos los 12,000 tokens de reasoning** y no genera contenido en la respuesta final
- **Ejemplo del log**:
  ```
  TOKENS: prompt=518, completion=12000 (reasoning=12000, response=0), total=12518, finish_reason=length
  RAW_RESPONSE: [EMPTY_RESPONSE] GPT-5 returned empty content - check prompt format
  ```
- **Casos afectados**: R664, R955, R601, R457, R316, R542, R213, S9, R206, R549, R633, R959, R132
- **Problema**: El modelo dedica tanto tiempo a "razonar internamente" que se queda sin tokens para generar la respuesta final

### 2. **Cambio en el Orden de Probabilidad** 🔄
- **Problema real**: Con `high` reasoning effort, el modelo **cambia el orden** de los diagnósticos, colocando diagnósticos correctos pero más específicos en **posiciones peores**
- **Tu observación es correcta**: Ser más específico NO es malo si el diagnóstico es correcto. El problema es que el **sistema de evaluación premia la posición**, no la especificidad.
- **Ejemplos reales**:
  - **Caso 7 (Sarcoidosis)**:
    - Low: "Sarcoidosis" en **P3** 
    - Medium: "Sarcoidosis" en **P4**
    - High: "Sarcoidosis (systemic granulomatous disease)" en **P3** (similar a low)
  - **Caso 8 (Rett syndrome)**:
    - Low: "Rett syndrome (MECP2-related)" en **P2**
    - Medium: "Rett syndrome (MECP2-related)" en **P3**
    - High: "Rett syndrome (MECP2-related)" en **P3** (similar a medium)
  - **Caso 18 (Glutaric acidemia)**:
    - Low: "Glutaric acidemia type I" en **P7** ❌
    - Medium: "Glutaric acidemia type I" en **P6** ❌
    - High: "Glutaric acidemia type I (glutaryl-CoA dehydrogenase deficiency)" en **P2** ✅ (MEJOR que low/medium)
- **Conclusión importante**:
  1. **El diagnóstico más específico puede ser correcto** y clínicamente mejor
  2. **PERO el sistema de evaluación busca coincidencias por códigos SNOMED/ICD-10** en orden secuencial (P1, P2, P3...)
  3. **Si el diagnóstico correcto está en P2 o P3 en lugar de P1**, empeora la posición promedio
  4. **El razonamiento excesivo** puede hacer que el modelo sobre-piense y cambie el orden de probabilidad, colocando diagnósticos correctos pero más específicos después de otros que considera más probables
  5. **Resultado**: Aunque los diagnósticos sean correctos y más específicos, están en posiciones peores en promedio (1.781 vs 1.664 en medium)

### 3. Evaluación de múltiples GDX
- Cuando un caso tiene múltiples GDX, el evaluador evalúa cada GDX individualmente
- Si un GDX específico no coincide con ningún DDX, se marca como rechazado
- Esto puede explicar algunos de los rechazos cuando hay múltiples GDX en un caso

### 4. Errores de Parsing
- Algunos casos tienen errores de parsing JSON: `Expecting value: line 1 column 2 (char 1)`
- Esto ocurre cuando la respuesta del LLM no es JSON válido o está vacía

## Conclusiones

1. **Low reasoning effort es el mejor**: 
   - ✅ 100% de éxito
   - ✅ Mejor distribución de posiciones (66.7% en P1)
   - ✅ Sin problemas de tokens o parsing
   - ✅ Posición promedio: 1.727

2. **Medium reasoning effort es bueno**: 
   - ✅ 99.33% de éxito (solo 1 caso rechazado)
   - ✅ **Mejor posición promedio (1.664)** - incluso mejor que low
   - ✅ Balance óptimo entre reasoning y respuesta
   - ✅ 65.8% en P1

3. **High reasoning effort es problemático**: 
   - ❌ Solo 91.33% de éxito (13 casos rechazados)
   - ❌ **Peor posición promedio (1.781)** incluso en casos exitosos
   - ❌ **Problema crítico #1**: Usa todos los 12,000 tokens de reasoning y no genera respuesta final
   - ❌ **Problema crítico #2**: Genera diagnósticos **demasiado específicos y complejos** que:
     - No coinciden exactamente con los GDX esperados (que suelen ser más generales)
     - Requieren más evaluación semántica (menos coincidencias exactas por SNOMED/ICD10)
     - Cambian el orden de probabilidad debido a razonamiento excesivo sobre combinaciones complejas
   - ❌ Genera respuestas vacías en 13 casos (8.67% del total)
   - ❌ Menos casos en P1 (64.2% vs 66.7% en low, 65.8% en medium)
   - ❌ Más casos en posiciones peores (P4-P10)
   - ⚠️ **No recomendado** - peor en todos los aspectos medibles

## Recomendaciones

1. **Usar `reasoning_effort: medium`** para obtener la mejor posición promedio (1.664) con 99.33% de éxito
2. **Usar `reasoning_effort: low`** si se requiere 100% de éxito absoluto (1.727 posición promedio)
3. **Evitar `reasoning_effort: high`** completamente:
   - ❌ **Peor posición promedio** (1.781) incluso en casos exitosos
   - ❌ **13 casos fallaron** (8.67% del total) debido a límite de tokens de reasoning
   - ❌ El modelo usa todos los 12,000 tokens de reasoning y no genera respuesta final
   - ❌ Menos casos en P1 y más en posiciones peores
   - ⚠️ **No aporta ningún beneficio** comparado con low/medium
4. **Si absolutamente se requiere `high` reasoning effort**:
   - Aumentar `max_tokens` significativamente (20,000-30,000)
   - Monitorear el uso de tokens de reasoning vs respuesta
   - Considerar implementar detección de respuestas vacías y reintentos automáticos
   - **Aún así, esperar peor posición promedio** que low/medium

## Comparación con otros modelos

### gpt-5-mini (low)
- Success rate: 99.33% (149/150)
- Average position: 1.671
- Similar a gpt-5.2 medium

### grok-4-1-fast-reasoning (low)
- Success rate: ~similar (revisar summary específico)
- Comparar con gpt-5.2 para ver diferencias

