# Pipeline V4 vs V5 — mismas listas DDX

- Baseline (V4): `../../../multimodal_beta/outputs/judge_audit/all256_gpt56terra_low_strict/evaluation_details.txt`
- Candidate (V5): `output/all_256_clean/juanjo_classic_v2/gpt_5_6_terra_low_translated_en/20261027194849/evaluation_details.txt`
- Casos comparados: 256

| Evaluación | R@1 | R@3 | R@5 | Cobertura |
|---|---:|---:|---:|---:|
| V4 strict | 63.3% (162) | 80.1% (205) | 83.2% (213) | 83.2% (213) |
| V5 estricta (grado 2) | 69.9% (179) | 80.1% (205) | 82.0% (210) | 82.0% (210) |
| V5 laxa (grado ≥ 1) | 89.1% (228) | 93.4% (239) | 95.7% (245) | 95.7% (245) |

## Aciertos de V4 que V5 no da por buenos (14)

Agrupados por la capa de V4 que los decidía. «Grado V5» es la nota que V5 da a la opción que V4 contaba.

### BERT_AUTOCONFIRM (1)

| Caso | Gold | V4 | Grado V5 |
|---|---|---|---:|
| S173 | Mucolipidosis type III alpha/beta | P5 Mucolipidosis II/III (GNPTAB-related mucolipidosis, especially mucolipidosis III alpha/beta) (BERT_AUTOCONFIRM) | 1 |

### ICD10_PARENT (2)

| Caso | Gold | V4 | Grado V5 |
|---|---|---|---:|
| B82 | Sickle Cell Trait with Hematuria | P1 Sickle cell anemia (hemoglobin SS disease) (ICD10_PARENT) | 1 |
| Q409 | Tumor stage | P2 Early-stage screen-detected breast cancer (ICD10_PARENT) | 0 |

### ICD10_SIBLING (9)

| Caso | Gold | V4 | Grado V5 |
|---|---|---|---:|
| B136 | Cerebral atrophy | P2 Delirium due to an underlying medical condition (ICD10_SIBLING) | 1 |
| B23 | Meiotic nondisjunction | P1 Klinefelter syndrome (47,XXY) (ICD10_SIBLING) | 1 |
| B51 | Constrictive pericarditis | P1 Cardiac tamponade due to pericardial effusion (ICD10_SIBLING) | 1 |
| Q669 | Decreased release of glycine | P1 Neonatal tetanus (ICD10_SIBLING) | 1 |
| R193 | Carnitine palmitoyltransferase I deficiency | P2 Multiple acyl-CoA dehydrogenase deficiency (MADD) (ICD10_SIBLING) | 1 |
| R601 | Bethlem myopathy 1 | P3 RYR1-related congenital myopathy (ICD10_SIBLING) | 0 |
| S10 | Rare Cutaneous Lupus Erythematosus | P2 Subacute cutaneous lupus erythematosus (SCLE) (ICD10_SIBLING) | 1 |
| S19 | Renal Dysplasia | P3 Autosomal dominant polycystic kidney disease (ADPKD) (ICD10_SIBLING) | 0 |
| S30 | Fetal Cytomegalovirus Syndrome | P3 Congenital rubella syndrome (ICD10_SIBLING) | 0 |

### LLM_JUDGMENT (2)

| Caso | Gold | V4 | Grado V5 |
|---|---|---|---:|
| B139 | Atrioventricular node dysfunction | P3 Complete (third-degree) atrioventricular block (LLM_JUDGMENT) | 1 |
| R917 | Brugada Syndrome, BrS | P4 Danon disease (LLM_JUDGMENT) | 0 |

## Aciertos nuevos en V5 (11)

| Caso | Gold | V5 |
|---|---|---|
| B110 | Ovarian tumor | P1 Sertoli-Leydig cell tumor of the ovary (JUDGE) |
| B55 | Left ventricular hypertrophy | P2 Hypertrophic cardiomyopathy (JUDGE) |
| Q1103 | Increased prothrombin time due to liver dysfunction | P2 Alcohol-related cirrhosis with liver failure (JUDGE) |
| Q4527 | Graft-versus-host disease | P1 Acute graft-versus-host disease (acute GVHD) (JUDGE) |
| Q6173 | Mitochondrial myopathy with ragged red fibers | P1 MELAS syndrome (Mitochondrial Encephalomyopathy, Lactic Acidosis, and Stroke-like Episodes) (JUDGE) |
| Q952 | Non-Hodgkin’s Lymphoma | P1 Post-transplant lymphoproliferative disorder (PTLD), likely monomorphic diffuse large B-cell lymphoma (JUDGE) |
| S118 | Proximal 16p11.2 Microdeletion Syndrome | P1 16p11.2 deletion syndrome (JUDGE) |
| S180 | Rare Lymphatic Malformation | P1 Hennekam lymphangiectasia-lymphedema syndrome (JUDGE) |
| S4 | Endocrine Gland Tumor | P1 Thyroid cancer (JUDGE) |
| T385 | Hypertensive crisis | P1 Crisis hipertensiva sin daño agudo de órgano diana (urgencia hipertensiva) (JUDGE) |
| T795 | Lower respiratory infection | P1 Community-acquired pneumonia (JUDGE) |

## Cambios de posición (12)

| Caso | Gold | V4 | V5 |
|---|---|---|---|
| B27 | Obstructive shock | P3 Acute right ventricular failure due to obstructive shock (SNOMED_MATCH) | P1 Massive pulmonary embolism (JUDGE) |
| Q1052 | Fulminant Hepatic Failure | P2 Acute liver failure with hepatic encephalopathy (LLM_JUDGMENT) | P1 Fulminant acute hepatitis B causing acute liver failure (JUDGE) |
| Q5239 | Meningococcal Septicemia | P2 Meningococcal meningitis due to Neisseria meningitidis (ICD10_SIBLING) | P1 Meningococcemia due to Neisseria meningitidis (JUDGE) |
| Q6130 | Heart failure with reduced ejection fraction (HFrEF) | P3 Secondary tricuspid regurgitation from pulmonary hypertension/right-sided heart failure (ICD10_SIBLING) | P1 Heart failure with reduced ejection fraction due to ischemic cardiomyopathy (JUDGE) |
| Q6182 | Boerhaave syndrome (Transmural esophageal rupture) | P3 Mallory-Weiss syndrome (ICD10_SIBLING) | P1 Boerhaave syndrome (spontaneous esophageal rupture) (JUDGE) |
| Q815 | Rheumatic heart disease with mitral stenosis | P2 Atrial fibrillation secondary to mitral stenosis (SNOMED_MATCH) | P1 Rheumatic mitral stenosis causing congestive heart failure (ICD10_EXACT) |
| Q933 | Ovarian Metastasis from Gastric Cancer | P2 Diffuse-type gastric adenocarcinoma (linitis plastica) with ovarian metastases (SNOMED_MATCH) | P1 Krukenberg tumor due to metastatic gastric adenocarcinoma (JUDGE) |
| R206 | Glycerol kinase deficiency | P2 Isolated glycerol kinase deficiency (SNOMED_MATCH) | P1 Complex glycerol kinase deficiency (X-linked contiguous gene deletion syndrome) (JUDGE) |
| S182 | Hematodermic Neoplasm CD4+/CD56+ | P4 Peripheral T-cell lymphoma, not otherwise specified (PTCL-NOS), with leukemic and cutaneous involvement (ICD10_SIBLING) | P1 Blastic plasmacytoid dendritic cell neoplasm (BPDCN) (JUDGE) |
| S24 | Renal Cell Carcinoma | P2 Renal cell carcinoma with pulmonary and possible bone metastases (SNOMED_MATCH) | P1 Metastatic renal cell carcinoma (clear cell renal cell carcinoma) (JUDGE) |
| T208 | Acute conjunctivitis | P3 Acute conjunctivitis, likely viral (SNOMED_MATCH) | P1 Adenoviral pharyngoconjunctival infection (JUDGE) |
| T34 | Lymphoproliferative process | P2 Primary bone lymphoma or secondary osseous lymphoma (LLM_JUDGMENT) | P1 Multiple myeloma (JUDGE) |
