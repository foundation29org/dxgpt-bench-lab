# DxGPT Evaluation — Roadmap completo

**Objetivo final:** Poder publicar una comparativa de DxGPT contra los mejores sistemas del paper de Nature (DeepRare, 2025) sobre los mismos datasets, con métricas equivalentes y resultados auditables.

**Última actualización:** Abril 2026  
**Estado actual:** Fase 0 completada, Fase 1 en ejecución

---

## Visión general

```
FASE 0 [✅ HECHA]    Línea base con pipeline actual
FASE 1 [🔄 AHORA]    Limpiar dataset + arquitectura de datos
FASE 2 [⏳ PRÓXIMA]  Integrar datasets del paper de Nature
FASE 3 [⏳ FUTURA]   Añadir Recall@K + comparativa pública
FASE 4 [⏳ ASPIRAC.] Escalar a 3.500 casos + validación clínica
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
- [x] **0.6** Documentar hipótesis y conclusiones en `cleanInfo.md`

### Conclusiones clave de la Fase 0

- gpt-4o y gpt-5-mini tienen calidad equivalente en all_275 (+0.8% a favor de mini)
- El juez gemini-2.5-pro recupera ~3% más de casos que normalcalls
- La traducción mejora `average_position` pero reduce ligeramente el total de matches
- El dataset all_275 **falla los gates de calidad** — no apto para publicación externa

---

## Fase 1 — Limpiar el dataset 🔄 EN CURSO

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

### Paso 1.4 — Re-ejecutar modelos finalistas sobre `all_256_clean` 🔄 EN CURSO

Re-ejecutar los dos modelos finalistas sobre el dataset limpio para obtener la primera línea base honesta apta para publicación.

**Run 1.4-A: gpt-4o ✅ COMPLETADO (2026-04-16)**
- Modelo: `gpt-4o` · Juez: `gemini-2.5-pro` · Traducción: `true`
- Dataset: `bench/datasets/all_256_clean.json`
- Resultado: pos. media **1.545** · éxito **96.1% (246/256)**
- ⚠️ SapBERT activo solo desde caso 197/256 (reactivado durante el run)

**Comparativa Run B (all_275 sucio) → Run 1.4-A (all_256_clean limpio):**

| Métrica | Run B — all_275 sucio | Run 1.4-A — all_256_clean | Δ |
|---------|----------------------|--------------------------|---|
| Avg position | 1.646 | **1.545** | **−0.101 (mejor)** |
| Success % | 95.6% (263/275) | **96.1% (246/256)** | +0.5% |
| LLM_JUDGMENT | 97 | 87 | −10 |
| BERT matches | 0 | 5 | +5 |

**Conclusión inesperada — el boilerplate perjudicaba al modelo:**
La hipótesis de Ripley era que los scores bajarían ~5–8% al eliminar el leakage. Ocurrió lo contrario: los scores **mejoraron**. Explicación: los 49 casos RAMEDIS con boilerplate en español confundían al modelo — al limpiarlos a solo lista de síntomas HPO, el modelo genera mejores DDX. El leakage (19 casos triviales) no era el factor dominante; era el boilerplate el que degradaba la calidad.

**Run 1.4-B: gpt-5-mini ⏳ EN CURSO (2026-04-16)**
- Modelo: `gpt-5-mini` · `reasoning_effort: low`
- Juez: `gemini-2.5-pro` · Traducción: `true`
- Dataset: `bench/datasets/all_256_clean.json`
- SapBERT activo desde el inicio (primer run 100% limpio)
- Velocidad observada primeros casos: ~32-47s/caso → estimado ~3h total
- ⚠️ El cambio de política Azure (no auto-upgrade) NO redujo la latencia — los ~40s/caso son intrínsecos al modelo. El colega medía ~52s para el flujo completo de producción (3 llamadas: intención ~6s + DDX ~40s + anonimización ~6s). La llamada DDX siempre fue ~40s.

**Parámetros fijos (ambos runs):** `temperature=0.1, max_tokens=12000, BERT_accept=0.8, BERT_autoconfirm=0.9`

---

### Paso 1.5 — Crear la arquitectura de datos en tres niveles

**Por qué:** Antes de ingerir datos externos (Nature paper), necesitamos una estructura que garantice que nunca mezclamos datos sucios con limpios sin saberlo.

```
data29/data-repos/
├── raw/                              ← NIVEL 1: archivos originales, no se modifican
│   ├── SOURCE_MANIFEST.json          ← nuevo: documenta cada fuente (origen, licencia, fecha, hash)
│   ├── ramedis.json
│   ├── hms.csv
│   └── ...
│
├── normalized-by-source/             ← NIVEL 2: nuevo directorio
│   ├── ramedis/
│   │   ├── ramedis_v1.json           ← convertido al schema DxGPT + campo case_en pre-traducido
│   │   ├── qa_report_ramedis_v1.txt  ← resultado del validation_checks.py
│   │   └── provenance.json           ← raw → normalized, transformaciones aplicadas
│   └── mygene2/
│       ├── mygene2_v1.json
│       ├── qa_report_mygene2_v1.txt
│       └── provenance.json
│
└── curated-datasets/                 ← NIVEL 3: nuevo directorio (datasets de evaluación)
    └── all_256_clean/
        ├── all_256_clean.json
        ├── _metadata.json            ← composición: 256 casos, fuentes, fecha de creación
        └── _lineage.txt              ← qué casos vienen de qué fuente
```

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

**Criterio de aceptación:** Cualquier dataset en `curated-datasets/` tiene su `_metadata.json` y su fuente ha pasado el QA checker en el Nivel 2.

---

## Fase 2 — Integrar datasets del paper de Nature ⏳ PENDIENTE

**Prerequisito:** Fase 1 completa (dataset limpio + arquitectura tres niveles).

**Objetivo:** Evaluar DxGPT sobre los mismos datasets que usa DeepRare para poder hacer comparación directa.

### Paso 2.1 — Instalar y explorar RareCrowds

[RareCrowds](https://github.com/foundation29org/RareCrowds) es una librería Python de Foundation 29 que sirve los datasets públicos de enfermedades raras en formato HPO.

```powershell
pip install rarecrowds
```

Explorar qué datasets están disponibles y en qué formato:
```python
from rarecrowds import PhenotypicDatabase
db = PhenotypicDatabase()
# ver fuentes disponibles: RAMEDIS, HMS, LIRICAL, MME, Robinson, Lee, Cipriani...
```

---

### Paso 2.2 — Obtener y normalizar MyGene2 (~146 casos)

**Por qué primero MyGene2:** DeepRare tiene un 74% Recall@1 en este dataset — es el benchmark más revelador para la comparación. Es el dataset donde más claramente veremos si DxGPT es competitivo.

**Formato de entrada en Nature:** lista de HPO terms codificados → `["HP:0001250", "HP:0000083", ...]`

**Conversión a formato DxGPT:**
```json
{
  "case_id": "mygene2_001",
  "case_text": "Seizures, Intellectual disability, Hypotonia, Short stature",
  "diagnosis": "OMIM:123456",
  "source": "mygene2"
}
```
Cada HPO term se convierte a su nombre legible en inglés y se concatenan con comas. Sin narrativa clínica — solo la lista de síntomas.

**Pasos:**
1. Extraer casos de RareCrowds/MyGene2 en formato HPO nativo
2. Convertir HPO codes → nombres legibles (usar el ontology HPO)
3. Generar JSON en schema DxGPT
4. Guardar en `data29/data-repos/normalized-by-source/mygene2/mygene2_v1.json`
5. Ejecutar `validation_checks.py` sobre el resultado

**Criterio de aceptación:** QA report PASS + 146 casos correctamente estructurados

---

### Paso 2.3 — Obtener y normalizar RAMEDIS (~624 casos)

Mismo proceso que MyGene2 pero con RAMEDIS.

> ⚠️ Los casos RAMEDIS en `data29/data-repos/raw/ramedis.json` tienen el boilerplate español añadido artificialmente. Para este paso, usar el fuente original de RareCrowds (HPO nativo), **no** el fichero raw del repo.

**Pasos:**
1. Extraer casos de RareCrowds/RAMEDIS en formato HPO nativo
2. Convertir HPO codes → nombres legibles
3. Generar JSON en schema DxGPT
4. Guardar en `data29/data-repos/normalized-by-source/ramedis/ramedis_v1.json`
5. Ejecutar QA checker

---

### Paso 2.4 — Piloto de 50 casos antes de la ejecución completa

Antes de lanzar los 770 casos (146 + 624), ejecutar un piloto de 50 casos aleatorios (25 MyGene2 + 25 RAMEDIS) para validar que:
- El pipeline procesa correctamente el formato HPO-como-texto
- El medlabeler asigna códigos correctamente a nombres HPO
- El evaluador compara contra el diagnóstico gold correctamente

```powershell
python bench/validation_checks.py --dataset bench/datasets/pilot_50_hpo.json
python main.py  # con config apuntando al pilot dataset
```

**Criterio de aceptación:** Pipeline ejecuta sin errores, resultados son razonables (Recall@1 > 30%)

---

### Paso 2.5 — Ejecución completa Phase 1

Ejecutar los modelos finalistas sobre MyGene2 y RAMEDIS por separado:

| Run | Dataset | Modelo | Juez |
|-----|---------|--------|------|
| P1-A | mygene2_v1 (146) | gpt-4o | gemini-2.5-pro |
| P1-B | mygene2_v1 (146) | gpt-5-mini | gemini-2.5-pro |
| P1-C | ramedis_v1 (624) | gpt-4o | gemini-2.5-pro |
| P1-D | ramedis_v1 (624) | gpt-5-mini | gemini-2.5-pro |

Reportar por cada run: Recall@1, Recall@3, Recall@5, average_position, success%

---

## Fase 3 — Añadir Recall@K y comparativa pública ⏳ PENDIENTE

**Prerequisito:** Fase 2 completada con resultados estables + SapBERT activo (ver abajo).

**Objetivo:** Tener una comparativa directa contra el paper de Nature, reportable externamente.

### Prerequisito — Reactivar SapBERT ⚠️ PENDIENTE

**Problema:** El endpoint SapBERT está pausado por falta de créditos en la cuenta HuggingFace `Devf29`. Todos los runs desde entonces tienen 0 BERT matches — todos los casos semánticos van al juez LLM.

**Impacto en comparabilidad:**
- Runs 1-12 del ranking: BERT activo (scores potencialmente ligeramente mejores en casos borderline)
- Runs 13+ del ranking: BERT offline (solo LLM judge)
- Esta diferencia no invalida los runs actuales pero **sí es un confound** para publicación externa

**Acción cuando se acerque la publicación:**
1. Ir a [ui.endpoints.huggingface.co](https://ui.endpoints.huggingface.co/) con la cuenta `Devf29`
2. Añadir créditos (endpoint: `doln60zovu62g568`, us-east-1 AWS, ~$0.06-0.15/hora)
3. Reanudar el endpoint
4. Re-ejecutar los modelos finalistas sobre `all_256_clean` con BERT activo
5. Esos resultados serán los publicables definitivos

### Paso 3.1 — Implementar Recall@K full-denominator en el evaluador

**Qué es:** En lugar de "posición media de los casos que matchearon", contar sobre el total de casos:
- Recall@1 = % de casos donde el diagnóstico correcto está en posición 1
- Recall@3 = % de casos donde el diagnóstico correcto está en top 3
- Recall@5 = % de casos donde el diagnóstico correcto está en top 5

**Diferencia con la métrica actual:** La métrica actual (`average_position`) solo considera los casos donde hubo un match. Si 20 casos no matchearon, los ignora. Recall@K los cuenta como fallos.

**Implementación:** Modificar `evaluator.py` para calcular y exportar estas métricas adicionales en `summary.json`. No hay que eliminar las métricas actuales.

---

### Paso 3.2 — Tabla comparativa contra DeepRare

| Dataset | Métrica | DeepRare (Nature) | DxGPT gpt-4o | DxGPT gpt-5-mini |
|---------|---------|-------------------|--------------|------------------|
| MyGene2 | Recall@1 | **74%** | ? | ? |
| MyGene2 | Recall@5 | ~90% | ? | ? |
| RAMEDIS | Recall@1 | ~60% | ? | ? |
| RAMEDIS | Recall@5 | ~80% | ? | ? |

Los valores de DeepRare son del paper. Los valores DxGPT se rellenan con los runs de Fase 2.

**Criterio de éxito:** Si Recall@1 de DxGPT está dentro de ±10% del paper, el pipeline es comparable. Si está >15% por debajo, investigar antes de publicar.

---

### Paso 3.3 — Documentar el modo de entrada diferencial

**Track A — Modo síntomas HPO:** Input = lista de síntomas HPO. Comparable con DeepRare.

**Track B — Modo texto clínico libre:** Input = descripción narrativa (como en producción). Comparable con uso real. Ningún sistema del paper evalúa en este modo — es el valor diferencial de DxGPT.

Reportar ambos tracks por separado en cualquier comunicación externa.

---

## Fase 4 — Escalar y validar (aspiracional) ⏳ FUTURA

**Objetivo:** Extender a ~3.500 casos y añadir validación clínica humana.

### Paso 4.1 — Evaluar DDD dataset (~2.283 casos)

El dataset DDD (Deciphering Developmental Disorders) es el mayor público en el paper de Nature. Requiere evaluar acceso y licencia antes de proceder.

### Paso 4.2 — Estratificación de resultados

Reportar resultados desglosados por:
- Tipo de enfermedad (rara genética vs. pediátrica general)
- Complejidad del caso (C2-C4 vs. C5+)
- Modalidad de input (HPO vs. texto libre)
- Idioma (español vs. inglés)

### Paso 4.3 — Validación clínica (opcional, muy alto valor)

El paper de Nature usó un panel de 8 médicos independientes con 88% de concordancia para validar sus resultados. Para una publicación de alto impacto, considerar un piloto similar (5-10 casos, 2-3 médicos).

---

## Resumen visual del estado

```
FASE 0  ████████████████████  100% ✅
FASE 1  ████░░░░░░░░░░░░░░░░   20% 🔄  (documentado, falta ejecutar)
FASE 2  ░░░░░░░░░░░░░░░░░░░░    0% ⏳
FASE 3  ░░░░░░░░░░░░░░░░░░░░    0% ⏳
FASE 4  ░░░░░░░░░░░░░░░░░░░░    0% ⏳
```

---

## Criterios de éxito globales

| Criterio | Métrica | Target |
|----------|---------|--------|
| Dataset limpio | validation_checks.py | OVERALL: PASS |
| Comparabilidad con Nature | Recall@1 en MyGene2 | ≥ 50% (Nature tiene 74%) |
| Cobertura de datasets | Nº de datasets del paper integrados | ≥ 2 (MyGene2 + RAMEDIS) |
| Reproducibilidad | Mismos resultados en 2 runs del mismo modelo | ± 1% |
| Trazabilidad | Cada caso en un dataset tiene `source` y `case_id` | 100% |

---

## Documentos relacionados

| Fichero | Contenido |
|---------|-----------|
| `bench/pipelines/pipeline_v4 - fork/main/cleanInfo.md` | Log detallado de experimentos Fase 0 |
| `bench/pipelines/pipeline_v4 - fork/main/output/rankingV2.txt` | Historial de benchmarks |
| `.squad/decisions.md` | Decisiones arquitectónicas del equipo multidisciplinar |
| `bench/pipelines/pipeline_v4 - fork/main/GUIA_EVALUACION.md` | Guía paso a paso para ejecutar el pipeline |
