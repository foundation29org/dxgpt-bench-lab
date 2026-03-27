# Transparencia y alineación de métricas públicas (DxGPT)

**Estado:** borrador interno para revisión antes de actualizar contenido en [dxgpt.app/aboutus](https://dxgpt.app/aboutus).  
**Audiencia:** equipo producto / clínico / ingeniería.  
**Contexto:** más de 1M usuarios; modelo por defecto **GPT-5 mini**; modelo “avanzado” **o3** (deployment Azure).

---

## 1. Resumen ejecutivo

1. **Los números publicados en documentación antigua (p. ej. “1.326 – 92,7%” para o3 + classic_v2) no cuadran con el ranking reproducible del repo** tal como está archivado en `output/ranking.txt`.
2. **El 92,7% sí es rastreable**: corresponde a **255/275 casos con match** en el dataset **`all_275`**, prompt **`juanjo_classic`** (no `juanjo_classic_v2`), modelo **`o3_images`**. En esa misma corrida, la **posición media** en el ranking es **~1.443**, no 1.326.
3. **Mezclar “mejor posición media” de un experimento con “mejor % éxito” de otro** (o redondeos de gráficos sin tabla de referencia) genera **cifras optimistas o incoherentes** para la web pública.
4. **Los cambios del pipeline del 3 de enero de 2026** (commit `cf362dd`, mensaje *"new evals and cases"*) **sí apuntan a corregir y robustecer el flujo** (traducción para Text Analytics, extracción de códigos, juez configurable, prompt del juez dinámico en N DDX, etc.). No son “cosméticos”.
5. **“o3” como modelo avanzado** debe entenderse como **nombre de deployment en Azure** (`o3_images`, `o3-dxgpt`, …), no como una única entidad fija. **Otros modelos** (p. ej. GPT-5.x, Gemini 3 preview en benchmarks internos) pueden superar a un o3 concreto según **dataset, prompt, juez y versión del evaluador**. La decisión de producto debe basarse en **tabla actualizada misma métrica / mismo split**.
6. **Recomendación:** volver a ejecutar (o al menos publicar) resultados con **`all_275`** y, si se usa en informes, **`all_450`**, con **config congelada** (`config.yaml` copiado en `output/.../___config.yaml` + `summary.json`) y **una sola fila por experimento** en un ranking maestro.

---

## 2. Origen del “1.326 – 92,7%” en los informes LaTeX/Markdown

En `evaluacion_modelos_llm_diagnostico_pediatrico_pipeline_pv4.md` (y simplificado) aparece, en el anexo de mejores prompts para **o3**:

```text
classic_v2
Puntuación: 1.326 - 92.7%
```

### 2.1 Qué dice el `ranking.txt` del repo (julio 2025)

En `bench/pipelines/pipeline_v4 - fork/main/output/ranking.txt`:

| Puesto | Dataset   | Prompt           | Modelo     | Score (pos. media) | Éxito   |
|--------|-----------|------------------|------------|--------------------|---------|
| 🥇     | all_275   | juanjo_classic   | o3_images  | **1.305**          | **56,0%** (154/275) |
| 🥈     | all_275   | juanjo_classic   | o3_images  | **1.443**          | **92,7%** (255/275) |
| 4      | all_275   | juanjo_classic   | o3_images  | **1.492**          | **96,0%** (264/275) |

**Conclusión:** el **92,7%** del informe coincide con la fila **🥈** (255/275), pero la **posición media asociada en ese mismo experimento es ~1.443**, no 1.326.

**El valor 1.326 no aparece** en las filas de `ranking.txt` para esa combinación. Posibles explicaciones (no excluyentes):

- **Error de transcripción** al pasar del Excel/gráfico al PDF.
- **Agregación de otro corte** (otro prompt, otro subconjunto, o media ponderada de un gráfico tipo el adjunto en conversación).
- Confusión entre **`juanjo_classic`** vs **`juanjo_classic_v2`** (son prompts distintos; el ranking que lleva 92,7% es **`juanjo_classic`**, no `_v2`).

### 2.2 Verificación numérica directa sobre `evaluation_details.txt`

Se parseó `output/all_275/juanjo_classic/o3_images/20250719182451/evaluation_details.txt` con el script `compare_evaluation_details.py`:

- **275** casos, **255** con `final_resolution` con posición → **92,73%** de “éxito” según definición del pipeline.
- **Posición media** (solo casos con match): **~1.443**.

Esto **cierra** la correspondencia **92,7% ↔ 1.443** para ese artefacto concreto.

### ⚠️ Aclaración crítica: `juanjo_classic` ≠ `juanjo_classic_v2`

| Qué | Prompt | Dónde está la evidencia en repo |
|-----|--------|----------------------------------|
| **92,7% (255/275) y pos. media ~1.443** verificados con script | **`juanjo_classic`** (sin `_v2`) | `output/all_275/juanjo_classic/o3_images/20250719182451/evaluation_details.txt` |
| Run `all_150` julio 2025 con ~46/150 matches (o3_images) | **`juanjo_classic_v2`** | `output/all_150/juanjo_classic_v2/o3_images/20250719215218/evaluation_details.txt` |

**No mezclar** en informes públicos ni en gráficos: el anexo del PDF que cita **“classic_v2”** con **“92,7%”** **no cuadra** con el artefacto que **sí** sostiene el 92,7% en el repo (ese es **`juanjo_classic`** sobre **`all_275`**). Si el producto clínico usa **`juanjo_classic_v2`**, las cifras a publicar deben salir de corridas con **ese** prompt (y el dataset acordado), no del run `all_275` + `juanjo_classic` sin más contexto.

---

## 3. Por qué el benchmark “all_150 + o3_images” del 2025 parece tan malo al re-leer hoy

Se compararon dos ficheros bajo `all_150` + `juanjo_classic_v2`:

- `.../o3_images/20250719215218/evaluation_details.txt`
- `.../o3_dxgpt_high_translated_en/20260323163834/evaluation_details.txt`

Resultado del script de comparación (misma definición de “match”):

| Métrica | o3_images (2025-07) | o3-dxgpt (2026-03) |
|---------|------------------------|---------------------|
| Casos con match | **46 / 150** (~30,7%) | **150 / 150** (100%) |
| Pos. media (solo matched) | ~1.33 | ~1.63 |
| Métodos dominantes | BERT + LLM | SNOMED + ICD-10 + BERT + LLM |

**Interpretación:** no es (solo) que “o3 empeorara”. El run antiguo en `all_150` muestra un **régimen de evaluación casi solo semántico** (pocos matches por códigos). El run nuevo entra masivamente por **SNOMED/ICD-10**, coherente con **mejoras en `medlabeler`** (manejo de `data_sources`, envío estable a Text Analytics, etc.) y con **cambios en el evaluador**. Tras el commit de enero 2026 el `medlabeler` **llegó a incluir** traducción opcional de cada texto DDX vía Azure Translator antes de Text Analytics; **en el estado actual del repo (marzo 2026)** ese paso **se retiró** del labeler por robustez (SDK `azure-ai-translation-text` 1.x sin API antigua, menos puntos de fallo). Detalle en **§10**.

Por tanto: **comparar el PDF de 2025 con números de 2026 sin fijar versión de pipeline es engañoso**. Lo honesto es etiquetar cada cifra pública con **versión de commit** (o hash) y **ruta del `summary.json`**.

---

## 4. Cambios del 3 de enero de 2026 — ¿iban a “mejorar el pipeline”?

Commit: **`cf362dd`** (*new evals and cases*). Archivos relevantes en `bench/pipelines/pipeline_v4 - fork/main/` y `utils/llm/`:

| Área | Cambio principal | Efecto en la métrica |
|------|------------------|----------------------|
| **medlabeler.py** | (Ene. 2026) Traducción de textos DDX a inglés vía Azure Translator antes de Text Analytics + retries; comprobación de `data_sources`. *(Mar. 2026: en el código vigente del repo se eliminó la traducción de DDX en el labeler; los DDX van directo a Text Analytics con `language="en"`; ver §10.)* | Objetivo original: más códigos cuando el DDX no estaba en inglés. La capa extra de Translator también podía **añadir errores** (API, cuotas, cambios de SDK), no solo “arreglar” idioma. |
| **emulator.py** | Traducción opcional del caso; retries; unificación de llamadas por tipo de modelo | Menos fallos transitorios; caso y salida más alineados con el idioma esperado por el labeler. |
| **evaluator.py** | Juez configurable (`JUDGE_MODEL` / auto `normalcalls`); prompt del juez **1–N** DDX (antes asumía 5); parámetros por tipo de juez | Menos artefactos por prompt incorrecto; distinta tasa de aceptación semántica según juez. |
| **main.py** | Sufijo `_translated_<lang>` en rutas de salida | Trazabilidad de runs con traducción. |

**Conclusión:** sí, la intención y el efecto esperado son **mejorar corrección y reproducibilidad del pipeline**, no inflar artificialmente el % (aunque **cambiar reglas y cobertura de códigos sí cambia** el número reportado: eso es inevitable y debe explicarse en la web).

---

## 5. Modelo “avanzado”: ¿seguir con o3?

Criterios recomendados para la web y para producto:

1. **Definir una tabla única** con columnas mínimas: `dataset`, `prompt`, `deployment`, `juez`, `commit`, `N`, `% match`, `posición media`, `fecha`.
2. **No afirmar “o3 es el mejor”** sin esa tabla; en benchmarks internos recientes aparecen configuraciones **GPT-5.x / Gemini** con buen equilibrio posición/% según `rankingV2.txt` (siempre con el mismo dataset y juez).
3. Si **o3** se mantiene como “avanzado”, aclarar que es **opción de mayor coste/latencia razonamiento**, no garantía de mejor posición media en el benchmark interno actual.
4. Tras estabilizar métricas, **actualizar aboutus** con una frase tipo: *“Última actualización de cifras: [fecha]. Metodología: [enlace a este doc o a README del pipeline].”*

---

## 6. Próximos pasos concretos (para alinearte con o3_1 / o3_4 + GPT-4o del repo)

Los paths que citas:

- `output/all_275/o3_1/gpt_4o_summary/20250718113358/evaluation_details.txt`
- `output/all_275/o3_4/gpt_4o_summary/20250718115413/evaluation_details.txt`

Son runs **antiguos** (julio 2025): **prompts `o3_1` / `o3_4`**, **emulador aparentemente no es “o3 Azure”** en el sentido del deployment `o3_images`; el **evaluador/juez** es **`gpt_4o_summary`**. **No son comparables directamente** con “o3-dxgpt + juez Gemini” sin igualar juez y pasos.

**Plan sugerido:**

1. Fijar `DATASET_PATH` a `bench/datasets/all_275.json` (o `all_450` si existe en el entorno).
2. Correr **matriz pequeña**:
   - Mismo prompt (`juanjo_classic_v2` o el que uséis en producción).
   - Modelos: `gpt-5-mini` (default), `o3-dxgpt` (avanzado), opcionalmente `gpt-5.1` o el que queráis probar.
   - **Dos jueces** para sensibilidad: `normalcalls` vs `gemini-2.5-pro`.
3. Publicar solo **`summary.json` + `___config.yaml`** de cada run.

---

## 7. ¿Iba mal tu compañero?

**No es justo reducirlo a “errores” sin matices:**

- El informe y los gráficos reflejan **un momento del pipeline** y mezclas interpretables (p. ej. **emparejar 1.326 con 92,7%** cuando en el repo **92,7% va con ~1.443** en `all_275` + `juanjo_classic` + `o3_images`).
- La **evolución del evaluador y del labeler** cambia los números; eso **no invalida** el trabajo anterior, pero **sí obliga** a **versionar** lo que se muestra al público.

**Sí hay riesgo real de comunicación incorrecta** si la web muestra cifras del PDF **sin** dataset/prompt/juez/commit.

---

## 8. Referencias internas (repo)

| Recurso | Uso |
|---------|-----|
| `bench/pipelines/pipeline_v4 - fork/main/output/ranking.txt` | Ranking histórico julio 2025 (`all_275`, varios prompts). |
| `bench/pipelines/pipeline_v4 - fork/main/output/rankingV2.txt` | Ranking más reciente (incluye juez en leyenda). |
| `bench/pipelines/pipeline_v4 - fork/main/compare_evaluation_details.py` | Comparar dos `evaluation_details.txt`. |
| `evaluacion_modelos_llm_diagnostico_pediatrico_pipeline_pv4.md` | Informe del compañero (revisar anexo “1.326 – 92,7%”). |
| Commit `cf362dd` (2026-01-03) | Cambios de pipeline (diff en `evaluator.py`, `medlabeler.py`, `emulator.py`, `main.py`). |

---

## 9. ¿Vas por buen camino?

**Sí**, si:

- Tratas las cifras públicas como **resultados de un experimento versionado**, no como constantes físicas.
- Actualizas aboutus con **una tabla mínima** (dataset, N, %, posición media, modelo, juez, fecha, commit).
- Evitas afirmar **“el mejor modelo”** sin **misma metodología** que el benchmark interno actual.

**Siguiente paso más útil:** una corrida **all_275** (y opcionalmente **all_450**) con la **config de producción** y **juez explícito** documentado, y sustituir en la web cualquier par “posición / %” que no provenga de un `summary.json` identificable.

---

## 10. Traducción: descripción del paciente vs DDX — ¿qué pasaba antes y podía empeorar las cosas?

### 10.1 Dos cosas distintas

| Qué se traduce | Dónde | Para qué |
|----------------|--------|----------|
| **Descripción del caso** (narrativa clínica) | `emulator.py`, opción `TRANSLATE_CASE` | Que el **input** al LLM esté en inglés si el dataset viene en otro idioma. |
| **Textos DDX** (cada etiqueta de diagnóstico diferencial en la salida del modelo) | `medlabeler.py` (**solo en una fase del código tras ene. 2026**; **retirado en mar. 2026** en el repo) | Que Azure **Text Analytics** reciba texto en inglés para reconocimiento de entidades y códigos. |

Los **DDX no son la descripción del paciente**: son las **cadenas que el modelo escribe** en la lista de diagnósticos. Con caso en inglés y **prompt en inglés**, en la práctica **casi siempre** salen en inglés; no es una garantía formal del código (excepciones raras: latinismos, mezclas, alucinaciones).

### 10.2 ¿Antes también se traducían los DDX?

- **Antes del pipeline enriquecido (p. ej. julio 2025 en muchos runs):** el diseño habitual era **no** depender de una segunda traducción por DDX en el labeler; el flujo era esencialmente **Text Analytics sobre el texto del DDX tal cual** (con idioma declarado `en` cuando el experimento asumía inglés).
- **Tras el commit `cf362dd` (3 ene. 2026):** se añadió la intención explícita de **traducir cada texto DDX al inglés** antes de Text Analytics si hacía falta (Azure Translator + credenciales en `.env`). Eso ayuda si algún DDX llega en español u otro idioma.
- **Problema posterior:** la librería `azure-ai-translation-text` en versión 1.x **no expone** la API antigua (`TranslatorCredential`, `detect_language` como en tutoriales previos). Eso producía fallos en tiempo de ejecución aunque el paquete estuviera instalado. Además, **cada llamada al Translator** es un punto más de fallo (red, cuota, credenciales) **independiente** de Text Analytics.
- **Estado documentado aquí (marzo 2026, repo):** en `medlabeler.py` **se eliminó** el paso de traducción de DDX: los DDX del JSON del emulador se envían **directamente** a `begin_analyze_healthcare_entities` con `language="en"`. La traducción de la **descripción del caso** en el emulador (`TRANSLATE_CASE`) **sigue siendo independiente** y no se quitó.

### 10.3 ¿La traducción de DDX podía añadir más errores?

**Sí, en varios sentidos:**

1. **Operativos:** fallos de SDK, timeouts, 429, claves mal configuradas → el run se corta o se degrada a “sin traducción” con warnings.
2. **Semánticos (menos frecuentes):** un traductor automático puede **deformar** un término médico raro; Text Analytics trabajaría sobre un texto distinto al que emitió el modelo, o se rellenaba `normalized_text` con una variante no deseada frente al DDX original.
3. **Coste y tiempo:** ~una petición de traducción por término DDX único (o por batch según implementación) además del LRO de Text Analytics.

Por eso, **para experimentos donde el caso ya va en inglés y el prompt es inglés**, muchos equipos aceptan **no traducir DDX** y asumir inglés en la salida del modelo, priorizando **estabilidad del pipeline** frente a una capa redundante.

### 10.4 Resumen para comunicación interna

- **No confundir** “traducimos el caso” con “traducimos los DDX”: son capas distintas.
- **El 92,7% / comparativas históricas** no dependen de que el labeler actual traduzca DDX; dependen del **dataset, prompt, modelo, juez y versión del evaluador** concretos del artefacto citado.
- Si en el futuro se **reactiva** la traducción de DDX, conviene hacerlo con **flag en `config.yaml`**, SDK 1.x correcto (`AzureKeyCredential` + `translate(body=..., to_language=...)` y detección vía respuesta, no `detect_language`), y documentar commit y config copiada en `___config.yaml`.

---

## 11. Preguntas importantes para Yago

Objetivo: cerrar lagunas de documentación y alinear lo publicado con artefactos reproducibles.

1. **Origen exacto del “1.326”** en el informe LaTeX/PDF junto a **92,7%** para “classic_v2”: ¿de qué hoja, script o gráfico salió? En el repo, **92,7%** encaja con **`all_275` + `juanjo_classic` + `o3_images`** y pos. media **~1.443**, no 1.326.
igual patino, y se confuncio y fue ~1.443
2. **Confirmación de prompt en producción vs benchmark:** ¿el producto usa **`juanjo_classic`** o **`juanjo_classic_v2`** (u otro)? Las métricas del **92,7%** son del primero sobre **275** casos; el run **`all_150` + `_v2` + o3_images** es **otro experimento** (mucho menor % match en el `evaluation_details` que revisamos).
3. **Tres filas distintas en `ranking.txt` para `all_275-juanjo_classic-o3_images`** (1.305 / 56%, 1.443 / 92,7%, 1.492 / 96%): ¿qué cambiaba entre corridas (config, juez, versión evaluador, re-etiquetado, subconjunto)? ¿Cuál se consideraba “oficial” para comunicación externa?
4. **`summary.json` / `evaluation.log` / `emulator.log`:** ¿existían localmente y no se subieron al repo, o el pipeline de entonces no los generaba igual? ¿Hay backup en otro sitio (Drive, máquina, CI)?
5. **Gráfico de barras (o3 ~1.326):** ¿promedia varios prompts, varios runs o otro dataset? Necesitamos la **tabla fuente** fila a fila para poder actualizar aboutus sin ambigüedad.
los genero con claudeweb
6. **Criterio de “éxito” en el informe público:** ¿coincide 100% con `best_match_found` / `final_resolution` del pipeline V4 actual, o había otra definición (p. ej. solo primer GDX, solo P1)?
7. **`all_450`:** ¿hay `evaluation_details` o solo figuras agregadas? ¿Commit o carpeta de referencia?

---

*Documento generado para revisión interna DxGPT. Ajustar fechas y enlaces públicos antes de publicar.*
