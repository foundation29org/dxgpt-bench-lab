# DxGPT Evaluation — Roadmap completo

**Objetivo final:** Poder publicar una comparativa de DxGPT contra los mejores sistemas del paper de Nature (DeepRare, 2025) sobre los mismos datasets, con métricas equivalentes y resultados auditables.

**Última actualización:** 2026-04-22  
**Estado actual:** Fase 0 ✅, Fase 1 ✅, Fase 2 ✅, Fase 3 ✅, Fase 4 🔄 (DDD completado; resto aspiracional)

Este documento es el roadmap y la bitacora de decisiones del proyecto.

- Para el estado actual del benchmark: `bench/pipelines/pipeline_v4 - fork/main/README.md`
- Para ejecutar el pipeline: `bench/pipelines/pipeline_v4 - fork/main/GUIA_EVALUACION.md`
- Para el historial completo de runs: `bench/pipelines/pipeline_v4 - fork/main/output/rankingV2.txt`

---

## Visión general

```
FASE 0 [✅ HECHA]    Línea base con pipeline actual
FASE 1 [✅ HECHA]    Limpiar dataset + arquitectura de datos
FASE 2 [✅ HECHA]    Integrar datasets del paper de Nature
FASE 3 [✅ HECHA]    Recall@K + comparativa pública cerrados
FASE 4 [🔄 PARCIAL] DDD completado; MIMIC-IV y validación clínica siguen como aspiracional
```

---

## Fase 0 — Línea base ✅ COMPLETADA

**Objetivo:** Entender el estado real del pipeline y establecer métricas comparables entre modelos.

### Pasos completados

- [x] **0.1** Ejecutar ablación completa sobre `all_275.json` con variables controladas:
  - Run A: gpt-4o + juez normalcalls + traducción → pos. 1.639, éxito 92.7%
  - Run B: gpt-4o + juez gemini-2.5-pro + traducción → pos. 1.646, éxito 95.6%
  - Paso 3: gpt-5-mini + juez gemini + traducción → pos. 1.653, éxito 96.4%
  - Paso 3c: gpt-4o + juez gemini + sin traducción → pos. 1.753, éxito 98.6%
- [x] **0.2** Documentar todos los runs en `rankingV2.txt` con parámetros explícitos
- [x] **0.3** Ejecutar `validation_checks.py` sobre `all_275.json` y documentar fallos
- [x] **0.4** Identificar causa de lentitud de gpt-5-mini (auto-upgrade Azure)
- [x] **0.5** Añadir métricas de tiempo al pipeline (`emulator.py`)
- [x] **0.6** Documentar hipótesis y conclusiones en `docs/pipeline/experiment-log.md`

### Conclusiones clave de la Fase 0

- gpt-4o y gpt-5-mini tienen calidad equivalente en all_275 (+0.8% a favor de mini)
- El juez gemini-2.5-pro recupera ~3% más de casos que normalcalls
- La traducción mejora `average_position` pero reduce ligeramente el total de matches
- El dataset all_275 **falla los gates de calidad** — no apto para publicación externa

---

## Fase 1 — Limpiar el dataset ✅ COMPLETADA

**Objetivo:** Tener un dataset base (`all_256_clean.json`) que pase los 8 gates del QA checker.

**Bloqueante para todo lo siguiente.** Sin esto, cualquier resultado publicado es cuestionable.

### Paso 1.1 — Eliminar label leakage (CRÍTICO) ✅ COMPLETADO (2026-04-16)

**Qué es:** 19 casos (7%) donde el diagnóstico correcto aparece literalmente en el texto clínico. El modelo hace pattern matching, no diagnóstico.

**Decisión del equipo (Bishop Decision #12):** ELIMINAR los 19 casos, no reescribirlos.
- Reescribir requiere 1-2 días de juicio clínico + QA manual con riesgo alto
- Eliminar es determinista, auditable y tarda <5 minutos
- 256 casos sigue siendo un dataset robusto (DeepRare usa 88–2.283 por dataset)

**Casos eliminados (19):** B133, J2, Q355, U2, U3, U5, U7, U8, U9, R10, R117, R123, R295, R360, R424, R443, R830, T1323, T741

**Output:** `bench/datasets/all_256.json` (275 − 19 = 256 casos)

**Criterio de aceptación:** `validation_checks.py` reporta Label Leakage PASS (0/256, 0%)

> ⚠️ Ripley (Decision #11): documentar la caída esperada de scores (~5–8%) al re-ejecutar sobre all_256 — es una caída sana que refleja la eliminación del leakage artificial, no una regresión del modelo.

---

### Paso 1.2 — Eliminar prefijo boilerplate (ALTO) ✅ COMPLETADO (2026-04-16)

**Qué es:** De los 57 casos originales con boilerplate, 8 ya se eliminaron en el Paso 1.1 (solapaban con leakage). Quedaban **49 casos** en `all_256.json` con el prefijo sintético `"Motivo de consulta: Paciente acude a consulta para ser diagnosticado Anamnesis: Paciente de sexo desconocido..."`.

**Hallazgo importante durante la limpieza:** hay dos tipos de casos con `"Motivo de consulta"`:
- **49 casos R\*** — envoltorio sintético alrededor de síntomas HPO en inglés → boilerplate real, limpiado
- **28 casos T\*** — narrativa clínica real con cabeceras médicas estándar (edad, sexo, síntomas en prosa) → legítimos, NO tocados

**Acción:** Stripping del prefijo fijo + sufijo fijo (`Antecedentes: No hay antecedentes Exploracion: No se realiza Pruebas clinicas:`), conservando solo la lista de síntomas HPO.

**Output:** `bench/datasets/all_256_clean.json` (256 casos, boilerplate 0%)

---

### Paso 1.3 — Verificación QA ✅ COMPLETADO (2026-04-16)

Resultado real de `validation_checks.py` sobre `all_256_clean.json`:

```
✓ LABEL LEAKAGE      — PASS   0/256   (0.0%,  umbral ≤5%)
✓ BOILERPLATE PREFIX — PASS   0/256   (0.0%,  umbral <10%)
✓ TEMPLATE MARKERS   — PASS  28/256  (10.9%, umbral <40%)
✓ LIST-FORMAT        — PASS   0/256   (0.0%,  umbral ≤60%)
OVERALL: PASS ✅
```

**Comparativa antes / después:**

| Gate | all_275 (original) | all_256_clean (limpio) |
|------|-------------------|----------------------|
| Label Leakage | ❌ 6.9% (19 casos) | ✅ 0.0% (0 casos) |
| Boilerplate Prefix | ❌ 20.7% (57 casos) | ✅ 0.0% (0 casos) |
| Template Markers | ✅ 31.6% (87 casos) | ✅ 10.9% (28 casos) — solo T* reales |
| List-Format | ✅ 0.0% | ✅ 0.0% |
| **OVERALL** | **FAIL** | **PASS** |

> Los 28 casos T\* con Template Markers son narrativa clínica real (pacientes con edad, sexo, síntomas en prosa). El 10.9% está muy por debajo del umbral de 40% — sin riesgo.

> ⚠️ Ripley (Decision #11): la caída esperada de scores al re-ejecutar sobre all_256_clean es ~5–8% — es una caída sana que refleja la eliminación del leakage artificial, no una regresión del modelo.

---

### Paso 1.4 — Re-ejecutar modelos finalistas sobre `all_256_clean` ✅ COMPLETADO

Re-ejecutar los dos modelos finalistas sobre el dataset limpio para obtener la primera línea base honesta apta para publicación.

**Run 1.4-A: gpt-4o ✅ COMPLETADO (2026-04-16)**
- Modelo: `gpt-4o` · Juez: `gemini-2.5-pro` · Traducción: `true`
- Dataset: `bench/datasets/all_256_clean.json`
- Resultado: pos. media **1.545** · éxito **96.1% (246/256)**
- ⚠️ SapBERT activo solo desde caso 197/256 (reactivado durante el run) — 5 BERT matches

**Run 1.4-B: gpt-5-mini ✅ COMPLETADO (2026-04-16)**
- Modelo: `gpt-5-mini` · `reasoning_effort: low`
- Juez: `gemini-2.5-pro` · Traducción: `true`
- Dataset: `bench/datasets/all_256_clean.json`
- Resultado: pos. media **1.588** · éxito **97.7% (250/256)**
- ✅ SapBERT activo desde el inicio — primer run 100% limpio — 16 BERT matches (4 autoconfirm + 12)
- Velocidad: ~32–47s/caso · LLM_JUDGMENT: 71 (vs 87 en Run 1.4-A — BERT resolvió más casos)

**Comparativa completa — all_275 sucio vs. all_256_clean limpio:**

| Métrica | all_275 gpt-4o | all_275 gpt-5-mini | **all_256_clean gpt-4o** | **all_256_clean gpt-5-mini** |
|---------|---------------|-------------------|--------------------------|------------------------------|
| Avg position | 1.646 | 1.653 | **1.545** | **1.588** |
| Success % | 95.6% (263/275) | 96.4% (265/275) | **96.1% (246/256)** | **97.7% (250/256)** |
| LLM_JUDGMENT | 97 | — | 87 | 71 |
| BERT matches | 0 | 0 | 5 | 16 |

**Comparativa de parámetros fijos (ambos runs):** `temperature=0.1, max_tokens=12000, BERT_accept=0.8, BERT_autoconfirm=0.9`

**Conclusiones de Paso 1.4:**

1. **Limpiar el dataset mejoró los scores en ambos modelos** — el boilerplate español confundía activamente al LLM.
2. **gpt-4o supera a gpt-5-mini en average_position** (1.545 vs 1.588 — mejor ranking del diagnóstico correcto).
3. **gpt-5-mini supera en success%** (97.7% vs 96.1% — encuentra el diagnóstico en más casos, aunque a veces más abajo en la lista).
4. **SapBERT impacta la comparabilidad**: gpt-4o tuvo BERT parcial (5 matches), gpt-5-mini tuvo BERT completo (16 matches). Para resultados 100% comparables, ambos modelos deberían re-ejecutarse con SapBERT activo desde el inicio. Pendiente si se necesita para publicación.
5. **Línea base publicable establecida**: `all_256_clean` con ambos modelos es la primera línea base honesta de DxGPT.

---

### Paso 1.5 — Crear la arquitectura de datos en tres niveles ✅ COMPLETADO (2026-04-16)

**Por qué:** Antes de ingerir datos externos (Nature paper), necesitamos una estructura que garantice que nunca mezclamos datos sucios con limpios sin saberlo.

**Estructura creada:**

```
data29/data-repos/
├── raw/                              ← NIVEL 1: archivos originales (ya existía, en .gitignore)
│   ├── SOURCE_MANIFEST.yaml          ← NUEVO: documenta 7 fuentes (origen, idioma, licencia)
│   ├── ramedis.json
│   └── ...  (7 fuentes)
│
├── pre-normalization/                ← Pipeline ETL interno (ya existía)
├── post-normalization (server)/      ← Datasets internos servidos (ya existía)
│
├── normalized-by-source/             ← NIVEL 2: NUEVO — para datasets externos (Nature paper)
│   └── README.md                    ← schema estándar + reglas + fuentes pendientes (mygene2, ramedis_hpo)
│
└── curated-datasets/                 ← NIVEL 3: NUEVO — datasets de evaluación definitivos
    ├── README.md
    └── all_256_clean/
        ├── _metadata.yaml           ← composición, QA gates, historial de runs (2 runs)
        └── _lineage.txt             ← trazabilidad hasta raw/
```

**Adaptación respecto al plan original:**
- Los `_metadata` son `.yaml` en lugar de `.json` para evitar ser excluidos por `.gitignore` (regla `*.json`)
- `normalized-by-source/` se crea vacío (sin contenido) — se poblará en Fase 2 con mygene2 y ramedis_hpo
- El `SOURCE_MANIFEST.yaml` en `raw/` no se puede trackear en git (`.gitignore` excluye `data29/data-repos/raw`) — es documentación local

**Decisión de traducción — pre-traducir en Nivel 2, no en runtime:**

Pre-traducir al crear el dataset normalizado es mejor que traducir en cada ejecución. Razones:
- **Reproducibilidad**: mismo texto exacto en cada run (Azure Translator puede devolver variaciones menores entre llamadas)
- **Auditabilidad**: puedes inspeccionar exactamente qué texto recibió el modelo
- **Velocidad**: elimina N llamadas a Azure Translator por run
- **Resiliencia**: el pipeline no falla si Azure Translator está caído

**Schema recomendado para Nivel 2** — añadir campo `case_en` junto al original:
```json
{
  "id": "R1",
  "case": "texto original en el idioma fuente",
  "case_en": "texto pre-traducido al inglés (igual que case si ya era inglés)",
  "complexity": "C3",
  "diagnoses": ["..."],
  "source": "ramedis",
  "lang": "en"
}
```

El flag `TRANSLATE_CASE` en `config.yaml` se mantiene para ablaciones y para futuros datasets imprevistos. Para curated datasets del Nivel 3 el pipeline debería usar `case_en` directamente si el campo existe.

**Criterio de aceptación:** ✅ Cumplido — `all_256_clean` tiene `_metadata.yaml`, `_lineage.txt`, y QA PASS documentado.

---

## Fase 2 — Integrar datasets del paper de Nature ✅ COMPLETADA

**Prerequisito:** ✅ Fase 1 completa.

**Objetivo:** Evaluar DxGPT sobre los mismos datasets que usa DeepRare para poder hacer comparación directa.

### Paso 2.1 — Obtener los datasets de RareBench (Hugging Face) ✅ COMPLETADO (2026-04-16)

> ⚠️ **Corrección respecto al plan original**: RareCrowds (Foundation29) NO es la fuente correcta.
> Está desactualizado (última actualización: enero 2022) y no contiene los datasets del paper de Nature.
> La fuente real es **`chenxz/RareBench`** en Hugging Face.

**Fuentes reales del paper DeepRare:**

| Dataset | Fuente | Casos | Enfermedades | Notes |
|---------|--------|-------|-------------|-------|
| RAMEDIS | `chenxz/RareBench` en HuggingFace | 624 | 74 | Casos de investigadores europeos |
| MME | `chenxz/RareBench` en HuggingFace | 40 | 17 | Matchmaker Exchange (Canadá) |
| HMS | `chenxz/RareBench` en HuggingFace | 88 | 39 | Hannover Medical School |
| LIRICAL | `chenxz/RareBench` en HuggingFace | 370 | 252 | Multi-país |
| MyGene2 | Harvard Dataverse / proyecto Shepherd (Zitnik Lab) | 146 | 55 MONDO | Plataforma de compartición de pacientes |

**Formato de los datos (RareBench):**
```python
# Instalar dependencias
pip install datasets  # Hugging Face datasets library

# Descargar
from datasets import load_dataset
data = load_dataset('chenxz/RareBench', 'RAMEDIS', split='test')
# Cada caso tiene:
# { "Phenotype": "HP:0001250, HP:0000083, HP:0002120, ...",
#   "RareDisease": "OMIM:123456" }
```

Son **HPO codes**, no texto legible. El mapeo `HP:code → nombre` viene incluido:
```
phenotype_mapping.json   ← HP:0001250 → "Seizures"
disease_mapping.json     ← OMIM:123456 → "Disease name"
```

**Dónde descargar los ficheros de mapeo:**
```
https://github.com/chenxz1111/RareBench  ← ver carpeta mapping/
```

**Pasos de este paso:**
1. Instalar `pip install datasets`
2. Descargar RAMEDIS + MyGene2 (los dos prioritarios para comparar con DeepRare)
3. Descargar los ficheros de mapeo HPO y disease del repo GitHub de RareBench
4. Verificar que los datos se cargan correctamente

**Criterio de aceptación:** Datos descargados, mapeos disponibles localmente.

---

### Paso 2.2 — Convertir y normalizar RareBench datasets ✅ COMPLETADO (2026-04-16)

**Resultados de conversión y QA:**

| Dataset | Casos | HPO/caso (avg) | HPO desconocidos | QA | Label leakage |
|---------|-------|---------------|------------------|----|---------------|
| RAMEDIS | 624 | 10.1 (min 3, max 46) | 0 | ✅ PASS | 2.1% (13 casos — HPO names = disease name, esperado) |
| MME | 40 | 12.2 (min 3, max 26) | 0 | ✅ PASS | 0% |
| HMS | 88 | 19.4 (min 5, max 54) | 9 | ✅ PASS | 0% |
| LIRICAL | 370 | 14.3 (min 3, max 96) | 8 | ✅ PASS | 0.3% (1 caso) |

**Ficheros generados:**
```
data29/data-repos/normalized-by-source/
├── ramedis_hpo/ramedis_hpo_v1.json    ← 624 casos
├── mme_hpo/mme_hpo_v1.json           ← 40 casos
├── hms_hpo/hms_hpo_v1.json           ← 88 casos
└── lirical_hpo/lirical_hpo_v1.json   ← 370 casos
```

**Schema de salida (compatible con pipeline DxGPT):**
```json
{
  "id": "RAMEDIS_000",
  "case": "Death in infancy, Metabolic acidosis, Decreased methylmalonyl-CoA mutase activity, Death in childhood",
  "case_en": "(igual que case — ya está en inglés)",
  "diagnoses": [{"name": "Vitamin B12-unresponsive methylmalonic acidemia", "normalized_text": "...", 
                 "severity": "S0", "medical_codes": {"icd10": [], "snomed": [], "omim": ["251000"], "orpha": ["27"]}}],
  "source": "ramedis_hpo",
  "lang": "en",
  "hpo_codes": ["HP:0001522", "HP:0001942", "HP:0003210", "HP:0003819"]
}
```

**Nota sobre "label leakage" en RAMEDIS (13 casos / 2.1%):** Los datos HPO contienen fenotipos cuyo nombre es idéntico al de la enfermedad (ej: "Methylmalonic acidemia" es a la vez un HPO term y el nombre del diagnóstico). Esto es inherente a los datos HPO — no es un error, es la naturaleza de la ontología. Está por debajo del umbral del 5% y se acepta como válido.

> ⚠️ El `data29/data-repos/raw/ramedis.json` tiene el boilerplate español añadido artificialmente.
> **No usar ese fichero para este paso.** Usar el RAMEDIS de RareBench (HPO nativo).

**Conversión de HPO codes a texto DxGPT:**
```python
# HP:0001250 → "Seizures"
# HP:0000083 → "Renal insufficiency"
# Resultado: "Seizures, Renal insufficiency, ..."
```

Cada caso se convierte de lista de códigos a string de nombres separados por comas.
Sin narrativa clínica — solo la lista de síntomas (esto es exactamente como evaluó DeepRare).

**Schema DxGPT de salida:**
```json
{
  "id": "RAMEDIS_001",
  "case": "Seizures, Renal insufficiency, Intellectual disability, ...",
  "case_en": "Seizures, Renal insufficiency, Intellectual disability, ...",
  "diagnoses": ["Diagnosis Name"],
  "source": "ramedis_hpo",
  "lang": "en",
  "hpo_codes": ["HP:0001250", "HP:0000083", "..."],
  "disease_code": "OMIM:123456"
}
```

**Pasos:**
1. Cargar RAMEDIS de RareBench
2. Cargar `phenotype_mapping.json` y `disease_mapping.json`
3. Script de conversión: HPO codes → nombres, OMIM codes → disease names
4. Guardar en `data29/data-repos/normalized-by-source/ramedis_hpo/ramedis_hpo_v1.json`
5. Ejecutar `validation_checks.py` → debe dar PASS

**Criterio de aceptación:** QA report PASS + 624 casos con nombres legibles y diagnóstico gold.

---

### Paso 2.3 — Convertir y normalizar MyGene2 (~146 casos) ✅ COMPLETADO (2026-04-16)

**Descarga:** Obtenido directamente via Harvard Dataverse API (sin necesidad de descarga manual):
```
https://dataverse.harvard.edu/api/access/datafile/6689035
doi:10.7910/DVN/TZTPFL — "Deep Learning for diagnosing patients with rare genetic diseases"
```
Fichero: `mygene2_5.7.22.txt` (snapshot de MyGene2 a 7 mayo 2022 — mismo que usan Shepherd y DeepRare)

**Resultado de conversión:**
- 146 casos, 55 enfermedades MONDO, 48 genes causales únicos
- HPO/caso: min=1, avg=7.7, max=32 (más cortos que RAMEDIS avg=10.1)
- Solo 2 HPO desconocidos (HP:0040083 — término obsoleto)
- QA: ✅ PASS (0.7% label leakage — 1 caso, por debajo del umbral 5%)

**Fichero:** `data29/data-repos/normalized-by-source/mygene2_hpo/mygene2_hpo_v1.json`

**Nota:** El fichero original tiene también `true_genes`, `pubmed_id`, `orpha_category` — se preservan en el raw, no en el schema DxGPT final.

**Por qué MyGene2:** DeepRare reporta sus mejores resultados comparativos en este dataset.
Es el benchmark donde más claramente se verá si DxGPT es competitivo.

**Fuente:** Los 146 casos del proyecto Shepherd (Zitnik Lab, Harvard), extraídos de MyGene2 como
de mayo 2022. Incluyen HPO terms, gen causal confirmado, y diagnóstico OMIM.

**Dónde obtenerlos:**
```
https://zitniklab.hms.harvard.edu/projects/SHEPHERD
Harvard Dataverse (referenciado en el paper DeepRare)
```

El proceso de conversión es idéntico al de RAMEDIS: HPO codes → nombres legibles.

**Pasos:**
1. Localizar y descargar el fichero de 146 casos de MyGene2 (formato HPO)
2. Convertir HPO codes → nombres con el mismo script/mapeo que RAMEDIS
3. Guardar en `data29/data-repos/normalized-by-source/mygene2/mygene2_v1.json`
4. Ejecutar QA checker

**Criterio de aceptación:** QA report PASS + 146 casos correctamente estructurados.

---

### Paso 2.4 — Piloto de 50 casos antes de la ejecución completa ✅ COMPLETADO

**Dataset:** `bench/datasets/pilot_50_hpo.json` — 25 RAMEDIS + 15 MME + 10 HMS  
**Run:** `20260416220835` — gpt-4o, juez gemini-2.5-pro, TRANSLATE_CASE=false  
**Fix aplicado durante el run:** disease_mapping.json de RareBench tiene nombres en chino (357/624 RAMEDIS). Reconstruido con nombres ingleses usando `orpha2name.json` + DeepRare `disease_mapping.json`. El piloto tenía 15 casos chinos → LLM judge los resolvió correctamente.

**Resultados:**

| Métrica | Valor |
|---------|-------|
| Coverage | 49/50 = **98%** |
| Recall@1 | 20/50 = **40%** ✅ (criterio: >30%) |
| Recall@3 | 34/50 = **68%** |
| Recall@5 | 48/50 = **96%** |
| Average position | **2.551** |
| Resolución | 100% LLM_JUDGMENT (SapBERT offline) |

**Conclusión:** Pipeline valida correctamente datasets HPO. El `average_position 2.551` vs ~1.5 en all_256_clean refleja que HPO-como-lista es más difícil que texto narrativo — esperado y coherente. Criterio de aceptación superado. ✅ Listo para ejecución completa.

> **Nota de comparabilidad:** Los resultados de Fase 2 (HPO datasets) **NO son comparables** con el ranking principal (all_150 / all_256_clean / all_275). Son dos tipos de input distintos:
> - **Ranking principal**: texto narrativo clínico (edad, historia, evolución, exámenes) — como en uso real de DxGPT.
> - **Fase 2 HPO**: lista de términos HPO sin contexto clínico (ej. "Seizures, Microcephaly, Hypotonia") — formato estructurado del paper DeepRare.
>
> La métrica relevante para Fase 2 es **Recall@K** (comparación directa con el paper), no average_position.
> Los resultados de Fase 2 se mantienen en una sección separada del ranking con el marcador `(§)`.

**Fix dataset aplicado:** `pilot_50_hpo.json` regenerado con `seed=42` y nombres ingleses.

---

### Paso 2.5 — Ejecución completa RAMEDIS 624 casos ✅ COMPLETADO

**Run:** `20260417004913` — gpt-4o, juez gemini-2.5-pro, TRANSLATE_CASE=false  
**Dataset:** `bench/datasets/ramedis_hpo.json` — 624 casos, nombres en inglés (corregido desde orpha2name + DeepRare maps).

**Resultados:**

| Métrica | DxGPT gpt-4o | DeepRare paper (GPT-4 class) |
|---------|-------------|------------------------------|
| **Recall@1** | **49.2%** (307/624) | ~25-35% |
| **Recall@3** | **83.7%** (522/624) | — |
| **Recall@5** | **99.4%** (620/624) | ~60-75% |
| Coverage | 99.7% (622/624) | — |
| Avg position | 1.976 | — |

| Método resolución | Casos | % |
|---|---|---|
| BERT_AUTOCONFIRM | 276 | 44.2% |
| LLM_JUDGMENT | 294 | 47.1% |
| BERT_MATCH | 52 | 8.3% |

> SapBERT volvió a funcionar a mitad del run → 52.6% BERT, 47.1% LLM judge. Run válido.

**Conclusión:** DxGPT con gpt-4o supera claramente el baseline GPT-4 del paper DeepRare en Recall@1 (+14-24pp). El prompt `juanjo_classic_v2` optimizado para enfermedades raras es el factor diferencial.

| Run | Dataset | Modelo | Juez | Estado |
|-----|---------|--------|------|--------|
| R1-A | ramedis_hpo (624) | gpt-4o | gemini-2.5-pro | ✅ COMPLETADO |
| R1-B | ramedis_hpo (624) | gpt-5.4-mini | gemini-2.5-pro | ✅ COMPLETADO |

**R1-B (gpt-5.4-mini, run 20260417105437):**
- R@1=46.3% · R@3=80.6% · R@5=97.9% · Coverage=97.9% (611/624)
- gpt-4o levemente mejor en R@1 (+2.9pp), pero la diferencia es pequeña
- SapBERT activo: 69.1% BERT matches (mejor que gpt-4o con 52.6%)

---

### Paso 2.6 — Runs completos en los 5 datasets DeepRare (MME, HMS, LIRICAL, MyGene2) ✅ COMPLETADO

**Objetivo:** Completar la matriz de evaluación con los 4 datasets restantes, con gpt-4o y gpt-5.4-mini.

**Todos los runs completados (2026-04-17):**

| Dataset | Casos | Modelo | R@1 | R@3 | R@5 | Avg Pos | Run |
|---------|-------|--------|-----|-----|-----|---------|-----|
| lirical_hpo | 370 | gpt-4o | 37.0% | 73.0% | 97.8% | 2.529 | 20260417125334 |
| lirical_hpo | 370 | gpt-5.4-mini | **55.1%** | **79.7%** | **98.1%** | **1.975** | 20260417182706 |
| mme_hpo | 40 | gpt-4o | **42.5%** | 60.0% | **95.0%** | **2.632** | 20260417113846 |
| mme_hpo | 40 | gpt-5.4-mini | 22.5% | 62.5% | 90.0% | 2.757 | 20260417174500 |
| hms_hpo | 88 | gpt-4o | 34.1% | 70.5% | 94.3% | 2.761 | 20260417115441 |
| hms_hpo | 88 | gpt-5.4-mini | **53.4%** | **86.4%** | **100.0%** | **1.909** | 20260417175146 |
| mygene2_hpo | 146 | gpt-4o | 23.3% | 64.4% | 95.9% | 2.909 | 20260417101125 |
| mygene2_hpo | 146 | gpt-5.4-mini | **38.4%** | **77.4%** | **97.3%** | **2.282** | 20260417154253 |

**Patrón observado:**
- gpt-5.4-mini supera a gpt-4o en 4/5 datasets, con márgenes de +15-19pp en R@1
- Excepción: MME (40 casos del hospital chino PUMCH) — gpt-4o +20pp en R@1
  - Solo 40 casos: varianza estadística alta, resultado no generalizable
- La ventaja de gpt-5.4-mini es especialmente marcada cuando SapBERT está activo (más BERT matches → mejor rankeamiento)

---

## Fase 3 — Añadir Recall@K y comparativa pública ✅ COMPLETADA

**Prerequisito real usado para cerrarla:** Fase 2 completada con resultados estables.

**Objetivo:** Tener una comparativa directa contra el paper de Nature, reportable externamente.

> `SapBERT` sigue siendo deseable para una versión pre-publicación especialmente estricta, pero **ya no es bloqueante** para considerar esta fase cerrada. La comparativa pública y la tabla principal quedaron completadas sin ello.

### Nota abierta — Reactivar SapBERT (opcional pre-publicación estricta)

**Problema:** El endpoint SapBERT está pausado por falta de créditos en la cuenta HuggingFace `Devf29`. Todos los runs desde entonces tienen 0 BERT matches — todos los casos semánticos van al juez LLM.

**Impacto en comparabilidad:**
- Runs 1-12 del ranking: BERT activo (scores potencialmente ligeramente mejores en casos borderline)
- Runs 13+ del ranking: BERT offline (solo LLM judge)
- Esta diferencia no invalida los runs actuales, pero **sí introduce un confound** para una publicación externa especialmente estricta

**Acción si se quiere reforzar aún más la versión publicable:**
1. Ir a [ui.endpoints.huggingface.co](https://ui.endpoints.huggingface.co/) con la cuenta `Devf29`
2. Añadir créditos (endpoint: `doln60zovu62g568`, us-east-1 AWS, ~$0.06-0.15/hora)
3. Reanudar el endpoint
4. Re-ejecutar los modelos finalistas sobre `all_256_clean` con BERT activo
5. Esos resultados serán los publicables definitivos

### Paso 3.1 — Implementar Recall@K full-denominator en el evaluador ✅ COMPLETADO

**Qué es:** En lugar de "posición media de los casos que matchearon", contar sobre el total de casos:
- Recall@1 = % de casos donde el diagnóstico correcto está en posición 1
- Recall@3 = % de casos donde el diagnóstico correcto está en top 3
- Recall@5 = % de casos donde el diagnóstico correcto está en top 5

**Estado:** Recall@K ya se calcula correctamente en el pipeline (implícito via `top_counts` / `total_cases`). Los runs de Fase 2 reportan R@1, R@3, R@5 derivados de `P1/total`, `(P1+P2+P3)/total`, `(P1+…+P5)/total`.

---

### Paso 3.2 — Tabla comparativa contra DeepRare ✅ COMPLETADO

**Resumen corto (tabla completa en `output/rankingV2.txt` y `bench/pipelines/pipeline_v4 - fork/main/README.md`):**

| Dataset | Casos | Mejor modelo | Señal principal |
|---------|-------|--------------|-----------------|
| RAMEDIS | 624 | `gemini-3-pro-preview` | empate tecnico en R@1 con gemini-2.5, pero ventaja clara en R@3 |
| LIRICAL | 370 | `gemini-3-pro-preview` | +5.9pp R@1 vs gemini-2.5 |
| HMS | 88 | `gemini-3-pro-preview` | +15.9pp R@1 vs gemini-2.5 |
| MyGene2 | 146 | `gemini-3-pro-preview` | mejor dataset para discriminar modelos |
| MME | 40 | `gemini-3-pro-preview` | mejor R@1 y R@3 del benchmark |
| DDD | 1.749 | `gemini-3-pro-preview` | resultado mas solido: 70.3% R@1, 97.6% R@3 |

**Conclusiones finales (tabla cerrada — 6 datasets, 4 modelos):**
1. **gemini-3-pro-preview gana en los 6 datasets** en R@1 — sin excepciones (empate técnico en RAMEDIS R@1, +0.1pp)
2. **La ventaja de gemini-3-pro-preview sobre gemini-2.5-pro es consistente:** +0.1pp a +15.9pp en R@1, +5.6pp a +10.3pp en R@3
3. **DDD (1.749 casos) es el resultado más sólido estadísticamente** — 70.3% R@1 con gemini-3, +6.8pp sobre gemini-2.5-pro
4. La ventaja de gemini-3 en R@3 es especialmente llamativa: **97.6% DDD vs 91.8%** (+5.8pp) — el diagnóstico correcto aparece casi siempre en el top-3
5. **MyGene2** sigue siendo el más discriminante: gpt-4o 23.3% → mini 38.4% → gemini-2.5 55.5% → gemini-3 **61.0%**
6. En R@5 los modelos convergen (todos ~97-100%), el diferenciador real es R@1 y R@3
7. **DxGPT gemini-3-pro-preview supera el baseline GPT-4 del paper en todos los datasets** (+10-48pp en R@1)

> **Nota:** El modelo DeepRare (74% R@1 en MyGene2) es **especializado y fine-tuned** para enfermedades raras con HPO.
> DxGPT es un sistema generalista de producción. La comparación relevante es contra el baseline GPT-4 del paper (~20-35%),
> donde DxGPT gemini-2.5-pro mejora sustancialmente en todos los datasets.

---

### Paso 3.3 — Documentar el modo de entrada diferencial ✅ COMPLETADO

**Track A — Modo síntomas HPO:** Input = lista de síntomas HPO. Comparable con DeepRare.

**Track B — Modo texto clínico libre:** Input = descripción narrativa (como en producción). Comparable con uso real. Ningún sistema del paper evalúa en este modo — es el valor diferencial de DxGPT.

Reportar ambos tracks por separado en cualquier comunicación externa. ✅ Documentado en rankingV2.txt con secciones separadas y nota de no-comparabilidad.

---

### Paso 3.4 — Benchmark de modelos sobre all_256_clean ✅ COMPLETADO (2026-04-18)

**Objetivo:** Establecer qué modelo usar en producción para cada modo, con el dataset limpio y publicable.

**Resultados all_256_clean (256 casos, juez gemini-2.5-pro) — tabla completa:**

| Modelo | Avg Pos | Success% | Avg/caso | Lectura |
|--------|---------|----------|----------|---------|
| `gemini-2.5-pro low` | **1.299** | 98.1% | 27.9s | mejor calidad absoluta |
| `gemini-3-pro-preview low` | **1.299** | 98.1% | 10.3s | misma calidad, mucho mas rapido |
| `gpt-5.4-mini low` | 1.526 | 98.1% | **4.7s** | mejor opcion OpenAI en calidad/latencia |
| `gpt-5.4 full low` | 1.502 | 98.8% | 17.3s | opcion OpenAI avanzada |
| `gpt-4o` | 1.545 | 96.1% | 10.3s | ya superado |
| `gpt-5-mini` | 1.588 | 97.7% | 48.1s | demasiado lento |

> Tabla completa y resto de modelos: `output/rankingV2.txt` y `bench/pipelines/pipeline_v4 - fork/main/README.md`.

**Hallazgos clave:**
- **gemini-3-pro-preview** empata a gemini-2.5-pro en narrativa y lo supera de forma consistente en HPO
- **grok** como mejor opción fuera del ecosistema Google/OpenAI (1.448)
- **gemini-2.5-flash** equilibra velocidad y calidad (1.434, similar a grok pero Google)
- **gpt-5.4-mini low** sigue siendo el campeón en ecosistema OpenAI por velocidad (4.7s/caso)

**Decisiones de producción recomendadas:**

1. **Modo normal** → migrar de `gpt-5-mini low` (actual, ~48s/caso) a **`gpt-5.4-mini low`**
   - Mejor avg position (1.526 vs 1.588), ~10x más rápido, mismo coste aproximado
   - También mejor en HPO: +15-19pp en R@1 sobre gpt-4o (LIRICAL, HMS, MyGene2)

2. **Modo avanzado** → **`gemini-3-pro-preview`** (supera a gemini-2.5-pro en HPO + 3x más rápido)
   - Texto narrativo: empata gemini-2.5-pro (1.299 avg_pos)
   - HPO: +5 a +16pp R@1 sobre gemini-2.5-pro en los 3 datasets validados
   - `gpt-5.4 full low` como alternativa si se prefiere OpenAI (1.502, 17.3s/caso)
   - o3 queda en posición 7 y es más lento que los top 3 — retirar

3. **o3 queda obsoleto para producción**: superado en calidad por 6 modelos, sin ventaja de velocidad

**✅ COMPLETADO (2026-04-21) — Experimento `thinking_level=medium` en gemini-3-pro-preview:**

Pregunta: ¿más razonamiento del modelo bajo prueba mejora avg_pos / R@1 / R@3?
Diseño: mismos prompts, mismo juez (gemini-2.5-pro low), solo cambia `thinking_level` del emulator. n total = **900 casos**.

| Dataset | n | ΔR@1 | ΔR@3 | Δavg_pos | Run |
|---------|---|------|------|----------|-----|
| MME (HPO) | 40 | **−15.0pp** | 0 | +0.31 | 20260421202253 |
| HMS (HPO) | 88 | −2.2pp | **−6.8pp** | +0.17 | 20260421204421 |
| MyGene2 (HPO) | 146 | −6.9pp | **−17.1pp** | +0.43 | 20260421210815 |
| LIRICAL (HPO) | 370 | −4.1pp | **−7.0pp** | +0.15 | 20260421230733 |
| **HPO weighted (4 ds)** | **644** | **−5.1pp** | **−8.8pp** | **+0.22** | — |
| all_256_clean (narrativa) | 256 | +1.2pp | −2.7pp | +0.02 (≈ ruido) | 20260421215831 |
| **TOTAL** | **900** | **−3.3pp** | **−7.1pp** | **+0.17** | — |

**Conclusiones:**
1. **HPO**: medium degrada claramente — patrón consistente en **4/4 datasets independientes** (n=644). R@1 baja 5pp, R@3 baja 9pp ponderado.
2. **Narrativa**: trade-off neutro — R@1 +1pp, R@3 −3pp, avg_pos empata. NO net-positive.
3. **Hipótesis**: medium induce diferenciales más diversos. Beneficia marginalmente top-1 en narrativa (más exploración) pero penaliza el ranking en HPO terse (input ya estructurado).
4. **Coste**: medium ~30-40s/caso vs ~22s/caso low (+50% latencia, +50% coste tokens razonamiento).
5. **DECISIÓN**: NO usar medium en producción ni en benchmark. Mantener `gemini-3-pro-preview low`.
6. **CANCELADOS** por evidencia suficiente: `ramedis_medium`, `ddd_medium` (~6h ahorradas — patrón confirmado en 4 datasets HPO con n=644 ponderado).

Reproducibilidad: los configs sueltos en `main/` se eliminaron tras la limpieza del repo (2026-04-21). Cada run conserva su snapshot en `output/<dataset>/<prompt>/<model>_medium/<run_id>/juanjo_classic_v2___<model>_medium___config.yaml` — esa es la fuente de verdad para reejecutar cualquiera de los 5 medium ya completados (MME, HMS, MyGene2, LIRICAL, all_256_clean). Los configs cancelados (RAMEDIS, DDD medium) recuperables desde git history si se quisieran lanzar.

### Paso 3.5 — Evaluación de modelos adicionales (Claude, DeepSeek, etc.) 🔄 EN CURSO

**Objetivo:** Ampliar la comparativa con modelos de Anthropic, DeepSeek y futuros modelos.

> Esta línea de trabajo **no bloquea** el cierre de la Fase 3. La comparativa pública principal ya quedó cerrada con los modelos actuales.

**Estado Claude (Anthropic) — integración completada 2026-04-18:**

| Modelo | Estado | Snapshot config | Resultado |
|--------|--------|-----------------|-----------|
| claude-opus-4-7 | ✅ Completado | `output/all_256_clean/.../claude_opus_4_7_reeval/<run_id>/*___config.yaml` | avg_pos=1.668 / **80.1%** ⚠️ / **~$8 USD** (256c) |
| claude-sonnet-4-6 | ⏳ Pendiente | _config eliminado en limpieza 2026-04-21; recuperar de git o recrear_ | — |
| claude-haiku-4-5 | ⏳ Pendiente | _config eliminado en limpieza 2026-04-21; recuperar de git o recrear_ | — |

> **Nota técnica:** La API de Anthropic deprecó `temperature` en los modelos Claude 4.x. El provider `utils/llm/claude.py` detecta la versión del modelo y omite el parámetro automáticamente.

**⚠️ Hallazgo importante — Claude Opus 4.7 (80.1% coverage):**

Claude Opus 4.7 solo matcheó 205/256 casos — significativamente peor que otros modelos (97-99%). Hipótesis identificadas:

1. **Claude genera diagnósticos más elaborados/específicos** que se alejan del gold standard. Ej: en lugar de "Lupus eritematoso sistémico", puede generar "SLE con afectación renal clase III y síndrome antifosfolípido secundario" — correcto clínicamente pero el juez LLM no siempre lo confirma como equivalente.
2. **`juanjo_classic_v2` no está optimizado para Claude** — el prompt fue diseñado para OpenAI/Gemini. Claude interpreta las instrucciones de forma diferente (más detallado, más hedging, posiblemente omite enfermedades raras en favor de diferenciales más comunes).
3. **Claude es más conservador** en enfermedades raras — puede no incluir la enfermedad rara correcta en su top-8 DDX.

**Pendiente (Paso 3.6):** Evaluar Sonnet y Haiku para ver si el patrón se mantiene en toda la familia Claude. Si confirma, considerar crear `juanjo_claude_v1` — una versión del prompt optimizada para el estilo de respuesta de Claude.

### Paso 3.6 — Optimización de prompt (todos los modelos) ⏳ PENDIENTE

**Contexto:** El prompt `juanjo_classic_v2` es el prompt actual de producción, nunca reoptimizado desde que se introdujeron los modelos nuevos (gpt-5.4, gemini-2.5-pro, Claude, etc.). Cada familia de modelos tiene un estilo de respuesta diferente y puede beneficiarse de instrucciones adaptadas.

**Por qué es relevante ahora:**
- Claude Opus 4.7 evidenció que el prompt puede penalizar significativamente a algunos modelos (80% vs 98% coverage)
- Los modelos han evolucionado — las instrucciones óptimas para gpt-4o pueden no ser óptimas para gemini-2.5-pro o gpt-5.4
- Un prompt mejorado podría subir el ranking de todos los modelos, especialmente en enfermedades raras

**Enfoque recomendado:**
1. Analizar casos fallidos de los modelos top (Claude, gpt-4o) para identificar patrones de error
2. Diseñar variantes del prompt (`juanjo_v3`, `juanjo_claude_v1`, etc.) con ajustes específicos:
   - Instrucciones explícitas sobre formato de nombre de enfermedad (conciso, sin calificadores)
   - Énfasis en incluir enfermedades raras aunque sean poco probables
   - Instrucciones de ranking más claras
3. Evaluar las variantes sobre `all_256_clean` con los 3-4 modelos top
4. Seleccionar el mejor prompt universal o uno por familia de modelos

**Nota:** Esta tarea es de alto valor pero requiere iteración manual + criterio clínico. No es bloqueante para la publicación con los resultados actuales.

**Estado DeepSeek:**
- ⏳ Pendiente añadir `DEEPSEEK_API_KEY` al `.env` y crear config
- Candidatos: `deepseek-r1`, `deepseek-v3`

---

## Fase 4 — Escalar y validar (aspiracional) 🔄 PARCIAL

**Objetivo:** Extender la validación externa y preparar una versión más fuerte para publicación.

### Paso 4.1 — Dataset DDD (Gene2Phenotype, 1.749 casos) ✅ COMPLETADO

**Resumen:**

- Fuente: G2P EBI `DDG2P_2025-05-28.csv.gz`
- Conversión: HP codes a labels HPO legibles usando `hp.obo`
- Rol: dataset HPO más grande y resultado más sólido del benchmark

**Datasets generados:**

| Archivo | Casos | Descripción |
|---------|-------|-------------|
| `bench/datasets/ddd_hpo.json` | **1.749** | Todos los casos con fenotipos |
| `bench/datasets/ddd_hpo_confident.json` | 1.596 | Solo definitive + strong |
| `bench/datasets/ddd_hpo_pilot50.json` | 50 | Pilot (35 definitive + 15 strong, seed=42) |

**Resultado final por modelo:**

| Run | Dataset | Modelo | R@1 | R@3 | R@5 | Avg Pos | Estado |
|-----|---------|--------|-----|-----|-----|---------|--------|
| Modelo | R@1 | R@3 | R@5 | Avg Pos |
|--------|-----|-----|-----|---------|
| `gpt-4o` | 44.9% | 76.8% | 97.0% | 2.267 |
| `gpt-5.4-mini low` | 52.4% | 79.6% | 97.2% | 2.036 |
| `gemini-2.5-pro` | 63.5% | 91.8% | 98.0% | 1.614 |
| `gemini-3-pro-preview` | **70.3%** | **97.6%** | **98.1%** | **1.394** |

**Lectura:** DDD confirma el mismo orden que el resto del track HPO y refuerza a `gemini-3-pro-preview` como mejor modelo del benchmark para enfermedades raras estructuradas.

### Paso 4.2 — Dataset MIMIC-IV ⏸️ APLAZADO / BAJA PRIORIDAD

MIMIC-IV es el único dataset público del paper DeepRare no integrado. Razones para aplazar:

1. **Requiere registro burocrático**: cuenta en PhysioNet + Data Use Agreement (tarda 1-2 días en aprobarse, aunque es gratuito).
2. **No es específico de enfermedades raras**: son notas clínicas generales del Beth Israel Deaconess Medical Center (Boston). DeepRare usa un subconjunto filtrado — requeriría trabajo de preprocesamiento adicional para aislar los casos relevantes.
3. **Ya tenemos cobertura completa**: con los 6 datasets HPO (RAMEDIS, LIRICAL, HMS, MME, MyGene2, DDD) la comparativa con DeepRare está completa y es publicable.
4. **Texto narrativo ya cubierto**: `all_256_clean` (256 casos internos) cubre ya el track de texto narrativo.

**Conclusión**: MIMIC-IV sería un "bonus" para el track de texto narrativo externo, pero no es bloqueante para la publicación. Reevaluar su necesidad en función del tipo de publicación objetivo y los revisores.

Los otros 2 datasets del paper (Xinhua Hospital, 975 casos; Hunan Hospital, 162 casos) son **privados y no accesibles**.

### Paso 4.3 — Estratificación de resultados ⏳ PENDIENTE

Reportar resultados desglosados por:
- Tipo de enfermedad (rara genética vs. pediátrica general)
- Complejidad del caso (C2-C4 vs. C5+)
- Modalidad de input (HPO vs. texto libre)
- Idioma (español vs. inglés)

### Paso 4.4 — Validación clínica (opcional, muy alto valor)

El paper de Nature usó un panel de 8 médicos independientes con 88% de concordancia para validar sus resultados. Para una publicación de alto impacto, considerar un piloto similar (5-10 casos, 2-3 médicos).

### Paso 4.5 — Auditoría del juez LLM ⏳ PENDIENTE / PRIORIDAD ALTA

Los benchmarks narrativos históricos usan un prompt `legacy_similarity` que pide la opción clínicamente más similar o intercambiable. La evaluación multimodal demostró que esta política puede aceptar diagnósticos relacionados pero no equivalentes: sobre las mismas 100 respuestas, la cobertura pasó de 80% con `strict_equivalence` a 99% con legacy.

Por tanto, la cobertura histórica —por ejemplo, 98,1% para `gpt-5.4-mini low` en `all_256_clean`— no debe interpretarse todavía como 98,1% de equivalencia diagnóstica estricta.

Tareas:

- [ ] Calibrar `strict_equivalence` mediante la revisión médico-técnica definida en `bench/multimodal_beta/MEDICAL_REVIEW.md`.
- [x] Reevaluar `gpt-5.4-mini low` y `gpt-5.6-terra low` desde `evaluation_details` existentes (2026-08-31). Mismas respuestas; solo cambia el juez. Informe: `bench/multimodal_beta/results/2026-08-31-all256-judge-audit-strict-mini-terra.md`.
  - Mini: cobertura 98,1% → 79,7%; R@1 68,0% → 58,2%.
  - Terra: cobertura 98,1% → 83,2%; R@1 74,6% → 63,3%.
- [ ] Reevaluar el resto de la selección, sin repetir inferencia:
  - producción avanzada: `gemini-3-pro-preview low`;
  - contraste: `gpt-5.6-sol medium`;
  - baseline histórico principal.
- [ ] Comparar cobertura, R@K, posición media, casos ganados/perdidos y falsos positivos legacy.
- [ ] Etiquetar todas las cifras del informe como `legacy_similarity` o `strict_equivalence`.
- [ ] Reevaluar el histórico completo solo si la muestra cambia rankings o decisiones de producción.
- [ ] Actualizar `docs/benchmark-report.html` con la cautela metodológica y, cuando existan, ambas métricas.

Esta auditoría afecta al evaluador, no a las respuestas originales de los modelos. Los resultados históricos siguen siendo reproducibles, pero su interpretación clínica queda pendiente.

### Paso 4.6 — Candidatos futuros de expansión (opcional)

Si en el futuro se quiere ampliar el trabajo más allá del benchmark actual, los candidatos más razonables son:

- **MultiCaRe**: dataset multimodal de casos clínicos con texto + imagen. Interesa sobre todo como posible base para una evaluación multimodal futura de DxGPT, no como necesidad del benchmark actual.
- **Orphanet case reports / official rare-disease sources**: potencial fuente adicional de casos raros con mejor alineación ORPHA y utilidad para futuras extensiones del track de enfermedades raras.

No son tareas activas ahora mismo. Solo quedan anotadas como posibles líneas futuras.

---

## Resumen visual del estado

```
FASE 0  ████████████████████  100% ✅  (línea base, ablación modelos)
FASE 1  ████████████████████  100% ✅  (dataset limpio all_256_clean, arquitectura datos)
FASE 2  ████████████████████  100% ✅  (integrados los 6 datasets HPO del paper, incluido DDD)
FASE 3  ████████████████████  100% ✅  (Recall@K, tabla DeepRare, benchmark público y ablation medium cerrados)
FASE 4  ████████░░░░░░░░░░░░   40% 🔄  (4.1 DDD ✅; pendientes MIMIC-IV, estratificación y validación clínica)
```

---

## Criterios de éxito globales

| Criterio | Métrica | Target |
|----------|---------|--------|
| Dataset limpio | validation_checks.py | OVERALL: PASS |
| Comparabilidad con Nature | Recall@1 en MyGene2 | ≥ 50% (Nature tiene 74%) |
| Cobertura de datasets | Nº de datasets HPO accesibles del paper integrados | **6/6 completados** |
| Reproducibilidad | Mismos resultados en 2 runs del mismo modelo | ± 1% |
| Trazabilidad | Cada caso en un dataset tiene `source` y `case_id` | 100% |

---

## Documentos relacionados

| Fichero | Contenido |
|---------|-----------|
| `docs/pipeline/experiment-log.md` | Log detallado de experimentos y decisiones técnicas |
| `bench/pipelines/pipeline_v4 - fork/main/output/rankingV2.txt` | Historial de benchmarks |
| `.squad/decisions.md` | Decisiones arquitectónicas del equipo multidisciplinar |
| `bench/pipelines/pipeline_v4 - fork/main/GUIA_EVALUACION.md` | Guía paso a paso para ejecutar el pipeline |
