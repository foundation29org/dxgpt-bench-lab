# Anotaciones de fallos por ejecución

Fichero para anotar manualmente los casos sin match y observaciones de cada run relevante.  
Complementa `rankingV2.txt` con análisis cualitativo.

---

## Sobre falsos positivos / falsos negativos del evaluador

El evaluador puede equivocarse en **ambas direcciones**:

| Tipo | Qué pasa | Ejemplo típico |
|------|----------|----------------|
| **Falso negativo** (fallo registrado, modelo acertó) | El evaluador no encuentra match aunque el DDX es clínicamente correcto | Modelo dice "Central Herniation", GDX es "Central Herniation" con otro código SNOMED; no hay match por código y BERT no alcanza el umbral. |
| **Falso positivo** (match registrado, modelo falló) | El evaluador acepta un match que no es correcto clínicamente | ICD10_SIBLING empareja dos enfermedades distintas que comparten código padre; o el juez LLM acepta un diagnóstico "relacionado" pero no equivalente. |

Mecanismos concretos de falso positivo:
- **ICD10_SIBLING**: dos enfermedades con el mismo código padre ICD-10 se consideran "hermanas"; pueden ser distintas.
- **LLM Judge permisivo**: con BERT < 0.8, el juez decide; puede aceptar diagnósticos vagamente relacionados (ej. "Hypoparathyroidism" como match de "Iatrogenic hypoparathyroidism").
- **BERT embedding alto**: nombres de enfermedad similares léxicamente pero distintos clínicamente pueden superar umbral 0.9 y autoaceptarse.

---

## Run: all_275 · juanjo_classic_v2 · gemini_2_5_pro_low_translated_en
**Timestamp:** 20260324154608  
**Resultado:** 271/275 matched (98.5%) · pos. media 1.328 · juez gemini-2.5-pro

### Casos sin match (4)

| Caso | GDX (diagnóstico correcto) | DDX generado (top 3) | Tipo de fallo | Comentario |
|------|---------------------------|----------------------|---------------|------------|
| **B133** | Metastatic Colon Cancer | Intellectualization / Denial / Adjustment Disorder | **Error del modelo** — respuesta completamente fuera de contexto | El modelo generó mecanismos de defensa psicológicos en lugar de un diagnóstico oncológico. Posiblemente el caso describía el estado emocional del paciente y Gemini interpretó mal el objetivo. |
| **Q3435** | Central Herniation | Transtentorial Herniation / Tonsillar Herniation / Subfalcine Herniation | **Fallo del evaluador** — modelo clínicamente correcto | El modelo enumeró correctamente los tipos de herniación cerebral pero no usó exactamente "Central Herniation"; sin match por código (GDX sin SNOMED, ICD10 G93.5 no coincide con ningún DDX). Caso candidato a revisar el GDX o añadir sinónimos. |
| **Q409** | "Tumor stage" | Invasive Ductal Carcinoma / Radial Scar / Invasive Lobular Carcinoma | **Problema del dataset** — GDX no es un diagnóstico clínico | El GDX es el estadio tumoral, no la enfermedad. El modelo diagnosticó el tumor correctamente. Candidato a corregir en el dataset. |
| **Q548** | Hemolytic anemia and ataxia | Anaphylaxis / Severe Asthma / Decompensated Hemorrhagic Shock | **Error del modelo** — respuesta completamente errónea | El modelo generó diagnósticos de urgencia aguda sin relación con anemia hemolítica + ataxia. Caso con presentación probablemente atípica o ambigua. |

### Observaciones generales
- **2 de 4 fallos** son cuestionables como error real del modelo (Q3435 y Q409).
- **P5+ ausente**: todos los 271 matches están en las 4 primeras posiciones. Muy buen rendimiento de ranking.
- **LLM_JUDGMENT**: 94 casos resueltos por el juez (34%). El juez Gemini 2.5-pro es relativamente permisivo — posible fuente de falsos positivos a monitorizar.

---

## Run: all_275 · juanjo_classic_v2 · o3_dxgpt_high_translated_en
**Timestamp:** 20260324114455  
**Resultado:** 269/275 matched (97.8%) · pos. media 1.680 · juez gemini-2.5-pro

*(Pendiente análisis de los 6 casos sin match — ver evaluation_details.txt en la carpeta del run)*

---

## Run: all_275 · juanjo_classic_v2 · gpt_5_1_low
**Resultado:** 258/275 matched (93.8%) · pos. media 1.442 · juez N/A (sin anotar)

*(Pendiente análisis de los 17 casos sin match)*

---

## Plantilla para nuevos runs

```
## Run: <dataset> · <prompt> · <model>
**Timestamp:** <timestamp>  
**Resultado:** <matched>/<total> (<pct>%) · pos. media <avg> · juez <judge>

### Casos sin match

| Caso | GDX | DDX (top 3) | Tipo de fallo | Comentario |
|------|-----|-------------|---------------|------------|
| ... | ... | ... | Error modelo / Fallo evaluador / Problema dataset | ... |

### Observaciones generales
- ...
```
