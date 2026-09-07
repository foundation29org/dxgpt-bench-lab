# Listas de DxGPT — ronda 2 (20 unmatched + 16 LLM)

Escribe el veredicto en [david_deliverable_ronda2.md](david_deliverable_ronda2.md), no aquí.

La guía está en [../MEDICAL_REVIEW_RONDA2.md](../MEDICAL_REVIEW_RONDA2.md).

Historia e imágenes de cada id: `datasets/processed/medreamm_pilot100/<id>/`

Estas propuestas son las de la corrida T+I de 100 casos. Cinco ids de
ronda 1 están prellenados en el entregable (confírmalos). `24174966` y
`27074070` hay que volver a juzgar: la lista cambió respecto al piloto de 25.

Criterio (el mismo que en ronda 1): misma entidad diagnóstica, no
«parecida». Si ninguna propuesta es el gold, posición `0`. Si el programa
dijo `0` y tú también, el juez acertó (`correcto`).

---

## A — Casos sin match automático (20)

El programa dijo que ninguna propuesta es el gold. Aquí se esconden los falsos negativos.

### 24174966 **(la lista cambió respecto al piloto 25; vuelve a juzgar)**

- Gold: **Primary cardiac angiofibroma**
- El programa: `NO_MATCH` (posición `0`)
- Historia e imágenes: `datasets/processed/medreamm_pilot100/24174966`

Propuestas:
1. Cardiac fibroma (left ventricular)
2. Left ventricular thrombus
3. Cardiac myxoma (ventricular)
4. Papillary fibroelastoma
5. Cardiac hemangioma


### 25995698

- Gold: **Extralobar pulmonary sequestration**
- El programa: `NO_MATCH` (posición `0`)
- Historia e imágenes: `datasets/processed/medreamm_pilot100/25995698`

Propuestas:
1. Splenic infarction
2. Left lower lobe pneumonia with pleurisy
3. Splenic abscess
4. Accessory spleen torsion/infarction
5. Acute pancreatitis
6. Acute pyelonephritis (left-sided)


### 27656661 **(ronda 1; confirma)**

- Gold: **Multiple sclerosis-like disorder**
- El programa: `NO_MATCH` (posición `0`)
- Historia e imágenes: `datasets/processed/medreamm_pilot100/27656661`

Propuestas:
1. Primary progressive multiple sclerosis (PPMS)
2. Hereditary spastic paraplegia (HSP), complex form with optic neuropathy
3. OPA1-related dominant optic atrophy plus (DOA+)
4. HTLV-1 associated myelopathy/tropical spastic paraparesis (HAM/TSP)
5. Myelin oligodendrocyte glycoprotein antibody-associated disease (MOGAD)
6. Cervical/thoracic spondylotic myelopathy


### 30687305 **(ronda 1; confirma)**

- Gold: **Refractory cytopenias with multilineage dysplasia**
- El programa: `NO_MATCH` (posición `0`)
- Historia e imágenes: `datasets/processed/medreamm_pilot100/30687305`

Propuestas:
1. Myeloid/lymphoid neoplasm with eosinophilia (myeloproliferative hypereosinophilic syndrome, e.g., PDGFRA/PDGFRB/FGFR1-related)
2. Chronic eosinophilic pneumonia
3. Cryptogenic organizing pneumonia (COP)
4. Eosinophilic granulomatosis with polyangiitis (EGPA)
5. Allergic bronchopulmonary aspergillosis (ABPA)


### 27074070 **(la lista cambió respecto al piloto 25; vuelve a juzgar)**

- Gold: **Mixed-cellularity subtype of classic Hodgkin's lymphoma**
- El programa: `NO_MATCH` (posición `0`)
- Historia e imágenes: `datasets/processed/medreamm_pilot100/27074070`

Propuestas:
1. Crohn's disease (pediatric inflammatory bowel disease)
2. Intestinal tuberculosis
3. Non-Hodgkin lymphoma with gastrointestinal involvement
4. Langerhans cell histiocytosis with gastrointestinal/hepatic involvement
5. Amebic colitis with possible liver abscess (Entamoeba histolytica)
6. Hemophagocytic lymphohistiocytosis (secondary HLH)


### 24054536

- Gold: **Peripheral air embolism**
- El programa: `NO_MATCH` (posición `0`)
- Historia e imágenes: `datasets/processed/medreamm_pilot100/24054536`

Propuestas:
1. Paradoxical systemic air embolism via patent foramen ovale (PFO)
2. Venous air embolism (pulmonary air embolism)
3. Coronary air embolism causing acute coronary syndrome (NSTEMI)
4. Transient ischemic attack due to cerebral air embolism (paradoxical)
5. Acute pulmonary embolism (non-air thromboembolism) – less likely


### 29748223

- Gold: **Oesophageal cancer**
- El programa: `NO_MATCH` (posición `0`)
- Historia e imágenes: `datasets/processed/medreamm_pilot100/29748223`

Propuestas:
1. Dermatomyositis (idiopathic)
2. Paraneoplastic dermatomyositis (likely associated with esophageal malignancy)
3. Polymyositis
4. Inclusion body myositis
5. Immune-mediated necrotizing myopathy (e.g., statin-associated or anti-HMGCR/anti-SRP)


### 27332906

- Gold: **Iododerma**
- El programa: `NO_MATCH` (posición `0`)
- Historia e imágenes: `datasets/processed/medreamm_pilot100/27332906`

Propuestas:
1. Acute generalized exanthematous pustulosis (drug-induced, likely from iodinated contrast)
2. Stevens–Johnson syndrome/toxic epidermal necrolysis (drug-induced)
3. Sweet syndrome (acute febrile neutrophilic dermatosis, drug-induced)
4. Generalized pustular psoriasis (von Zumbusch type)
5. Bullous fixed drug eruption


### 32340587

- Gold: **Clear cell renal cell carcinoma**
- El programa: `NO_MATCH` (posición `0`)
- Historia e imágenes: `datasets/processed/medreamm_pilot100/32340587`

Propuestas:
1. Infrarenal abdominal aortic aneurysm (AAA)
2. Right hydronephrosis due to extrinsic ureteral compression (e.g., from aneurysmal iliac/aortic enlargement)
3. Ureterolithiasis with obstructive uropathy
4. Urothelial carcinoma of the ureter causing obstruction
5. Autosomal dominant polycystic kidney disease (ADPKD)


### N-10000032

- Gold: **Pancreatic ductal adenocarcinoma**
- El programa: `NO_MATCH` (posición `0`)
- Historia e imágenes: `datasets/processed/medreamm_pilot100/N-10000032`

Propuestas:
1. Distal extrahepatic cholangiocarcinoma (bile-duct adenocarcinoma)
2. Choledocholithiasis (common bile duct stone) with obstructive jaundice
3. Primary sclerosing cholangitis
4. IgG4-related sclerosing cholangitis (with or without autoimmune pancreatitis)
5. Liver fluke infection (clonorchiasis/Opisthorchis) causing cholangitis/obstructive jaundice
6. Acute viral hepatitis (e.g., hepatitis A or E) with cholestatic presentation


### 26819809

- Gold: **Malignant gastrointestinal stromal tumor**
- El programa: `NO_MATCH` (posición `0`)
- Historia e imágenes: `datasets/processed/medreamm_pilot100/26819809`

Propuestas:
1. Gastrointestinal stromal tumor (GIST) of the stomach
2. Pancreatic neuroendocrine tumor (nonfunctional)
3. Pancreatic ductal adenocarcinoma
4. Primary gastric lymphoma (e.g., diffuse large B-cell lymphoma or MALT lymphoma)
5. Retroperitoneal/mesenteric liposarcoma
6. Desmoid-type fibromatosis (intraabdominal/mesenteric)


### 24910386

- Gold: **Ischaemic scalp lesions**
- El programa: `NO_MATCH` (posición `0`)
- Historia e imágenes: `datasets/processed/medreamm_pilot100/24910386`

Propuestas:
1. Critical proximal common carotid artery stenosis/occlusion with scalp ischemia
2. Giant cell arteritis (temporal arteritis) with scalp necrosis
3. Subclavian steal syndrome (proximal subclavian/brachiocephalic stenosis)
4. Cardiac arrhythmia causing recurrent syncope with secondary traumatic/pressure-related scalp ulcer
5. Carotid sinus hypersensitivity/neurocardiogenic syncope


### 23752113

- Gold: **Prostatic adenocarcinoma**
- El programa: `NO_MATCH` (posición `0`)
- Historia e imágenes: `datasets/processed/medreamm_pilot100/23752113`

Propuestas:
1. Acute calculous cholecystitis
2. Acalculous cholecystitis
3. Choledocholithiasis with transient obstruction
4. Gallstone pancreatitis (resolved)
5. Malignant biliary obstruction from metastatic disease (e.g., prostate cancer metastasis to cystic duct/gallbladder or perihilar nodes)
6. Primary gallbladder carcinoma


### N-10000050

- Gold: **Cryptococcal pneumonia**
- El programa: `NO_MATCH` (posición `0`)
- Historia e imágenes: `datasets/processed/medreamm_pilot100/N-10000050`

Propuestas:
1. Lung abscess (bacterial, likely anaerobic)
2. Necrotizing pneumonia
3. Pulmonary tuberculosis (post-primary, cavitary)
4. Cavitating squamous cell carcinoma of the lung
5. Organizing pneumonia (cryptogenic or post-infectious)
6. Thoracic actinomycosis (aspiration-related)


### 23574122

- Gold: **Torus palatinus**
- El programa: `NO_MATCH` (posición `0`)
- Historia e imágenes: `datasets/processed/medreamm_pilot100/23574122`

Propuestas:
1. Accessory uvula (duplicated uvula/uvular polyp)
2. Lymphoid polyp (accessory tonsil) of the soft palate/uvula
3. Lymphangioma (lymphatic malformation) of the soft palate/uvula
4. Squamous papilloma of the uvula/soft palate
5. Pleomorphic adenoma of minor salivary glands (soft palate)


### 19721837

- Gold: **Acute hypereosinophilic syndrome**
- El programa: `NO_MATCH` (posición `0`)
- Historia e imágenes: `datasets/processed/medreamm_pilot100/19721837`

Propuestas:
1. Idiopathic hypereosinophilic syndrome (HES) with central nervous system involvement
2. Eosinophilic myocarditis/Loeffler endocarditis
3. Myeloid/lymphoid neoplasm with eosinophilia (e.g., PDGFRA/B or FGFR1 rearrangement)
4. Eosinophilic granulomatosis with polyangiitis (EGPA, Churg–Strauss syndrome)
5. Helminthic parasitic infection (e.g., toxocariasis or strongyloidiasis) with systemic eosinophilia
6. Primary angiitis of the central nervous system (PACNS)


### 26958738

- Gold: **Meningoencephalitis**
- El programa: `NO_MATCH` (posición `0`)
- Historia e imágenes: `datasets/processed/medreamm_pilot100/26958738`

Propuestas:
1. Cerebral venous sinus thrombosis (CVST)
2. Dengue-associated neurovascular complications (encephalitis/vasculopathy or CVST)
3. Varicella-zoster virus (VZV) vasculopathy
4. Bacterial meningitis with secondary cerebrovascular complications
5. Rickettsial spotted fever or typhus group infection with CNS involvement
6. Infective endocarditis with septic cerebral emboli


### 28620010

- Gold: **Right femoral neck fracture**
- El programa: `NO_MATCH` (posición `0`)
- Historia e imágenes: `datasets/processed/medreamm_pilot100/28620010`

Propuestas:
1. Emphysematous cystitis
2. Bilateral subcapital femoral neck fractures
3. Complicated urinary tract infection
4. Osteoporosis (fragility fracture risk)
5. Delirium secondary to infection (UTI-related) in a patient with dementia


### 28706431

- Gold: **Primary pancreatic T-cell/histiocyte-rich large B-cell lymphoma**
- El programa: `NO_MATCH` (posición `0`)
- Historia e imágenes: `datasets/processed/medreamm_pilot100/28706431`

Propuestas:
1. Pancreatic ductal adenocarcinoma (head of pancreas)
2. Distal (extrahepatic) cholangiocarcinoma
3. Ampullary carcinoma
4. Choledocholithiasis with obstructive jaundice
5. IgG4-related sclerosing cholangitis/autoimmune pancreatitis
6. Primary hepatic or biliary tract lymphoma (extranodal lymphoma causing biliary obstruction)


### 28104685

- Gold: **Bicondylar tibial plateau fracture**
- El programa: `NO_MATCH` (posición `0`)
- Historia e imágenes: `datasets/processed/medreamm_pilot100/28104685`

Propuestas:
1. Lateral tibial plateau split-depression fracture (Schatzker II)
2. Tibial spine (ACL) avulsion fracture
3. Posterior cruciate ligament (PCL) injury
4. Knee dislocation (spontaneously reduced) with multiligament injury
5. Traumatic meniscal tear (lateral more likely)


---

## B — Matches que decidió el juez LLM (16)

El programa dio por buena una propuesta. Aquí se esconden los falsos positivos.

### 27068836 **(ronda 1; confirma)**

- Gold: **Full-thickness oesophageal segment destruction**
- El programa aceptó la posición `1` (método `LLM_JUDGMENT`)
- Historia e imágenes: `datasets/processed/medreamm_pilot100/27068836`

Propuestas:
1. Esophageal perforation with descending mediastinitis (likely secondary to cervical hardware erosion)
2. Cervical vertebral osteomyelitis/discitis with paraspinal abscess
3. Spinal epidural abscess (cervicothoracic)
4. Instrumentation (hardware)-associated chronic infection with sinus/abscess formation
5. Retropharyngeal/paraesophageal abscess with mediastinal extension
6. Tuberculous spondylitis (Pott disease) with cold paraspinal abscess


### 21424749 **(ronda 1; confirma)**

- Gold: **Mitochondrial disease**
- El programa aceptó la posición `1` (método `LLM_JUDGMENT`)
- Historia e imágenes: `datasets/processed/medreamm_pilot100/21424749`

Propuestas:
1. MERRF-spectrum mitochondrial disease (mtDNA tRNA-Lys mutation)
2. POLG-related mitochondrial ataxia–myopathy spectrum
3. Inclusion body myositis (IBM)
4. Myofibrillar myopathy (e.g., desmin-related myopathy)
5. Spinocerebellar ataxia (e.g., SCA6)


### 23281978 **(ronda 1; confirma)**

- Gold: **ST-segment elevation myocardial infarction**
- El programa aceptó la posición `1` (método `LLM_JUDGMENT`)
- Historia e imágenes: `datasets/processed/medreamm_pilot100/23281978`

Propuestas:
1. Acute anterior ST-elevation myocardial infarction (LAD territory)
2. Polycythemia vera (myeloproliferative neoplasm, likely JAK2-mutated)
3. Essential thrombocythemia (myeloproliferative neoplasm)
4. Gastroesophageal reflux disease (GERD) with reflux esophagitis
5. Coronary vasospasm (Prinzmetal/variant angina)
6. Acute myopericarditis


### 27709474

- Gold: **Phosphaturic mesenchymal tumor**
- El programa aceptó la posición `1` (método `LLM_JUDGMENT`)
- Historia e imágenes: `datasets/processed/medreamm_pilot100/27709474`

Propuestas:
1. Tumor-induced osteomalacia (phosphaturic mesenchymal tumor with excess FGF23)
2. Anticonvulsant (phenytoin)-induced osteomalacia
3. Primary hyperparathyroidism
4. Fanconi syndrome (proximal renal tubular dysfunction) with phosphate wasting
5. Vitamin D deficiency osteomalacia (malabsorption or nutritional)


### 27514369

- Gold: **Native valve infective endocarditis**
- El programa aceptó la posición `1` (método `LLM_JUDGMENT`)
- Historia e imágenes: `datasets/processed/medreamm_pilot100/27514369`

Propuestas:
1. Infective endocarditis (mitral valve) due to group A β-hemolytic streptococcus
2. Cardioembolic ischemic stroke secondary to infective endocarditis
3. Acute severe mitral regurgitation with acute decompensated heart failure (secondary to IE)
4. Splenic infarction/abscess due to septic emboli from infective endocarditis
5. Brain abscess secondary to septic emboli (differential)


### 30766756

- Gold: **Primary yolk sac tumor of intestine**
- El programa aceptó la posición `1` (método `LLM_JUDGMENT`)
- Historia e imágenes: `datasets/processed/medreamm_pilot100/30766756`

Propuestas:
1. Extragonadal yolk sac tumor (endodermal sinus tumor) of the small intestine
2. Hepatoid adenocarcinoma of the small intestine
3. Primary intestinal yolk sac tumor with hepatoid differentiation
4. Metastatic hepatoblastoma or hepatocellular carcinoma to small intestine
5. Gastrointestinal stromal tumor (GIST) of the small intestine
6. Intestinal (Burkitt) lymphoma


### 32046748

- Gold: **Progressive multifocal leukoencephalopathy**
- El programa aceptó la posición `1` (método `LLM_JUDGMENT`)
- Historia e imágenes: `datasets/processed/medreamm_pilot100/32046748`

Propuestas:
1. Progressive multifocal leukoencephalopathy (PML) due to JC virus
2. PML-associated immune reconstitution inflammatory syndrome (PML-IRIS)
3. Multiple sclerosis relapse
4. Posterior reversible encephalopathy syndrome (PRES)
5. JC virus granule cell neuronopathy (JCV GCN)


### 23482507

- Gold: **Cavernous hemangioma of bone**
- El programa aceptó la posición `1` (método `LLM_JUDGMENT`)
- Historia e imágenes: `datasets/processed/medreamm_pilot100/23482507`

Propuestas:
1. Intraosseous hemangioma (venous malformation) of the ilium with soft‑tissue extension
2. Aneurysmal bone cyst (ABC) of the ilium
3. Fibrous dysplasia of the pelvis
4. Ewing sarcoma of the ilium
5. Giant cell tumor (GCT) of bone involving the ilium/acetabulum
6. Osteoblastoma of the pelvis


### N-10000086

- Gold: **BRAF inhibitor-related toxic effects**
- El programa aceptó la posición `2` (método `LLM_JUDGMENT`)
- Historia e imágenes: `datasets/processed/medreamm_pilot100/N-10000086`

Propuestas:
1. Disseminated histoplasmosis with granulomatous hepatitis
2. BRAF/MEK inhibitor–associated pyrexia syndrome (dabrafenib/trametinib)
3. Sepsis of unknown origin (possible biliary source)
4. Hemophagocytic lymphohistiocytosis (HLH), secondary
5. Miliary/disseminated tuberculosis with hepatic involvement
6. Sarcoidosis with hepatic and pulmonary involvement


### 23800107

- Gold: **Triple A syndrome**
- El programa aceptó la posición `1` (método `LLM_JUDGMENT`)
- Historia e imágenes: `datasets/processed/medreamm_pilot100/23800107`

Propuestas:
1. Allgrove (Triple A/4A/5A) syndrome due to AAAS gene mutation
2. Familial glucocorticoid deficiency (ACTH resistance due to MC2R/MRAP and related genes)
3. X-linked adrenoleukodystrophy (X-ALD)
4. Chiari I malformation with cervical syringomyelia
5. Familial dysautonomia (Riley–Day syndrome, IKBKAP/ELP1-related)
6. AAMR syndrome (alacrima, achalasia, intellectual disability due to GMPPA-related congenital disorder of glycosylation)


### 28302624

- Gold: **Intervertebral disc prolapse**
- El programa aceptó la posición `1` (método `LLM_JUDGMENT`)
- Historia e imágenes: `datasets/processed/medreamm_pilot100/28302624`

Propuestas:
1. Lumbar disc herniation with radiculopathy
2. Lumbar spinal stenosis (degenerative)
3. Cauda equina syndrome from large disc extrusion
4. Spinal epidural abscess
5. Piriformis syndrome (extra-spinal sciatica)


### 27797319

- Gold: **Germinoma**
- El programa aceptó la posición `1` (método `LLM_JUDGMENT`)
- Historia e imágenes: `datasets/processed/medreamm_pilot100/27797319`

Propuestas:
1. Suprasellar germinoma (pituitary stalk/hypothalamic germ cell tumor)
2. Craniopharyngioma (suprasellar cystic/solid epithelial tumor)
3. Langerhans cell histiocytosis with hypothalamic–pituitary axis involvement
4. Neurosarcoidosis involving the pituitary stalk/hypothalamus
5. Lymphocytic infundibuloneurohypophysitis
6. Nonfunctioning pituitary macroadenoma with stalk effect


### 22563559

- Gold: **T-lymphoblastic leukemia**
- El programa aceptó la posición `1` (método `LLM_JUDGMENT`)
- Historia e imágenes: `datasets/processed/medreamm_pilot100/22563559`

Propuestas:
1. T-lymphoblastic leukemia/lymphoma (T-ALL), mature TCR-positive variant with TCRAD translocation
2. T-cell prolymphocytic leukemia (T-PLL)
3. Early T-cell precursor acute lymphoblastic leukemia (ETP-ALL)
4. Adult T-cell leukemia/lymphoma (ATLL, HTLV-1 associated)


### 25336332

- Gold: **Squamous cell carcinoma of tonsil**
- El programa aceptó la posición `1` (método `LLM_JUDGMENT`)
- Historia e imágenes: `datasets/processed/medreamm_pilot100/25336332`

Propuestas:
1. HPV-positive oropharyngeal squamous cell carcinoma (tonsil/base of tongue) with cervical metastasis
2. Nasopharyngeal carcinoma
3. Hodgkin or non-Hodgkin lymphoma involving cervical nodes
4. Metastatic papillary thyroid carcinoma to cervical lymph node
5. Tuberculous cervical lymphadenitis (scrofula)
6. Second branchial cleft cyst with superimposed infection/inflammation


### 25282086

- Gold: **Secondary tumoral calcinosis**
- El programa aceptó la posición `1` (método `LLM_JUDGMENT`)
- Historia e imágenes: `datasets/processed/medreamm_pilot100/25282086`

Propuestas:
1. Uremic tumoral calcinosis (secondary hyperparathyroidism–related soft‑tissue calcification)
2. Calcific uremic arteriolopathy (calciphylaxis)
3. Myositis ossificans (heterotopic ossification)
4. Tophaceous gout
5. Extraskeletal osteosarcoma or calcified soft-tissue sarcoma


### 28472977

- Gold: **SHORT syndrome**
- El programa aceptó la posición `1` (método `LLM_JUDGMENT`)
- Historia e imágenes: `datasets/processed/medreamm_pilot100/28472977`

Propuestas:
1. SHORT syndrome (PIK3R1-related lipodystrophic syndrome)
2. Russell-Silver syndrome
3. Treacher Collins syndrome (mandibulofacial dysostosis)
4. 3M syndrome
5. CHARGE syndrome
