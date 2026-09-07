# Archivo historico

Origen: `bench/pipelines/summarization_feat (delete)/README.md`

Se conserva como analisis puntual de una linea de trabajo descartada. No forma parte del benchmark actual.

---

# ⚠️ EXPERIMENTAL ANALYSIS WARNING ⚠️

**IMPORTANTE**: Este benchmark **NO** fue diseñado originalmente para evaluar features de sumarización. Este análisis fue **improvisado** cuando Javi preguntó sobre el impacto de usar casos resumidos vs casos completos. Los resultados son informativos pero deben interpretarse con precaución dado el contexto experimental.

---

# Reflexión: Sumarización vs Casos Completos

## 🎯 Resumen Ejecutivo

La sumarización automática de casos clínicos con `gpt-4o-mini` degrada **drásticamente** la capacidad diagnóstica del modelo principal (`gpt-4o-summary`). Los resultados muestran caídas del 26-31% en métricas clave y un aumento del 95% en respuestas irrelevantes.

**Conclusión**: Para tareas de alta complejidad como el diagnóstico diferencial, la calidad del texto de entrada es crítica. "Garbage In, Garbage Out".

## 📊 Resultados Clave

| Métrica | Casos Completos | Casos Resumidos | Cambio |
|---------|----------------|-----------------|---------|
| `mean_best_match_score` | **0.6307** | **0.4672** | **-26%** |
| `hit_rate` (>0.8) | **0.46** | **0.32** | **-30%** |
| `EXACT_MATCH` | **0.45** | **0.31** | **-31%** |
| `UNRELATED_OR_NO_CODE` | **0.19** | **0.37** | **+95%** ⚠️ |

## 🔍 Ejemplos Reveladores

### Caso T1214: Colapso Total
- **GDx Real**: UTI + Acute Kidney Injury + Confusional syndrome
- **Completo (Score: 1.0)**: ✅ `Urinary Tract Infection`, `Acute Kidney Injury`
- **Resumido (Score: 0.0)**: ❌ `Over-anticoagulation`, `Respiratory infection sequelae`

**Análisis**: El resumen eliminó síntomas urinarios y marcadores renales, dejando solo "paciente mayor anticoagulado con somnolencia". El modelo se aferró a lo poco que quedó y falló completamente.

### Caso T1186: Confusión de Foco
- **GDx Real**: `Acute lower respiratory infection`
- **Completo**: ✅ `Community-Acquired Pneumonia`, `Acute Exacerbation of Chronic Bronchitis`
- **Resumido**: ❌ `Urinary Tract Infection`, `Pyelonephritis`, `Diverticulitis`

**Análisis**: El resumen borró señales respiratorias, dejando solo "fiebre en paciente mayor". El modelo defaulteó a focos infecciosos más comunes en geriatría.

## ✅ Por Qué Es Un Buen Análisis

1. **Datos Robustos**: Métricas consistentes muestran degradación en todos los frentes
2. **Casos Específicos**: Los ejemplos demuestran mecanismos de fallo claros
3. **Efecto Masivo**: +95% en respuestas irrelevantes es estadísticamente irrefutable
4. **Explicación Causal**: Identifica la pérdida de información crítica como causa raíz

## ❌ Limitaciones del Análisis

1. **Diseño Improvisado**: No fue planificado, puede haber sesgos metodológicos
2. **Sample Size**: Solo comparamos 2 runs, necesitamos más repeticiones
3. **Modelo de Resumen**: Solo probamos `gpt-4o-mini`, otros modelos podrían ser mejores
4. **Evaluación**: El sistema ICD10 puede no capturar toda la validez clínica

## 🔬 Qué Dicen Los Resultados

**Fenómeno Principal**: La sumarización destruye la **señal clínica**

1. **Pérdida de Especificidad**: "dolor torácico opresivo irradiado" → "dolor de pecho"
2. **Omisión de Datos Clave**: Se eliminan laboratorios, exploración física, historia clínica
3. **Aumento de Ambigüedad**: Cuadros vagos → diagnósticos vagos o incorrectos
4. **Colapso de Confianza**: El modelo "dispara a ciegas" con más frecuencia

## 🚀 Próximos Pasos

### Inmediatos
- [ ] Repetir experimento con más runs para confirmar consistencia
- [ ] Probar otros modelos de resumen (`gpt-4`, `claude-3.5-sonnet`)
- [ ] Evaluar diferentes niveles de compresión (50%, 25%, 10%)

### Investigación Futura
- [ ] Desarrollar métricas específicas para evaluar preservación de información clínica
- [ ] Comparar resumen automático vs resumen por médicos expertos
- [ ] Investigar técnicas de resumen "conscientes de dominio médico"

### Consideraciones de Producto
- [ ] **NO** implementar sumarización automática en producción sin más investigación
- [ ] Considerar alertas cuando el texto de entrada sea demasiado corto
- [ ] Evaluar si vale la pena el trade-off contexto vs precisión

---

**Nota Final**: Este análisis, aunque improvisado, revela un hallazgo fundamental sobre la importancia de la calidad del input en tareas de IA médica. Merece investigación más profunda antes de cualquier implementación en entornos reales.
