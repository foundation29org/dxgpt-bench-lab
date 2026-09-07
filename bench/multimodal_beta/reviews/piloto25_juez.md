# Listas de DxGPT — 7 casos del piloto

Son las propuestas que hay que auditar en las tareas 2 y 3.
Escribe el veredicto en [david_deliverable.md](david_deliverable.md), no aquí.

Historia e imágenes de cada id: `datasets/processed/medreamm_pilot25/<id>/`

---

## Casos sin match automático

El programa dijo que ninguna propuesta es el gold.

### 24174966

- Gold: **Primary cardiac angiofibroma**
- El programa: `NO_MATCH` (posición `0`)
- Historia e imágenes: `datasets/processed/medreamm_pilot25/24174966`

Propuestas:
1. Cardiac cavernous hemangioma (left ventricular)
2. Left ventricular thrombus
3. Cardiac fibroma
4. Ventricular myxoma
5. Papillary fibroelastoma
6. Cardiac lipoma

### 27656661

- Gold: **Multiple sclerosis-like disorder**
- El programa: `NO_MATCH` (posición `0`)
- Historia e imágenes: `datasets/processed/medreamm_pilot25/27656661`

Propuestas:
1. Primary progressive multiple sclerosis (PPMS)
2. Hereditary spastic paraplegia (complicated form with optic atrophy)
3. Dominant optic atrophy (OPA1) with neurologic “DOA-plus” features
4. Primary lateral sclerosis (PLS)
5. MOG antibody-associated disease (MOGAD)
6. Adrenomyeloneuropathy in a heterozygous female carrier

### 30687305

- Gold: **Refractory cytopenias with multilineage dysplasia**
- El programa: `NO_MATCH` (posición `0`)
- Historia e imágenes: `datasets/processed/medreamm_pilot25/30687305`

Propuestas:
1. Myeloid/lymphoid neoplasm with eosinophilia (e.g., PDGFRA/PDGFRB/FGFR1 rearrangement) or chronic eosinophilic leukemia
2. Idiopathic hypereosinophilic syndrome (HES)
3. Chronic eosinophilic pneumonia
4. Eosinophilic granulomatosis with polyangiitis (EGPA, Churg–Strauss)
5. Drug-induced eosinophilic pneumonia

### 27074070

- Gold: **Mixed-cellularity subtype of classic Hodgkin's lymphoma**
- El programa: `NO_MATCH` (posición `0`)
- Historia e imágenes: `datasets/processed/medreamm_pilot25/27074070`

Propuestas:
1. Burkitt lymphoma (abdominal)
2. Crohn’s disease (ileocolic inflammatory bowel disease)
3. Intestinal (abdominal) tuberculosis
4. Yersinia enterocolitica/pseudotuberculosis infection (terminal ileitis with mesenteric adenitis)
5. Entamoeba histolytica infection (amebic colitis with possible liver abscess)

---

## Casos que el juez automático aceptó

El programa dio por buena una propuesta. Hay que decir si esa equivalencia es correcta.

### 27068836

- Gold: **Full-thickness oesophageal segment destruction**
- El programa aceptó la posición `1`
- Historia e imágenes: `datasets/processed/medreamm_pilot25/27068836`

Propuestas:
1. Pharyngoesophageal perforation/fistula from cervical spine hardware erosion
2. Infection of cervical spine instrumentation with prevertebral/paraspinal abscess
3. Esophageal perforation with mediastinitis and paraspinal abscess (non-hardware related)
4. Descending necrotizing mediastinitis from an oropharyngeal source
5. Vertebral osteomyelitis/discitis with contiguous paraspinal abscess
6. Tuberculous spondylitis (Pott disease) with paraspinal abscess

### 21424749

- Gold: **Mitochondrial disease**
- El programa aceptó la posición `1`
- Historia e imágenes: `datasets/processed/medreamm_pilot25/21424749`

Propuestas:
1. Maternally inherited mitochondrial myopathy with ataxia (mtDNA-related)
2. Inclusion body myositis (IBM)
3. Late-onset Pompe disease (acid maltase deficiency)
4. Multiple system atrophy, cerebellar type (MSA-C)
5. Autosomal dominant spinocerebellar ataxia with hearing loss (e.g., SCA36)

### 23281978

- Gold: **ST-segment elevation myocardial infarction**
- El programa aceptó la posición `1`
- Historia e imágenes: `datasets/processed/medreamm_pilot25/23281978`

Propuestas:
1. Acute anterior ST-elevation myocardial infarction (LAD occlusion)
2. Vasospastic (Prinzmetal) angina
3. Gastroesophageal reflux disease (GERD) with esophagitis
4. Esophageal spasm
5. Polycythemia vera (PV)
6. Essential thrombocythemia (ET)
