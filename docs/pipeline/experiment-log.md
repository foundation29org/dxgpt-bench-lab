# Dataset Cleanup Analysis — all_275.json

**Última actualización:** Marzo 2026

---

## 1. Script de validación (Parker)

Los agentes generaron `bench/validation_checks.py`, un script de control de calidad que detecta problemas en el dataset **antes** de gastar tokens evaluando.

### Cómo ejecutarlo

```powershell
cd "c:\repos\DxGPT\eval"
$env:PYTHONIOENCODING = "utf-8"
python bench/validation_checks.py --dataset bench/datasets/all_275.json
```

Para exportar resultados a JSON:
```powershell
python bench/validation_checks.py --dataset bench/datasets/all_275.json --output bench/pipelines/pipeline_v4 - fork/main/output/validation_report.json
```

---

## 2. Resultado sobre `all_275.json` (ejecutado 2026-03-24)

```
✗ LABEL LEAKAGE     — FAIL   6.9%  (19/275)  umbral ≤5%
✗ BOILERPLATE PREFIX — FAIL  20.7% (57/275)  umbral <10%
✓ TEMPLATE MARKERS  — PASS  31.6% (87/275)  umbral <40%
✓ LIST-FORMAT       — PASS   0.0%  (0/275)   umbral ≤60%

OVERALL: FAIL
```

### Detalle de los fallos

#### Label Leakage (CRÍTICO) — 19 casos
El diagnóstico correcto aparece literalmente en el texto clínico del caso. El modelo no necesita razonar, solo hacer *pattern matching*.
Casos de muestra: `B133, J2, Q355, R10, R117`

#### Boilerplate Prefix (ALTO) — 57 casos
El caso empieza con el texto sintético `"Motivo de consulta: Paciente acude... Anamnesis:"`. Es un artefacto del pipeline de generación de datos, no texto clínico real. Puede inflar scores porque introduce contexto estructural artificial.
Casos de muestra: `R1, R10, R106, R108, R117`

---

## 3. Impacto en los resultados actuales

Los 19 casos de label leakage elevan artificialmente el score de **todos** los modelos por igual. Por tanto:

- La **comparación relativa entre modelos sigue siendo válida** (el ranking no cambia significativamente)
- Los **valores absolutos están sobreestimados** (el verdadero score sería algo menor)
- Los resultados actuales **no son aptos para publicación externa** hasta limpiar el dataset

---

## 4. Plan de limpieza (pendiente)

### Tier 1 — Bloquea evaluación honesta (hacer antes de publicar)
- [ ] Eliminar los 19 casos con diagnóstico en el texto (`Label Leakage`)
- [ ] Eliminar o reformatear los 57 casos con prefijo boilerplate

### Tier 2 — Mejora calidad (opcional)
- [ ] Separar los ~68 casos con mezcla de idiomas español/inglés
- [ ] Documentar los 87 casos con marcadores de plantilla

### Tier 3 — Aspiracional
- [ ] Convertir casos con listas de síntomas a prosa clínica

---

## 6. Ejemplo: por qué hay resultados distintos entre runs aparentemente iguales

Un caso concreto que ilustra el problema: dos runs sobre `all_150` con modelos o3 pero de épocas distintas dan resultados completamente diferentes porque el pipeline de evaluación cambió entre medias.

| Métrica | `o3_images` (2025-07) | `o3_dxgpt` (2026-03) |
|---|---|---|
| Casos | 150 | 150 |
| Con match (posición asignada) | 46 (~30.7%) | 150 (100%) |
| Posición media (solo entre los que matchearon) | 1.33 | 1.63 |
| Cómo resolvió | Solo BERT + LLM (18+16+12) | SNOMED/ICD-10 + BERT + LLM (66 SNOMED, 11+11+3 ICD-10, etc.) |

**Conclusión:** el run antiguo tenía pocos matches, casi todo resuelto semánticamente. El run nuevo resuelve casi todo con SNOMED/ICD-10 primero. La diferencia no es del modelo — es del pipeline de evaluación (medlabeler con más ontologías, umbrales BERT diferentes, juez distinto). Por eso **no se pueden comparar runs de épocas diferentes directamente**.

## 5. Plan de ejecución y decisiones

Antes de limpiar el dataset, se ejecutan runs de ablación sobre `all_275.json` tal como está para entender qué parte del pipeline (modelo, juez, traducción) explica las diferencias con los resultados históricos.

### Parámetros fijos en todos los runs (variables de control)

Para que los runs sean comparables, estos parámetros deben mantenerse iguales salvo que se esté probando específicamente su efecto:

| Parámetro | Valor usado | Impacto en benchmark |
|---|---|---|
| `temperature` | **0.1** | Casi determinista. A 0.0 sería 100% reproducible; a >0.3 introduce variabilidad entre runs del mismo modelo. Para comparación justa debe ser idéntico en todos los runs. |
| `BERT_ACCEPTANCE_THRESHOLD` | **0.8** | Umbral mínimo para que BERT considere un match válido |
| `BERT_AUTOCONFIRM_THRESHOLD` | **0.9** | Por encima de esto, BERT acepta sin consultar al juez |
| `max_tokens` | **12000** | Limita longitud de respuesta del modelo |
| `JUDGE_MODEL` | **gemini-2.5-pro** (en runs nuevos) | El juez es la variable con mayor impacto observado en éxito (+2.9%) |
| Dataset | **all_275.json** | Ver sección §2 para problemas de calidad del dataset |

> ⚠️ Los runs con `temperature` distinta, `JUDGE_MODEL` distinto o `BERT_*` distinto **no son directamente comparables**.

### Config de referencia — run anterior gpt-4o (2025-07-18)
- Dataset: `all_275.json`
- Modelo: `gpt-4o-summary` (versión no registrada, probablemente `2024-08-06` o `2024-05-13`)
- Juez: no explícito (auto → `normalcalls`)
- Traducción: no
- max_tokens: 4000, temperature: 0.1
- Resultado: pos. media **1.543** · éxito **93.8%** (258/275)

---

### Paso 1 — Run A: gpt-4o + juez normalcalls  ✅ COMPLETADO (2026-04-15)

Mismo juez que el run histórico pero con el pipeline nuevo (traducción activada, 12k tokens, medlabeler actualizado). Sirve para aislar el impacto del pipeline sobre el resultado del modelo.

- Dataset: `all_275.json`
- Modelo: `gpt-4o` versión `2024-11-20 (Default)`
- Juez: `normalcalls`
- Traducción: `TRANSLATE_CASE: true`
- max_tokens: 12000, temperature: 0.1

- Resultado: pos. media **1.639** · éxito **92.7%** (255/275) · rankingV2 rank 14

> Diferencia respecto al run de julio 2025 = impacto del pipeline nuevo (traducción + medlabeler + tokens)

**Conclusión del Run A:**

| Métrica | julio 2025 (pipeline viejo) | Run A (pipeline nuevo) | Δ |
|---|---|---|---|
| Pos. media | 1.543 | 1.639 | +0.096 (peor) |
| Éxito | 93.8% (258/275) | 92.7% (255/275) | -1.1% |
| SNOMED_MATCH | 79 casos | 126 casos | +47 |
| LLM_JUDGMENT | 86 casos | 84 casos | similar |

Paradoja: el pipeline nuevo resuelve muchos más casos por SNOMED (126 vs 79), lo que indica que el medlabeler actualizado asigna más y mejores códigos. Sin embargo, la posición media empeora. Hipótesis: **la traducción al inglés hace que el modelo genere diagnósticos más genéricos** (p.ej. "pneumonia" en vez de "community-acquired pneumonia"), empujando algunos P1 a P2-P3. El diagnóstico se encuentra pero no en primera posición.

---

### Paso 2 — Run B: gpt-4o + juez gemini-2.5-pro  ✅ COMPLETADO (2026-04-15)

Mismo config que Run A pero cambiando solo el juez. Sirve para cuantificar exactamente cuánto mueve el resultado cambiar el juez.

- Dataset: `all_275.json`
- Modelo: `gpt-4o` versión `2024-11-20 (Default)`
- Juez: `gemini-2.5-pro`
- Traducción: `TRANSLATE_CASE: true`
- max_tokens: 12000, temperature: 0.1
- Resultado: pos. media **1.646** · éxito **95.6%** (263/275) · rankingV2 rank 13
- ⚠️ SapBERT offline durante este run → 0 BERT matches (todos los casos semánticos fueron a LLM_JUDGMENT)

> Diferencia Run A → Run B = impacto del juez

**Conclusión del Run B:**

| Métrica | Run A — normalcalls | Run B — gemini-2.5-pro | Δ |
|---|---|---|---|
| Pos. media | 1.639 | 1.646 | +0.007 (inapreciable) |
| Éxito | 92.7% (255/275) | 95.6% (263/275) | **+2.9% (+8 casos)** |
| LLM_JUDGMENT | 84 | 97 | +13 |
| BERT | 7 | 0 | -7 (SapBERT offline) |
| No matched | 20 | 12 | **-8** |

Gemini como juez es más permisivo y más preciso: recuperó 8 casos que normalcalls rechazó, reconociendo mejor la equivalencia semántica entre nombres de diagnósticos. La posición media es prácticamente idéntica — el juez no mueve dónde pone el modelo los diagnósticos, solo si acepta o rechaza el match.

---

### Paso 3 — gpt-5-mini + traducción sobre all_275  ✅ COMPLETADO (2026-04-15)

El colega comparó gpt-5-mini vs gpt-4o sobre `all_150`. Para confirmar si la mejora de calidad se mantiene en el conjunto completo se necesita ejecutar sobre `all_275` con el mismo juez (`gemini-2.5-pro`).

- Dataset: `all_275.json`
- Modelo: `gpt-5-mini` · `reasoning_effort: low`
- Juez: `gemini-2.5-pro`
- Traducción: `TRANSLATE_CASE: true`
- Resultado: pos. media **1.653** · éxito **96.4%** (265/275) · rankingV2 rank 14
- ⚠️ SapBERT offline → 0 BERT matches (igual que Run B gpt-4o, comparación limpia)
- ⚠️ Run muy lento (horas) — causa: auto-upgrade del deployment Azure (ver sección Notas de latencia)

**Conclusión del Paso 3 — comparativa gpt-4o vs gpt-5-mini (mismas condiciones):**

| Métrica | gpt-4o Run B | gpt-5-mini Paso 3 | Δ |
|---|---|---|---|
| Pos. media | 1.646 | 1.653 | +0.007 (inapreciable) |
| Éxito | 95.6% (263/275) | 96.4% (265/275) | **+0.8%** |
| SNOMED | 127 | 131 | +4 (mini más específico) |
| LLM_JUDGMENT | 97 | 91 | -6 (mini menos semántico) |
| No matched | 12 | 10 | -2 |

**Veredicto:** calidad prácticamente equivalente. La mejora del colega (+0.5%) se confirma en el orden correcto (+0.8%) pero es marginal. gpt-5-mini genera diagnósticos más específicos (más SNOMED directos), gpt-4o genera diagnósticos más genéricos que el juez acepta semánticamente. **Con la lentitud actual de gpt-5-mini por el auto-upgrade de Azure, gpt-4o es la opción de producción más razonable hasta que se resuelva el problema del deployment.**

---

### Paso 3b — gpt-5-mini SIN traducción sobre all_275  ⏳ PENDIENTE

Para probar la hipótesis de que la traducción generaliza diagnósticos y empeora la posición media. Misma config que Paso 3 pero con `TRANSLATE_CASE: false`.

- Dataset: `all_275.json`
- Modelo: `gpt-5-mini` · `reasoning_effort: low`
- Juez: `gemini-2.5-pro`
- Traducción: `TRANSLATE_CASE: false`

> Diferencia Paso 3 → Paso 3b = impacto puro de la traducción, sin confounders del pipeline viejo

---

### Paso 3c — gpt-4o SIN traducción sobre all_275  ✅ COMPLETADO (2026-04-15)

Para cerrar el círculo y confirmar que la traducción también afecta a gpt-4o de forma aislada.

- Dataset: `all_275.json`
- Modelo: `gpt-4o`
- Juez: `gemini-2.5-pro`
- Traducción: `TRANSLATE_CASE: false`
- Resultado: pos. media **1.753** · éxito **98.6%** (271/275) · rankingV2 rank 18

> Diferencia Run B (gpt-4o con traducción) → Paso 3c (sin traducción) = confirma o refuta hipótesis en gpt-4o

**Conclusión — hipótesis de traducción REFUTADA (o más bien, matizada):**

| Métrica | Run B — con traducción | Paso 3c — sin traducción | Δ |
|---|---|---|---|
| Pos. media | **1.646** | 1.753 | **+0.107 (peor sin traducción)** |
| Éxito | 95.6% (263/275) | **98.6% (271/275)** | +3.0% (mejor sin traducción) |
| P1 hits | **191** | 184 | -7 |
| P8/P10 hits | 0 | **4** | +4 (aparecen posiciones muy tardías) |
| LLM_JUDGMENT | 97 | **103** | +6 |
| No matched | 12 | **4** | -8 |

La hipótesis original era: "la traducción generaliza diagnósticos → peor posición media". Los datos la **refutan**: sin traducción la posición media es PEOR (1.753 vs 1.646). Lo que realmente ocurre:
- **Sin traducción:** gpt-4o genera diagnósticos en español o mezclados. Gemini acepta más (271 vs 263) pero en posiciones tardías — aparecen P8 y P10 que destrozan la media.
- **Con traducción:** el modelo es más preciso, pone el diagnóstico correcto en P1 más veces (191 vs 184), aunque pierde algunos matches difíciles.

**La causa real de la degradación respecto al pipeline viejo (1.543→1.646) es el cambio en el evaluador** (medlabeler actualizado, diferentes pesos de ontologías), no la traducción. La traducción en realidad *mejora* la posición media.

---

### Paso 4 — Limpiar all_275 y re-ejecutar  ⏳ PENDIENTE (después de §7)

---

## 7. Estrategia de evaluación con datasets del paper Nature (DeepRare)

**Referencia:** "An agentic system for rare disease diagnosis with traceable reasoning", Nature, 2025.
DOI: https://www.nature.com/articles/s41586-025-10097-9

El paper usa un enfoque mixto: resultados detallados por dataset individualmente (para mostrar robustez en 14 especialidades y ~3.000 enfermedades) y resultados agregados para comparación estadística global con otras herramientas. **El objetivo es poder referenciar ese paper y comparar DxGPT frente a los mismos benchmarks.**

---

### 7.1 Contexto: formato de entrada en DeepRare vs DxGPT

| Aspecto | DeepRare (Nature) | DxGPT actual |
|---|---|---|
| Formato de entrada | Lista de HPO terms codificados (`HP:0001250`, `HP:0000083`...) | Descripción clínica libre en texto |
| Datasets | RAMEDIS (624), HMS (87), LIRICAL (369), MME (40), + 5 más | all_275, all_150 (enfermedades raras + comunes) |
| Métrica | Recall@K (K=1,3,5,10) | average_position + success% |
| Idioma input | Inglés (HPO es universal) | Español / inglés / mezcla |

**Problema:** si convertimos HPO terms a texto clínico generado por LLM para alimentar DxGPT, introducimos ruido del generador. Si usamos los HPO terms directamente, estamos evaluando un modo de uso diferente.

**Solución:** dos tracks de evaluación que miden cosas distintas y se reportan por separado.

---

### 7.2 Track A — Modo síntomas HPO (comparable con DeepRare)

**Objetivo:** comparación directa con DeepRare, GPT-4o, o3-mini, Claude del paper.

- **Input a DxGPT:** lista de síntomas HPO convertidos a nombres legibles en inglés (`"Seizures, Intellectual disability, Hypotonia"`) — sin narrativa clínica, solo síntomas separados por comas
- **Por qué es válido:** los usuarios de DxGPT ya introducen síntomas solos (sin historia clínica). Este modo existe en producción.
- **Métrica:** Recall@1, Recall@3, Recall@5, Recall@10 — misma métrica que el paper para comparación directa
- **Datasets:**

| Dataset | Casos | Fuente | Disponible en repo |
|---|---|---|---|
| RareBench-RAMEDIS | 624 | RAMEDIS DB (Alemania) | `data29/data-repos/raw/ramedis.json` ⚠️ con boilerplate |
| RareBench-HMS | 87 | HMS genetics clinic | `bench/datasets/` |
| RareBench-LIRICAL | 369 | Simulados con LIRICAL | `bench/datasets/` |
| RareBench-MME | 40 | MME benchmark | `bench/datasets/` |

> ⚠️ Los casos RAMEDIS en el repo tienen el boilerplate español artificialmente añadido (ver §2). Para Track A hay que extraer solo los HPO terms originales, **no** usar el wrapper en castellano.

- **Fuente de datos limpia:** librería Python [RareCrowds](https://github.com/foundation29org/RareCrowds) (Foundation 29 — misma organización) sirve estos datasets en formato HPO nativo. Permite obtener los datos sin el wrapper artificial.

- **Estado:** ⏳ PENDIENTE — falta definir formato exacto de input y adaptar pipeline

---

### 7.3 Track B — Modo texto clínico libre (valor diferencial de DxGPT)

**Objetivo:** demostrar lo que DxGPT hace que DeepRare no hace — procesar texto clínico narrativo real como el que introducen los médicos.

- **Input a DxGPT:** descripción clínica libre (como en producción)
- **Métrica:** average_position + success% (pipeline actual)
- **Dataset:** `all_275_clean.json` (Paso 4 pendiente — limpiar label leakage + boilerplate)
- **Ventaja comunicativa:** ninguno de los sistemas del paper evalúa en este modo. Es el caso de uso real de DxGPT.

- **Estado:** ⏳ PENDIENTE — bloqueado por Paso 4 (limpieza dataset)

---

### 7.4 Roadmap de implementación

```
[AHORA]   Paso 4    → Limpiar all_275 (label leakage + boilerplate)
[PRÓXIMO] Track A   → Instalar rarecrowds, extraer HPO nativo de RAMEDIS/HMS/LIRICAL/MME
                    → Adaptar prompt para modo síntomas (sin narrativa)
                    → Ejecutar gpt-4o y gpt-5-mini sobre los 4 datasets
                    → Calcular Recall@1/3/5/10 por dataset + agregado
[DESPUÉS] Track B   → Ejecutar modelos finalistas sobre all_275_clean
                    → Reportar average_position + success%
[FINAL]   Publicar  → Tabla comparativa DeepRare vs DxGPT con ambos tracks
                    → Referenciar paper Nature como benchmark externo
```

---

### 7.5 Nota sobre RareCrowds

[RareCrowds](https://github.com/foundation29org/RareCrowds) es una librería Python open-source de **Foundation 29** (misma organización) que sirve los datasets públicos de pacientes con enfermedades raras en formato HPO. Incluye exactamente los datasets que usa el paper de Nature (RAMEDIS, HMS, etc.) más otros adicionales:

- Robinson (384 casos), Lee (200 casos), Cipriani (134 casos), ClinVar (~68k submuestra), Tomar (50 casos), Ebiki (20 casos)...
- Total: varios cientos de casos reales con diagnóstico verificado y síntomas HPO

Es la fuente más limpia para Track A porque proporciona los HPO terms directamente, sin el boilerplate artificial que tienen los CSV del repo. Instalar con `pip install rarecrowds`.

---

### Paso 4 — Limpiar all_275 y re-ejecutar  ⏳ PENDIENTE

Una vez tengamos la línea base completa (Pasos 1–3b), limpiar el dataset (Tier 1: label leakage 19 casos + boilerplate 57 casos) y re-ejecutar los modelos finalistas para obtener resultados publicables.

Ver sección `## 2` para los resultados del script de validación.

---

### Notas de latencia (observadas)

La latencia es un criterio de decisión para producción igual de importante que la calidad. Hay que medirla en cada run.

| Modelo | Fecha medición | Tiempo/caso | Fuente |
|---|---|---|---|
| `gpt-5-mini` | 2025-08 (colega) | ~52 s (42 s modelo + 10 s anon.) | estimación manual — versión desconocida |
| `o3-dxgpt` | 2025-08 (colega) | ~48 s (38 s modelo + 10 s anon.) | estimación manual |
| `gpt-5-mini` | 2026-04-15 | **mucho más lento** ⚠️ | run actual en curso — medir al terminar |

> ⚠️ **Causa identificada de la lentitud:** el deployment `gpt-5-mini` en Azure tiene política **"Upgrade once new default version becomes available"**. Microsoft actualizó automáticamente la versión del modelo (actualmente `2025-08-07`) desde la creación del deployment (2025-08-27). La versión nueva es más lenta. **Acción pendiente: cambiar la política a "No automatic upgrades" en el portal Azure** para congelar la versión y garantizar reproducibilidad de benchmarks futuros.
>
> Adicionalmente, el pipeline usa múltiples regiones (India, Japón, Suecia, US West, US East) según el usuario, lo que introduce varianza de latencia entre llamadas.

> **Nota:** Usar siempre versión `Default` del modelo y anotarla en el config para que quede registrada en el `summary.json`.
