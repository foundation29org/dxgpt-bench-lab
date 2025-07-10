# Bench - Sistema de Evaluación de Modelos de Diagnóstico 🏆

El directorio `bench` contiene el sistema de benchmarking para evaluar modelos de IA médica en tareas de diagnóstico diferencial, comparando su rendimiento con diagnósticos de referencia validados.

## 🎯 Propósito

Evaluar sistemáticamente la capacidad diagnóstica de modelos LLM mediante:

1. **Precisión Semántica**: Qué tan bien identifican el diagnóstico correcto
2. **Evaluación de Severidad**: Qué tan precisamente estiman la gravedad clínica

## 🏗️ Arquitectura del Sistema

```
bench/
├── README.md                           # Este archivo
├── candidate-prompts/                  # Prompts para generar diagnósticos
│   ├── candidate_output_schema.json    # Esquema de respuesta esperada
│   └── [varios prompts].txt            # Diferentes estrategias de prompting
├── datasets/                           # Datasets médicos evaluables
│   ├── all_150.json                   # Dataset balanceado (150 casos)
│   ├── all_250.json                   # Dataset medio (250 casos)
│   ├── all_450.json                   # Dataset completo (450 casos)
│   └── [otros datasets].json          # Datasets especializados
└── pipelines/                         # Pipelines de evaluación (3 versiones)
    ├── pipeline_v1 - icd10/           # Pipeline base con ICD-10
    ├── pipeline_v2 - icd10 + bert/   # Pipeline mejorada con BERT
    └── pipeline_v3 - full LLM/       # Pipeline experimental LLM puro
```

## 🔄 Flujo de Evaluación

El proceso completo sigue estos pasos:

### 1. Generación de Diagnósticos (DDX)
```python
# El modelo recibe un caso clínico
caso = "Paciente de 45 años con dolor torácico..."

# Genera 5 diagnósticos diferenciales
ddx = ["Infarto", "Angina", "Reflujo", "Ansiedad", "Costocondritis"]
```

### 2. Evaluación Semántica
```python
# Comparamos DDX con diagnósticos correctos (GDX)
gdx = ["Infarto agudo de miocardio", "Síndrome coronario agudo"]

# SapBERT calcula similitud semántica
scores = {
    "Infarto": {"Infarto agudo de miocardio": 0.95},
    "Angina": {"Síndrome coronario agudo": 0.78},
    # ...
}
```

### 3. Asignación de Severidad
```python
# Un LLM asigna severidad a cada diagnóstico único
severidades = {
    "Infarto": "S9",        # Muy grave
    "Angina": "S7",         # Grave
    "Reflujo": "S3",        # Leve
    "Ansiedad": "S2",       # Muy leve
    "Costocondritis": "S1"  # Mínima
}
```

### 4. Cálculo de Métricas
```python
# Score semántico: mejor match entre DDX y GDX
semantic_score = 0.95  # (Infarto ↔ Infarto agudo)

# Score de severidad: distancia normalizada
severity_score = 0.15  # (cercano a severidad correcta)
```

## 📁 Componentes Principales

### datasets/
Contiene los datasets médicos procesados y validados para evaluación. Incluye datasets de diferentes tamaños y características, todos con casos clínicos estructurados y sus diagnósticos de referencia (GDX).

### pipelines/
Sistema evolutivo de evaluación con tres pipelines que representan un avance metodológico progresivo:

- **Pipeline v1 - ICD10**: Evaluación base usando clasificación ICD-10 directa
- **Pipeline v2 - ICD10 + BERT**: Evaluación mejorada incorporando embeddings biomédicos para mayor precisión semántica
- **Pipeline v3 - Full LLM**: Evaluación experimental usando LLMs para todo el proceso sin embeddings pre-entrenados

Cada pipeline contiene su propio `config.yaml` para configuración de experimentos y carpeta `results/` para almacenar resultados.

### candidate-prompts/
Contiene los prompts e instrucciones para que los modelos generen diagnósticos diferenciales, incluyendo el esquema de respuesta esperado y múltiples variantes de estrategias de prompting.

## 🚀 Ejecutar un Experimento

## 📚 Documentación Adicional

Para comprender el modelo conceptual del benchmarking y las notas de investigación detalladas, consulte:

📁 **`__benchmarking-conceptual-model-and-research-notes/`**
- Contiene análisis detallados, comparaciones entre pipelines y hallazgos de investigación
- Incluye visualizaciones y documentación del proceso evolutivo del sistema

### 1. Configurar el experimento

Editar `pipelines/[pipeline_version]/config.yaml`:
```yaml
experiment_name: "Mi Experimento GPT-4"
dataset_path: "bench/datasets/ramedis-45.json"

llm_configs:
  candidate_dx_gpt:
    model: "gpt-4o"  # o "jonsnow", "medgemma", etc.
    prompt: "../candidate-prompts/candidate_prompt.txt"
    
  severity_assigner_llm:
    model: "gpt-4o"
    prompt: "eval-prompts/severity_assignment_batch_prompt.txt"
```

## 🚨 Consideraciones Importantes

- Los datasets son sintéticos/anonimizados, NO contienen datos reales de pacientes
- Los resultados son para investigación, NO para diagnóstico clínico real
- La evaluación es automática, puede tener sesgos o limitaciones
- Siempre validar con expertos médicos antes de conclusiones

## 🔗 Referencias

- [Pipeline v1 - Documentación](pipelines/pipeline_v1%20-%20icd10/README.md)
- [Pipeline v2 - Documentación](pipelines/pipeline_v2%20-%20icd10%20+%20bert/pipeline_README.md)
- [Modelo Conceptual - Investigación](__benchmarking-conceptual-model-and-research-notes/)
- [Datasets - Origen y estructura](../data29/README.md)