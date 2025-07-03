# Dataset Origins & ETL Synopsis

## 1. Source Datasets  
| Alias | Full Name | Provider / URL |
|-------|-----------|----------------|
| `medbullet5op` | MedBulletS – 5-option MCQ | https://huggingface.co/datasets/JesseLiu/medbulltes5op |
| `medqa_usmle4op` | MedQA USMLE – 4-option MCQ | https://huggingface.co/datasets/GBaker/MedQA-USMLE-4-options |
| `procheck` | ProCheck rare-disease cases | Internal partner (MD, 20 y exp.) |

ProCheck cadence: 5-case pilot (`example_split`) + 1 curated rare case/week (`case1`, `case2`, …).

## 2. ETL Workflow (MedBulletS & MedQA)
1. Column pruning – keep `{case_text, diagnosis}`; drop `explanation`, distractors, keywords.
2. Diagnosis filter (GPT-4o) – retain `row_type == condition_diagnosis`; discard treatment/medication prompts (`clinical_action`).
3. Augmentation – tag `case_complexity`, `diagnosis_severity`, and map diagnosis → ICD-10 (utils.icd10.ICD10Taxonomy).

## 3. ProCheck Alignment
Same ETL logic; low volume enables occasional manual checks via ChatGPT/Claude.

## 4. Status
ETL complete – datasets ready for downstream evaluation and benchmarking.