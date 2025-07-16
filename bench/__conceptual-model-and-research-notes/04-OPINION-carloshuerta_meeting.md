# HALLAZGOS ESTRATÉGICOS: Propuestas de Carlos Huerta para Evolución del Framework
## Del Estancamiento Metodológico hacia Nuevos Horizontes de Evaluación

### Resumen Ejecutivo

Este informe documenta las reflexiones y propuestas estratégicas surgidas de la reunión con Carlos Huerta (8 de julio, 2025) en respuesta a los hallazgos de saturación metodológica identificados en nuestros pipelines de evaluación. Carlos presentó tres líneas de acción transformadoras que podrían revolucionar nuestra aproximación al benchmarking de modelos diagnósticos.

**El Diagnóstico de Carlos:** Hemos alcanzado los límites de nuestro approach actual no por deficiencias técnicas, sino porque **el prompt está demasiado optimizado y la tarea demasiado simplificada**. Los modelos de razonamiento avanzado necesitan desafíos más complejos para demostrar su verdadero potencial.

**Sus Propuestas Transformadoras:**
1. **Expansión Sintética del Contexto:** Hacer que el modelo desarrolle el caso antes de diagnosticar
2. **Integración de Deep Research:** Utilizar modelos de investigación profunda como evaluadores alternativos

### El Problema Identificado: Saturación por Simplicidad

#### La Observación Crítica

Carlos identificó inmediatamente el núcleo del problema: nuestro prompt, diseñado inicialmente para ser claro y objetivo, se ha convertido en una limitación. Su observación fue reveladora: *"Una pregunta inteligente da una respuesta inteligente para lo mando la distancia"*.

**Ejemplo ilustrativo de Carlos:**
- **Prompt simple:** "Dame una foto de Alcalá"
- **Resultado:** Foto genérica y predecible
- **Prompt expandido:** "Dame una fotografía con la Cámara Canon 400D EOS en el anochecer, cuando se ve la luz justamente en la Universidad, en la fachada de la Universidad"
- **Resultado:** Fotografía específica, contextualizada y de calidad superior

**La Aplicación al Diagnóstico:** Nuestro prompt actual (`list the 5 most likely diseases`) es el equivalente al "dame una foto de Alcalá". Funciona, pero no desafía las capacidades superiores de los modelos avanzados.

#### El Precedente Exitoso: Análisis de Proveedores

Carlos compartió un caso de éxito donde enfrentaron un problema similar. Al evaluar proveedores, descubrieron que:

- **Enfoque One-Shot:** Resultados mediocres y poco diferenciados
- **Enfoque Multi-Etapa:** Resultados significativamente superiores
  1. Entender el contexto del proveedor/paciente
  2. Identificar acciones potenciales a partir de ese contexto
  3. Generar universo de potenciales programas
  4. Resolver el caso con toda la información generada

**El Insight:** Los modelos de razonamiento brillan cuando se les permite construir su propia base de conocimiento expandida antes de llegar a conclusiones.

### Propuesta 1: Expansión Sintética del Contexto

#### El Concepto

En lugar de presentar casos directamente para diagnóstico, hacer que el modelo primero "desarrolle" el caso, expandiendo el contexto disponible antes de proporcionar su respuesta diagnóstica final.

#### Implementación Sugerida

**Fase 1: Desarrollo del Caso**
```
"Analiza la información proporcionada y expande el contexto clínico:
1. Identifica patrones fisiopatológicos relevantes
2. Desarrolla diferenciales por sistemas
3. Analiza interacciones y comorbilidades potenciales
4. Establece jerarquías de probabilidad
Con esta información expandida, procede al diagnóstico."
```

**Fase 2: Diagnóstico Informado**
El modelo usa su propia expansión para generar diagnósticos más fundamentados.

#### Ventajas Anticipadas

- **Revelación de Capacidades Latentes:** Los modelos avanzados podrán demostrar su razonamiento profundo
- **Diferenciación Clara:** Los modelos superficiales fallarán en la expansión, los avanzados brillarán
- **Mayor Precisión Diagnóstica:** El contexto expandido debería mejorar la precisión final

### Propuesta 2: Deep Research como Evaluador Alternativo

#### La Propuesta

Carlos sugirió implementar Azure Deep Research como sistema de evaluación alternativo, creando un framework comparativo entre:

- **ICD10+BERT** (precisión terminológica)
- **Juez LLM tradicional** (plausibilidad clínica)
- **Deep Research** (investigación exhaustiva y contextualizada)

#### Ventajas del Deep Research

1. **Capacidad de Investigación:** Puede profundizar en casos complejos de manera que otros evaluadores no pueden
2. **Neutralidad Familiar:** Al ser de diferente arquitectura, reduce el sesgo de autoevaluación
3. **Implementación Sencilla:** Ya está disponible en Azure

#### Framework de Comparación Propuesto

- **Paso 1:** Ejecutar los 450 casos con Deep Research
- **Paso 2:** Comparar resultados con evaluaciones anteriores
- **Paso 3:** Identificar qué información adicional aporta cada modelo
- **Paso 4:** Usar estas diferencias para entender mejor las capacidades reales

### Implicaciones Estratégicas y Siguientes Pasos

#### La Hipótesis de Carlos Validada

Los insights de Carlos explican perfectamente nuestros hallazgos de convergencia. No es que los modelos sean equivalentes, sino que **nuestra metodología no es lo suficientemente sofisticada para distinguir entre capacidades avanzadas**.

#### Priorización de Implementación

**Inmediato (1-2 semanas):**
1. Implementar Deep Research como evaluador adicional
2. Diseñar prompts expandidos para expansión de contexto

**Medio Plazo (1 mes):**
1. Ejecutar comparación completa con los tres sistemas de evaluación
2. Analizar discrepancias y patrones emergentes

**Largo Plazo (2-3 meses):**
1. Explorar framework multi-agente con Autogen Studio
2. Validar con casos del Hospital San Juan de Dios

#### El Cambio de Paradigma

Carlos nos ha mostrado que el problema no es que nuestros modelos no sean diferentes, sino que **nuestras preguntas no son lo suficientemente inteligentes**. La solución no está en cambiar los modelos evaluados, sino en elevar la sofisticación de la evaluación misma.

### Reflexiones Finales: Hacia una Evaluación de Nueva Generación

La reunión con Carlos representa un punto de inflexión en nuestro approach metodológico. Sus propuestas no son simples ajustes técnicos, sino un replanteamiento fundamental de cómo evaluamos capacidades de razonamiento clínico en modelos de IA.

**La Pregunta Central:** ¿Estamos preguntando "¿Qué modelo es mejor?" o estamos preguntando "¿Cómo podemos hacer que cada modelo demuestre lo mejor de sí mismo?"

Carlos sugiere que la segunda pregunta es mucho más valiosa estratégicamente. Un framework de evaluación que revele las capacidades latentes de cada modelo nos dará ventajas competitivas más claras y decisiones de producto más informadas.

**El Next Step:** Implementar estas propuestas no como reemplazo de nuestro sistema actual, sino como expansión hacia un ecosistema de evaluación más rico y matizado que capture la verdadera sofisticación de los modelos de nueva generación.

![Visualización del proceso ETL del dataset](imgs/etl_visualized_as_sankey_at_20250708.png)

*Nota: La imagen muestra la complejidad de nuestro proceso de datos actual - el marco de evaluación debe evolucionar para capturar esta misma riqueza y diversidad.*