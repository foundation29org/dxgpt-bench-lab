# Revisión clínica — pilot25 T+I gpt5 strict

Paquete local generado automáticamente. El pretriaje es técnico y no
sustituye el veredicto del revisor médico.

## Resumen

- Casos evaluados: 25.
- Casos sin match: 4.
- Matches decididos por el juez LLM: 3.

## Casos sin match

### 24174966

- Gold: **Primary cardiac angiofibroma**
- Resolución automática: `NO_MATCH`
- Posición aceptada: `0`
- Historia e imágenes: `bench/multimodal_beta/datasets/processed/medreamm_pilot25/24174966`
- Condición: `T+I`
- Modelo real: `gpt5`
- Resumido: `False`
- Mejor BERT: P3, puntuación 0.760
- Pretriaje técnico: Prioridad alta: similitud BERT elevada; posible problema de equivalencia, granularidad o gold.

Propuestas:
1. Cardiac cavernous hemangioma (left ventricular)
2. Left ventricular thrombus
3. Cardiac fibroma
4. Ventricular myxoma
5. Papillary fibroelastoma
6. Cardiac lipoma

Respuesta clínica:

- Primera posición equivalente:
- Veredicto del evaluador:
- Calidad/granularidad del gold:
- Justificación:
- Confianza:

### 27656661

- Gold: **Multiple sclerosis-like disorder**
- Resolución automática: `NO_MATCH`
- Posición aceptada: `0`
- Historia e imágenes: `bench/multimodal_beta/datasets/processed/medreamm_pilot25/27656661`
- Condición: `T+I`
- Modelo real: `gpt5`
- Resumido: `False`
- Mejor BERT: P1, puntuación 0.714
- Pretriaje técnico: Prioridad media: resultado fronterizo; requiere criterio clínico.

Propuestas:
1. Primary progressive multiple sclerosis (PPMS)
2. Hereditary spastic paraplegia (complicated form with optic atrophy)
3. Dominant optic atrophy (OPA1) with neurologic “DOA-plus” features
4. Primary lateral sclerosis (PLS)
5. MOG antibody-associated disease (MOGAD)
6. Adrenomyeloneuropathy in a heterozygous female carrier

Respuesta clínica:

- Primera posición equivalente:
- Veredicto del evaluador:
- Calidad/granularidad del gold:
- Justificación:
- Confianza:

### 30687305

- Gold: **Refractory cytopenias with multilineage dysplasia**
- Resolución automática: `NO_MATCH`
- Posición aceptada: `0`
- Historia e imágenes: `bench/multimodal_beta/datasets/processed/medreamm_pilot25/30687305`
- Condición: `T+I`
- Modelo real: `gpt5`
- Resumido: `False`
- Mejor BERT: P1, puntuación 0.499
- Pretriaje técnico: Similitud semántica baja; posible error diagnóstico sustantivo, pendiente de confirmación clínica.

Propuestas:
1. Myeloid/lymphoid neoplasm with eosinophilia (e.g., PDGFRA/PDGFRB/FGFR1 rearrangement) or chronic eosinophilic leukemia
2. Idiopathic hypereosinophilic syndrome (HES)
3. Chronic eosinophilic pneumonia
4. Eosinophilic granulomatosis with polyangiitis (EGPA, Churg–Strauss)
5. Drug-induced eosinophilic pneumonia

Respuesta clínica:

- Primera posición equivalente:
- Veredicto del evaluador:
- Calidad/granularidad del gold:
- Justificación:
- Confianza:

### 27074070

- Gold: **Mixed-cellularity subtype of classic Hodgkin's lymphoma**
- Resolución automática: `NO_MATCH`
- Posición aceptada: `0`
- Historia e imágenes: `bench/multimodal_beta/datasets/processed/medreamm_pilot25/27074070`
- Condición: `T+I`
- Modelo real: `gpt5`
- Resumido: `False`
- Mejor BERT: P1, puntuación 0.309
- Pretriaje técnico: Similitud semántica baja; posible error diagnóstico sustantivo, pendiente de confirmación clínica.

Propuestas:
1. Burkitt lymphoma (abdominal)
2. Crohn’s disease (ileocolic inflammatory bowel disease)
3. Intestinal (abdominal) tuberculosis
4. Yersinia enterocolitica/pseudotuberculosis infection (terminal ileitis with mesenteric adenitis)
5. Entamoeba histolytica infection (amebic colitis with possible liver abscess)

Respuesta clínica:

- Primera posición equivalente:
- Veredicto del evaluador:
- Calidad/granularidad del gold:
- Justificación:
- Confianza:

## Matches del juez LLM que deben muestrearse

Estos casos sirven para estimar falsos positivos del juez strict.

### 27068836

- Gold: **Full-thickness oesophageal segment destruction**
- Resolución automática: `LLM_JUDGMENT`
- Posición aceptada: `1`
- Historia e imágenes: `bench/multimodal_beta/datasets/processed/medreamm_pilot25/27068836`
- Condición: `T+I`
- Modelo real: `gpt5`
- Resumido: `False`
- Mejor BERT: P3, puntuación 0.473
- Pretriaje técnico: Similitud semántica baja; posible error diagnóstico sustantivo, pendiente de confirmación clínica.

Propuestas:
1. Pharyngoesophageal perforation/fistula from cervical spine hardware erosion
2. Infection of cervical spine instrumentation with prevertebral/paraspinal abscess
3. Esophageal perforation with mediastinitis and paraspinal abscess (non-hardware related)
4. Descending necrotizing mediastinitis from an oropharyngeal source
5. Vertebral osteomyelitis/discitis with contiguous paraspinal abscess
6. Tuberculous spondylitis (Pott disease) with paraspinal abscess

Respuesta clínica:

- Primera posición equivalente:
- Veredicto del evaluador:
- Calidad/granularidad del gold:
- Justificación:
- Confianza:

### 21424749

- Gold: **Mitochondrial disease**
- Resolución automática: `LLM_JUDGMENT`
- Posición aceptada: `1`
- Historia e imágenes: `bench/multimodal_beta/datasets/processed/medreamm_pilot25/21424749`
- Condición: `T+I`
- Modelo real: `gpt5`
- Resumido: `True`
- Mejor BERT: P1, puntuación 0.644
- Pretriaje técnico: Prioridad media: resultado fronterizo; requiere criterio clínico.

Propuestas:
1. Maternally inherited mitochondrial myopathy with ataxia (mtDNA-related)
2. Inclusion body myositis (IBM)
3. Late-onset Pompe disease (acid maltase deficiency)
4. Multiple system atrophy, cerebellar type (MSA-C)
5. Autosomal dominant spinocerebellar ataxia with hearing loss (e.g., SCA36)

Respuesta clínica:

- Primera posición equivalente:
- Veredicto del evaluador:
- Calidad/granularidad del gold:
- Justificación:
- Confianza:

### 23281978

- Gold: **ST-segment elevation myocardial infarction**
- Resolución automática: `LLM_JUDGMENT`
- Posición aceptada: `1`
- Historia e imágenes: `bench/multimodal_beta/datasets/processed/medreamm_pilot25/23281978`
- Condición: `T+I`
- Modelo real: `gpt5`
- Resumido: `True`
- Mejor BERT: P1, puntuación 0.670
- Pretriaje técnico: Prioridad media: resultado fronterizo; requiere criterio clínico.

Propuestas:
1. Acute anterior ST-elevation myocardial infarction (LAD occlusion)
2. Vasospastic (Prinzmetal) angina
3. Gastroesophageal reflux disease (GERD) with esophagitis
4. Esophageal spasm
5. Polycythemia vera (PV)
6. Essential thrombocythemia (ET)

Respuesta clínica:

- Primera posición equivalente:
- Veredicto del evaluador:
- Calidad/granularidad del gold:
- Justificación:
- Confianza:
