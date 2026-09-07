# Comparación ciega — 8 casos

Lee cada caso con su carpeta de historia e imágenes. Elige la lista A, la B,
empate o ninguna. Escribe el veredicto en
[david_deliverable.md](david_deliverable.md), tarea 4.

No abras ningún `coordinator_key.md`.

Cómo leer un caso:

- **Gold**: el diagnóstico correcto del artículo.
- **Lista A / Lista B**: dos diferenciales de DxGPT. Una salió con texto
  solo y la otra con texto más imágenes. No te decimos cuál es cuál.
- **Match automático: N**: el programa cree que el gold está en el puesto N.
  `0` = no lo encontró. Tú puedes estar en desacuerdo.

---

## Caso 23553973

- Gold: **Amoebic liver abscess**
- Historia e imágenes: `datasets/processed/medreamm_pilot100/23553973`

### Lista A

- Match automático: `0`
1. Q fever (Coxiella burnetii)
2. Leptospirosis
3. Rickettsial infection (e.g., murine typhus or spotted fever group)
4. Pulmonary embolism
5. Viral pleuritis/pleurodynia (Coxsackie virus)
6. Influenza-like illness
7. Acute bacterial gastroenteritis with systemic inflammatory response

### Lista B

- Match automático: `6`
1. Melioidosis (Burkholderia pseudomallei) with visceral abscesses
2. Splenic abscess secondary to bacteremia (e.g., Staphylococcus aureus or Salmonella spp.)
3. Splenic infarction
4. Q fever (Coxiella burnetii)
5. Leptospirosis
6. Amoebic liver abscess (Entamoeba histolytica)

---

## Caso 27380346

- Gold: **Erythema nodosum**
- Historia e imágenes: `datasets/processed/medreamm_pilot100/27380346`

### Lista A

- Match automático: `0`
1. Azathioprine-induced hypersensitivity (serum sickness–like reaction)
2. Drug-induced Sweet syndrome (acute febrile neutrophilic dermatosis)
3. Parvovirus B19 infection (acute viral arthropathy)
4. Drug-induced leukocytoclastic vasculitis (hypersensitivity vasculitis)
5. Disseminated gonococcal infection (DGI)
6. Adult-onset Still's disease

### Lista B

- Match automático: `4`
1. Drug-induced Sweet syndrome (acute febrile neutrophilic dermatosis)
2. Azathioprine-induced hypersensitivity syndrome (serum sickness–like reaction)
3. Leukocytoclastic vasculitis (hypersensitivity vasculitis), drug-induced
4. Erythema nodosum (potentially drug-induced)
5. Septic arthritis (polyarticular)
6. Acute crystal arthropathy (gout or calcium pyrophosphate deposition disease)

---

## Caso 27068836

- Gold: **Full-thickness oesophageal segment destruction**
- Historia e imágenes: `datasets/processed/medreamm_pilot100/27068836`

### Lista A

- Match automático: `0`
1. Infected cervical spinal instrumentation with paraspinal abscess
2. Spinal epidural abscess (cervicothoracic)
3. Vertebral osteomyelitis/discitis (cervicothoracic) with associated paraspinal abscess
4. Retropharyngeal abscess with descending extension
5. Tuberculous spondylitis (Pott disease) with paraspinal 'cold' abscess

### Lista B

- Match automático: `1`
1. Esophageal perforation with descending mediastinitis (likely secondary to cervical hardware erosion)
2. Cervical vertebral osteomyelitis/discitis with paraspinal abscess
3. Spinal epidural abscess (cervicothoracic)
4. Instrumentation (hardware)-associated chronic infection with sinus/abscess formation
5. Retropharyngeal/paraesophageal abscess with mediastinal extension
6. Tuberculous spondylitis (Pott disease) with cold paraspinal abscess

---

## Caso 23281978

- Gold: **ST-segment elevation myocardial infarction**
- Historia e imágenes: `datasets/processed/medreamm_pilot100/23281978`

### Lista A

- Match automático: `0`
1. Non–ST-elevation myocardial infarction (NSTEMI)
2. Vasospastic (Prinzmetal) angina
3. Gastroesophageal reflux disease (GERD) with possible erosive esophagitis
4. Esophageal spasm
5. Polycythemia vera (JAK2-positive myeloproliferative neoplasm)

### Lista B

- Match automático: `1`
1. Acute anterior ST-elevation myocardial infarction (LAD territory)
2. Polycythemia vera (myeloproliferative neoplasm, likely JAK2-mutated)
3. Essential thrombocythemia (myeloproliferative neoplasm)
4. Gastroesophageal reflux disease (GERD) with reflux esophagitis
5. Coronary vasospasm (Prinzmetal/variant angina)
6. Acute myopericarditis

---

## Caso N-10000083

- Gold: **Intralobar bronchopulmonary sequestration**
- Historia e imágenes: `datasets/processed/medreamm_pilot100/N-10000083`

### Lista A

- Match automático: `0`
1. Hypoxic-ischemic encephalopathy (HIE) due to perinatal asphyxia
2. Meconium aspiration syndrome
3. Persistent pulmonary hypertension of the newborn (PPHN)
4. Early-onset neonatal sepsis
5. Critical congenital heart disease (ductal-dependent lesion)
6. Neonatal intracranial hemorrhage or traumatic birth injury

### Lista B

- Match automático: `4`
1. Neonatal pneumothorax (air-leak syndrome)
2. Pulmonary interstitial emphysema (PIE)
3. Congenital pulmonary airway malformation (CPAM) with possible hybrid lesion
4. Bronchopulmonary sequestration (systemic arterialized lung)
5. Meconium aspiration syndrome with secondary air-leak and PPHN risk

---

## Caso 24054536

- Gold: **Peripheral air embolism**
- Historia e imágenes: `datasets/processed/medreamm_pilot100/24054536`

### Lista A

- Match automático: `2`
1. Paradoxical venous air embolism via patent foramen ovale (PFO) causing coronary and cerebral ischemia
2. Coronary air embolism (iatrogenic)
3. Venous (pulmonary) air embolism
4. Acute coronary syndrome (non–ST-elevation myocardial infarction)
5. Aortic dissection

### Lista B

- Match automático: `0`
1. Paradoxical systemic air embolism via patent foramen ovale (PFO)
2. Venous air embolism (pulmonary air embolism)
3. Coronary air embolism causing acute coronary syndrome (NSTEMI)
4. Transient ischemic attack due to cerebral air embolism (paradoxical)
5. Acute pulmonary embolism (non-air thromboembolism) – less likely

---

## Caso 27709474

- Gold: **Phosphaturic mesenchymal tumor**
- Historia e imágenes: `datasets/processed/medreamm_pilot100/27709474`

### Lista A

- Match automático: `0`
1. Phenytoin-induced osteomalacia (anticonvulsant-induced vitamin D deficiency)
2. Vitamin D deficiency osteomalacia (non–drug-related)
3. Anticonvulsant-associated osteoporosis
4. Primary hyperparathyroidism (osteitis fibrosa cystica)
5. Polymyositis

### Lista B

- Match automático: `1`
1. Tumor-induced osteomalacia (phosphaturic mesenchymal tumor with excess FGF23)
2. Anticonvulsant (phenytoin)-induced osteomalacia
3. Primary hyperparathyroidism
4. Fanconi syndrome (proximal renal tubular dysfunction) with phosphate wasting
5. Vitamin D deficiency osteomalacia (malabsorption or nutritional)

---

## Caso 23574122

- Gold: **Torus palatinus**
- Historia e imágenes: `datasets/processed/medreamm_pilot100/23574122`

### Lista A

- Match automático: `3`
1. Fissured tongue (lingua plicata)
2. Second branchial cleft anomaly with internal sinus (tonsillar fossa opening)
3. Torus palatinus (or torus mandibularis)
4. Oral cavity lymphatic malformation (lymphangioma)
5. Dermoid cyst of the floor of mouth/submental region

### Lista B

- Match automático: `0`
1. Accessory uvula (duplicated uvula/uvular polyp)
2. Lymphoid polyp (accessory tonsil) of the soft palate/uvula
3. Lymphangioma (lymphatic malformation) of the soft palate/uvula
4. Squamous papilloma of the uvula/soft palate
5. Pleomorphic adenoma of minor salivary glands (soft palate)
