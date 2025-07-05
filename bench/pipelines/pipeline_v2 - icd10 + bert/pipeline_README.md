# Pipeline v2 - Flujo Lógico

## 1. CONFIGURACIÓN
- Carga config.yaml con modelo, prompt, dataset
- Crea directorio results/modelo/run_timestamp/
- Inicializa: DiagnosisGenerator (LLM), AzureTextAnalytics, SemanticEvaluator, SeverityEvaluator

## 2. FASE 1: PROCESAMIENTO DE CASOS (Paralelo)
Para cada caso:
1. **Genera DDX**: LLM → lista de diagnósticos diferenciales
2. **Extrae códigos**: Azure Text Analytics → normaliza texto + códigos médicos (ICD10, SNOMED, etc)
3. **Evaluación semántica**: 
   - Compara DDX vs GDX usando jerarquía ICD10
   - Si score = 0.0 → BERT fallback (cruza todas combinaciones texto, acepta si ≥ 0.80)
4. **Evaluación severidad**: Calcula distancias normalizadas entre severidades DDX-GDX

## 3. FASE 2: ASIGNACIÓN SEVERIDADES
- Extrae DDX únicos de todos los casos
- LLM asigna severidades (S0-S10) en lotes de 50
- Caché para reutilizar en evaluaciones

## 4. FASE 3: GENERACIÓN ARCHIVOS
- **run_summary.json**: Métricas globales + análisis ICD10 + estadísticas BERT
- **diagnoses.json**: DDX/GDX con códigos médicos por caso
- **semantic_evaluation.json**: Scores y relaciones (code_type: icd10/BERT/none)
- **severity_evaluation.json**: Análisis severidad con bias (optimista/pesimista)
- **ddx_analysis.csv**: Frecuencia DDX generados

## CÁLCULOS CLAVE
- **Score semántico**: Max(comparaciones ICD10) o BERT si falla
- **Score severidad**: Promedio(|sev_ddx - sev_gdx| / max_distancia)
- **Top-K accuracy**: % casos con score ≥ 0.8 en top K posiciones