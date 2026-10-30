# Pipeline V5

Pipeline V5 cambia solo el **evaluador**. El emulador, el labeler y el formato
de salida son los de Pipeline V4, que se queda intacto en
`bench/pipelines/pipeline_v4 - fork/main`.

Explicación completa del pipeline: [docs/pipeline/pipeline-v5.md](../../../../docs/pipeline/pipeline-v5.md).
Informe con gráficas: [docs/benchmark-report-v5.html](../../../../docs/benchmark-report-v5.html),
que se regenera con `py build_report.py` después de cada run o re-puntuación.

Origen de los cambios: la revisión de la rúbrica del juez
(`bench/multimodal_beta/JULIAN_HARNESS_REVIEW.md`, §9–§11) y el plan del
evaluador en `docs/ROADMAP.md`.

## Qué cambia respecto a V4

| | V4 strict | V5 |
|---|---|---|
| SNOMED exacto | acierto sin juez | acierto sin juez (igual) |
| ICD-10 exacto | acierto sin juez | **no decide** desde `graded_v2` (regla C1): decide el juez |
| ICD-10 hijo, padre, hermano | acierto sin juez | **no deciden**: se guardan como dato y decide el juez |
| SapBERT ≥ 0,90 | acierto sin juez | **no se usa** |
| SapBERT ≥ 0,80 | adelanta la posición del juez | **no se usa** |
| Cuándo se llama al juez | solo si ninguna capa acierta | **en todos los casos** |
| Texto del gold que lee el juez | `normalized_text` del labeler | **el gold tal como está en el dataset** |
| Respuesta del juez | una posición (`0` = ninguna) | **una nota por opción**: 2 / 1 / 0, en JSON |
| Posición del acierto | la de la primera capa que acierta | **la mejor** entre códigos exactos y juez |
| Métricas | una lectura | **estricta** (solo 2) y **laxa** (2 o 1) |

Notas del juez (`graded_v1`):

- **2**: misma entidad. Sinónimos, abreviaturas y variantes. Una forma más
  específica solo si todo paciente con la opción tiene el diagnóstico de
  referencia (subtipo de la referencia, o la referencia con lateralidad o
  extensión añadidas).
- **1**: relacionado, no igual. Categoría más amplia, omite un calificador que
  define la referencia («GIST» frente a «GIST maligno»), otro subtipo, gen o
  fenotipo de la misma familia, causa, complicación, precursor o consecuencia,
  o una disyuntiva «A o B».
- **0**: otra enfermedad.

Desde `graded_v2` (reglas de la rúbrica contestadas por Julián):

- **C1:** solo SNOMED exacto decide sin juez.
- **C2:** «X con Y» (Y es una complicación o manifestación) y «hallazgo debido
  a X» se aciertan con «X».
- **C3:** con varios gold, basta con acertar uno.
- **C4:** las referencias amplias se aciertan con una forma más específica.
- Si el gold trae `accepted_names`, el juez los recibe como «also known as».

El juez también indica si la referencia es una enfermedad
(`reference_is_disease`). No cambia la nota: sirve para limpiar el dataset.

La cifra oficial es la **estricta**. La laxa es de uso interno mientras la
frontera entre 1 y 0 no esté validada clínicamente.

## Cómo ejecutar

Igual que V4, desde esta carpeta:

```powershell
cd "C:\repos\DxGPT\eval\bench\pipelines\pipeline_v5\main"
py main.py --config config_terra_low_all256.yaml
```

`REUSE_LABELED_DDX` copia la salida del labeler de un run anterior y evalúa
esas mismas listas, sin llamar al emulador ni al labeler. Así la diferencia
con V4 se debe solo al evaluador. Sin esa clave, V5 hace un run completo como
V4.

`REFRESH_GOLD_FROM_DATASET: true`, junto a `REUSE_LABELED_DDX`, cambia el
gold de esas listas por el que tiene ahora `DATASET_PATH` y quita los casos
que ya no están en el dataset. Sirve para re-puntuar cuando se corrige el gold
(`narrative_v2` v0.2, HPO v2) sin generar listas nuevas.

`EVALUATOR.CASE_LIMIT: N` evalúa solo los primeros N casos (prueba rápida).

Si el juez falla tres veces en un caso (Gemini devuelve a veces 503 «high
demand»), el caso sale en `cases_with_judge_errors` del `summary.json`.
`py repair_judge_errors.py <carpeta del run>` vuelve a juzgar solo esos casos
y reescribe `evaluation_details.txt`, `summary.json` y `judge_metrics.json`.

## Salidas

En `output/<dataset>/<prompt>/<modelo>/<timestamp>/`:

- `evaluation_details.txt`: un bloque JSON por caso, separados por `---`.
  `final_resolution` (estricta) y `lax_resolution` (laxa) siguen el formato de
  V4. `graded_trace` guarda, por cada opción, el código exacto si lo hay, la
  relación ICD-10, la nota del juez y la nota final.
- `summary.json`: R@1, R@3, R@5, cobertura, posición media y MRR en las dos
  lecturas. También incluye las listas de auditoría:
  - `code_judge_disagreements`: código exacto, pero el juez no da un 2;
  - `icd10_relation_judge_grades`: qué nota pone el juez a hijos, padres y
    hermanos ICD;
  - `reference_not_disease`: gold que el juez no considera una enfermedad.
- `judge_metrics.json`: cada llamada al juez, con tokens, latencia y coste
  estimado.

Comparación con V4 sobre las mismas listas:

```powershell
py compare_runs.py --baseline "<v4>\evaluation_details.txt" --candidate "<v5>\evaluation_details.txt"
```

Escribe `comparison.md` junto al run de V5, con los casos que cambian
agrupados por la capa de V4 que los decidía.

Cifras por bloque de `narrative_v2` (y `live` sin los casos que el modelo pudo
ver, según su fecha de corte):

```powershell
py score_blocks.py --dataset bench/datasets/narrative_v2.json --runs <run> <run> ... `
  --live-dates ..\..\..\..\data29\data-repos\narrative-v2\work\live_dates.json
```

Con `--without-clinical` ignora los gold con `role: clinical` (en HPO v2, el
nombre de la enfermedad sin gen), lo que da la nota solo con el gold con gen
sobre las mismas llamadas al juez.

## Primer run: Terra low en all_256_clean (27-oct-2026)

Mismas listas DDX que el run `20260710140614`. Juez Gemini 2.5 Pro, prompt
`graded_v1`, anterior a las reglas C1 y C2.

| Evaluación | R@1 | R@3 | R@5 |
|---|---:|---:|---:|
| V4 strict (canónico) | 63,3 % | 80,1 % | 83,2 % |
| V5, gold normalizado por Azure (`20261027194849`) | 69,9 % | 80,1 % | 82,0 % |
| V5, gold del dataset sin normalizar (`20261027200004`) | **69,1 %** | 79,3 % | **81,2 %** |
| V5 laxa, gold del dataset sin normalizar | 88,7 % | 94,5 % | 96,9 % |

357 llamadas al juez, 0 respuestas inválidas, ≈ 4,2 $, p50 10 s, ≈ 10 min.
Detalle caso a caso en `comparison.md` de cada run.

- **R@1 sube unos 6 puntos.** V4 fijaba la posición con la primera capa que
  acertaba. En Boerhaave, Terra lo tenía en P1 y V4 lo contaba en P3 por un
  hermano ICD (Mallory-Weiss).
- **R@5 baja 2 puntos.** Salen unos 12 aciertos de hermanos/padres ICD y BERT
  que eran otra enfermedad: Mallory-Weiss por Boerhaave, MADD por déficit de
  CPT I, rubéola congénita por CMV fetal. Entran otros por la regla «más
  específico», varios con gold amplios.
- **Hermanos y padres ICD:** de 75 opciones con esa relación, el juez solo da
  un 2 a 12.
- **BERT no aporta aciertos que no dé el juez.** De los 16 casos que V4
  resolvía con BERT, el juez da un 2 a 14 y un 1 a 2. Sus fallos están en
  raras, con nombres casi iguales (L-2 frente a D-2 hidroxiglutárica).
- **La nota laxa (≈ 97 %) reproduce el 98 % del juez antiguo.**

## Modelos de referencia sobre narrative_v2 (28-oct-2026)

`narrative_v2` v0.1 (sin validación clínica), V5 `graded_v2`, juez Gemini 2.5
Pro. Mismo prompt (`juanjo_classic_v2`) y esfuerzo `low` en todos. Runs
completos (`config_<modelo>_low_narrative_v2.yaml`). Gemini 3 Pro ya no está
en la API de Google (404): se usa gemini-3.1-pro-preview, su sucesor.

R@1 estricta:

| Modelo | Total | `live` | `urg` | `exam` | `synth` | `live`+`urg` | Raras | `live` sin ver |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| gpt-6.1-sol | **67,0 %** | **60,0 %** | 53,3 % | 86,7 % | 90,0 % | **58,1 %** | **70,2 %** | 61,0 % (146) |
| claude-opus-5 | 64,7 % | 53,3 % | **56,7 %** | **88,3 %** | 90,0 % | 54,3 % | 62,1 % | 55,2 % (143) |
| gpt-5.6-terra (línea base) | 61,3 % | 52,0 % | 51,7 % | 83,3 % | 83,3 % | 51,9 % | 59,6 % | 52,0 % (150) |
| gpt-6.1-terra | 59,3 % | 51,3 % | 46,7 % | 78,3 % | 86,7 % | 50,0 % | 62,1 % | 52,7 % (129) |
| gemini-3.1-pro-preview | 57,0 % | 45,3 % | 46,7 % | 85,0 % | 80,0 % | 45,7 % | 55,9 % | 45,3 % (150) |
| gpt-5.4-mini | 54,7 % | 41,3 % | 43,3 % | 83,3 % | 86,7 % | 41,9 % | 54,0 % | 41,3 % (150) |

R@5 estricta:

| Modelo | Total | `live` | `urg` | `exam` | `synth` | `live`+`urg` | Raras | `live` sin ver |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| gpt-6.1-sol | **81,3 %** | **73,3 %** | **78,3 %** | **96,7 %** | 96,7 % | **74,8 %** | **78,9 %** | 73,3 % |
| claude-opus-5 | 78,7 % | 71,3 % | 73,3 % | 95,0 % | 93,3 % | 71,9 % | 73,3 % | 72,7 % |
| gpt-5.6-terra (línea base) | 78,3 % | 71,3 % | 76,7 % | 88,3 % | 96,7 % | 72,9 % | 73,9 % | 71,3 % |
| gpt-6.1-terra | 73,7 % | 64,7 % | 70,0 % | 88,3 % | 96,7 % | 66,2 % | 71,4 % | 68,2 % |
| gemini-3.1-pro-preview | 68,7 % | 57,3 % | 68,3 % | 90,0 % | 83,3 % | 60,5 % | 64,0 % | 57,3 % |
| gpt-5.4-mini | 70,0 % | 56,7 % | 73,3 % | 88,3 % | 93,3 % | 61,4 % | 64,6 % | 56,7 % |

«`live` sin ver»: casos publicados después del corte del modelo
(`data29/data-repos/narrative-v2/model_cutoffs.yaml`), entre paréntesis.

Diferencias con Terra 5.6 en casos reales (`live`+`urg`, 210 casos),
McNemar exacto sobre los mismos casos:

| Modelo | R@1: gana / pierde | p | R@5: gana / pierde | p |
|---|---:|---:|---:|---:|
| gpt-6.1-sol | 22 / 9 (+6,2 pp) | 0,03 | 14 / 10 (+1,9 pp) | 0,54 |
| claude-opus-5 | 26 / 21 (+2,4 pp) | 0,56 | 15 / 17 (−1,0 pp) | 0,86 |
| gpt-6.1-terra | 12 / 16 (−1,9 pp) | 0,57 | 6 / 20 (−6,7 pp) | 0,009 |
| gemini-3.1-pro-preview | 11 / 24 (−6,2 pp) | 0,04 | 5 / 31 (−12,4 pp) | < 0,001 |
| gpt-5.4-mini | 10 / 31 (−10,0 pp) | 0,001 | 7 / 31 (−11,4 pp) | < 0,001 |

| Modelo | Opciones por caso (mediana) | Latencia por caso (mediana) | Coste del juez |
|---|---:|---:|---:|
| gpt-6.1-sol | 5 | 22 s | 4,3 $ |
| claude-opus-5 | 10 | 27 s | 5,9 $ |
| gpt-5.6-terra | 4 | 8 s | 4,1 $ |
| gpt-6.1-terra | 5 | 4 s | 4,2 $ |
| gemini-3.1-pro-preview | 3 | 10 s | 3,4 $ |
| gpt-5.4-mini | 4 | 5 s | 4,2 $ |

Latencias con 8 llamadas en paralelo (4 en Opus) e incluyen la traducción de
`urg`. 0 casos con error del juez en los seis runs.

- **gpt-6.1-sol es el único que mejora a Terra 5.6 en P1 de forma clara** en
  casos reales (+6 puntos). En R@5 empatan.
- **gpt-6.1-terra no mejora a Terra 5.6**: igual en P1, peor en R@5. Coincide
  con `all_256_clean` V4 strict (62,5 % frente a 63,3 % en R@1; 77,3 % frente
  a 83,2 % en R@5).
- **Claude Opus 5** queda entre los dos, sin diferencia significativa con
  Terra 5.6. Devuelve listas de unas 10 opciones: su cobertura (82 %) no es
  comparable con la de los demás, R@1 y R@5 sí.
- **Gemini 3.1 Pro** devuelve 3 o 4 opciones en el 99 % de los casos, y eso le
  cuesta R@5. En `exam` está a la par de los demás.
- **`exam` no separa a los modelos** (78–88 % en R@1) y `live` sí (41–60 %):
  confirma que la cifra principal debe ser `live`+`urg`.
- **Sin señal de contaminación:** en los 21 casos `live` que gpt-6.1-terra
  pudo ver, no acierta más que en el resto.

## Esfuerzo de razonamiento medium (29-oct-2026)

¿Mejoran Terra y Sol razonando más? En `all_256_clean` (V4 strict) no
mejoraban: Terra low 63,3 % de R@1, frente a 62,5 % en medium, high y xhigh;
gpt-6.1-sol low 64,1 %, medium 62,1 %. Se repite en `narrative_v2`, donde los
casos reales dejan más margen. Runs completos con
`config_terra_medium_narrative_v2.yaml` y
`config_gpt61sol_medium_narrative_v2.yaml`: mismo prompt, juez y
`max_tokens` (12.000; ninguna respuesta cortada).

R@1 estricta; McNemar exacto de medium frente a low sobre los mismos casos:

| Grupo | Terra low | Terra medium | gana / pierde | p | Sol low | Sol medium | gana / pierde | p |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Casos reales (`live`+`urg`, 210) | 51,9 % | 53,3 % | 9 / 6 | 0,61 | 58,1 % | 58,6 % | 11 / 10 | 1,0 |
| Raras reales (116) | 53,4 % | 53,4 % | 5 / 5 | 1,0 | 64,7 % | 61,2 % | 4 / 8 | 0,39 |
| No raras reales (94) | 50,0 % | 53,2 % | 4 / 1 | 0,38 | 50,0 % | 55,3 % | 7 / 2 | 0,18 |
| `exam` (60) | 83,3 % | 81,7 % | 3 / 4 | 1,0 | 86,7 % | 85,0 % | 1 / 2 | 1,0 |
| Total (300) | 61,3 % | 62,3 % | 13 / 10 | 0,68 | 67,0 % | 67,0 % | 12 / 12 | 1,0 |

R@5 en casos reales: Terra 72,9 % → 74,3 %; Sol 74,8 % → 74,8 %.

| | Coste por caso | Latencia (mediana) |
|---|---:|---:|
| Terra low → medium | 1,34 → 1,40 c$ | 8,2 → 8,8 s |
| Sol low → medium | 1,04 → 1,17 c$ | 22,3 → 24,0 s |

- **Ninguna diferencia significativa** en ningún grupo ni modelo. Los cambios
  son de uno a cinco casos y en ambos sentidos.
- **Sol medium no mejora a Sol low en raras** (61,2 % frente a 64,7 %, no
  significativo); sube algo en no raras, también sin significación.
- **Se mantiene `low`.** Con casos reales y sin contaminar se confirma lo que
  ya se vio en `all_256_clean`: razonar más cuesta algo más y no acierta más.

## Pedir exactamente 5 diagnósticos (30-oct-2026)

El prompt (`juanjo_classic_v2.txt`), igual que el de producción
(`Server/assets/prompts.js`), dice «generate N possible diagnoses» con la N
sin sustituir, así que cada modelo decide cuántas opciones da. Terra da menos
de 5 en la mitad de los casos, Gemini 3.1 Pro casi siempre 3 y Opus 5 siempre
10, y eso afecta a R@5 y a la cobertura. Con el pipeline anterior, pedir 5
restaba precisión. Se repite con `juanjo_classic_v2_n5.txt`, que solo cambia
«N» por «5» (`config_<modelo>_low_n5_narrative_v2.yaml`). Mismos casos y
juez. McNemar de «5» frente a «N»:

| Grupo | Terra «N» | Terra «5» | gana / pierde | p | Sol «N» | Sol «5» | gana / pierde | p |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| R@1 casos reales (210) | 51,9 % | 53,3 % | 10 / 7 | 0,63 | 58,1 % | 59,5 % | 11 / 8 | 0,65 |
| R@1 raras reales (116) | 53,4 % | 53,4 % | 6 / 6 | 1,0 | 64,7 % | 63,8 % | 4 / 5 | 1,0 |
| R@1 no raras reales (94) | 50,0 % | 53,2 % | 4 / 1 | 0,38 | 50,0 % | 54,3 % | 7 / 3 | 0,34 |
| R@5 casos reales (210) | 72,9 % | 73,8 % | 7 / 5 | 0,77 | 74,8 % | 76,2 % | 6 / 3 | 0,51 |
| R@1 total (300) | 61,3 % | 62,3 % | 14 / 11 | 0,69 | 67,0 % | 67,3 % | 12 / 11 | 1,0 |

| | Opciones (mediana) | Con menos de 5 | Coste por caso | Latencia (mediana) |
|---|---:|---:|---:|---:|
| Terra «N» → «5» | 4 → 5 | 50 % → 0 % | 1,34 → 1,47 c$ | 8,2 → 9,4 s |
| Sol «N» → «5» | 5 → 5 | 8 % → 0 % | 1,04 → 1,03 c$ | 22,3 → 16,4 s |

- **Pedir 5 no resta precisión con ninguno de los dos.** Las diferencias son
  de 1 a 4 casos, en los dos sentidos, y caben en lo que cambia un modelo al
  repetir la misma ejecución.
- **Todas las listas tienen 5 opciones**, así que R@5 y la cobertura pasan a
  ser comparables entre modelos sin control de longitud.
- La latencia de Sol depende de la carga del momento (las dos ejecuciones no
  fueron a la vez); no conviene leer la bajada como efecto del prompt.
- **Decidido el 30-oct-2026: producción pide 5.** Cambiado en los dos prompts
  de diagnóstico de `Server/assets/prompts.js` (`withoutDiseases`: «generate 5
  possible diagnoses»; `withDiseases`: «generate 5 more»), en la rama
  `develop` de `Dx29_server_gpt`, sin commit ni despliegue todavía. Para que el
  benchmark mida lo mismo que producción, las próximas ejecuciones oficiales
  (el re-scoring con `narrative_v2` v0.2) usarán `juanjo_classic_v2_n5`.

## Prueba de juez más barato (29-oct-2026)

Paso 6 del ROADMAP. Las listas de los seis modelos se han vuelto a puntuar con
Gemini 3.8 Flash y Gemini 2.5 Flash (`OUTPUT_TAG: judge_<modelo>`, en carpetas
`<modelo>__judge_<juez>`), y Gemini 2.5 Pro se ha repetido sobre las listas de
Terra 5.6 para medir cuánto varía el propio juez. Detalle completo:
`output/narrative_v2/juanjo_classic_v2/judge_comparison.md`
(`py compare_judges.py --judges gemini-3.8-flash gemini-2.5-flash`).

R@1 estricta en casos reales (`live`+`urg`, 210):

| Modelo | Gemini 2.5 Pro | Gemini 3.8 Flash | Gemini 2.5 Flash |
|---|---:|---:|---:|
| gpt-6.1-sol | 58,1 % | 60,5 % | 56,7 % |
| claude-opus-5 | 54,3 % | 55,2 % | 56,2 % |
| gpt-5.6-terra | 51,9 % | 55,2 % | 52,9 % |
| gpt-6.1-terra | 50,0 % | 53,8 % | 50,0 % |
| gemini-3.1-pro | 45,7 % | 46,2 % | 44,8 % |
| gpt-5.4-mini | 41,9 % | 43,8 % | 42,9 % |

| Juez | Mismo «2 o no» que Pro (por opción) | Kappa | Misma nota 2/1/0 | Coste, seis modelos | Mediana por llamada |
|---|---:|---:|---:|---:|---:|
| Gemini 2.5 Pro repetido (Terra) | 98,5 % | 0,96 | 94,3 % | 26,15 $ | 11,1 s |
| Gemini 3.8 Flash | 98,0 % | 0,93 | 87,7 % | 0,83 $ | 2,0 s |
| Gemini 2.5 Flash | 97,8 % | 0,92 | 86,8 % | 5,99 $ | 5,0 s |

- **El orden de los modelos no cambia** en R@1 con ningún juez, ni en casos
  reales ni en el total. En R@5 solo se cruzan Opus 5 y Terra 5.6, que con Pro
  están a un punto o menos.
- **En la frontera que usa la nota estricta («2 o no»), Gemini 3.8 Flash
  discrepa de Pro casi lo mismo que Pro de sí mismo** (98,0 % frente a
  98,5 %). Sus diferencias están sobre todo entre 1 y 0, que solo afecta a la
  nota laxa.
- **3.8 Flash da 1–4 puntos más de R@1** según el modelo. No se pueden mezclar
  cifras de jueces distintos: si se cambia de juez, se re-puntúa todo (cuesta
  menos de 1 $ por los seis modelos).
- **En las 208 opciones en que discrepan sobre el 2, ninguno es claramente mejor.**
  Flash acierta, por ejemplo, «Polymyxin-associated neurotoxicity» frente a
  «Polymyxin B-induced neurotoxicity», que Pro deja en 1; Pro da un 2 dudoso a
  «Aortic regurgitation… with aortic root dilatation» frente a «Aortic aneurysm».
- **Gemini 3.8 Flash cuesta unas 30 veces menos y es 5 veces más rápido**
  (precio de Google hasta el 31-dic-2026; el doble después). La decisión
  depende de cuál se parece más al criterio de David (tarea 2 de
  `docs/tareas-david/`).

### Juez de otra familia: Claude Opus 5.5 (30-oct-2026)

Para comprobar que la conclusión no depende de usar siempre Gemini, las
mismas listas se han puntuado con Claude Opus 5.5 (esfuerzo `low`,
`OUTPUT_TAG: judge_claude-opus-5-5`). `evaluator.py` trata los modelos Claude
como jueces con esfuerzo, sin temperatura.

| Modelo | R@1 casos reales, Pro | Claude Opus 5.5 |
|---|---:|---:|
| gpt-6.1-sol | 58,1 % | 59,0 % |
| claude-opus-5 | 54,3 % | 53,3 % |
| gpt-5.6-terra | 51,9 % | 51,4 % |
| gpt-6.1-terra | 50,0 % | 51,0 % |
| gemini-3.1-pro | 45,7 % | 46,2 % |
| gpt-5.4-mini | 41,9 % | 42,9 % |

- **Mismo orden que Pro en R@1** (casos reales y total) y mismo «2 o no» en el
  97,8 % de las opciones (kappa 0,92), igual que Gemini 3.8 Flash. Es más
  estricto que Pro entre 1 y 0, que solo afecta a la nota laxa.
- **No favorece a Claude Opus 5**: le da un punto menos que Pro.
- **Sol frente a Terra con este juez:** 21 / 5 en casos reales (p = 0,002) y
  16 / 2 en raras reales (p = 0,001). Sol frente a Opus: 19 / 3 en raras reales
  (p = 0,001), 7 / 11 en no raras (p = 0,48).
- Coste: 11,97 $ los seis modelos, 2,8 s de mediana por llamada, 0 errores.

## Variabilidad entre ejecuciones (29-oct-2026)

¿Cuánto cambia el resultado si se repite el mismo run? Terra 5.6 low se ha
vuelto a ejecutar entero sobre `narrative_v2` (genera, traduce, etiqueta y
puntúa) con `config_terra_low_narrative_v2_rerun2.yaml`, en la carpeta
`gpt_5_6_terra_low_translated_en__rerun2`.

| Grupo | R@1 run 1 | R@1 run 2 | gana / pierde | p | R@5 run 1 | R@5 run 2 |
|---|---:|---:|---:|---:|---:|---:|
| Casos reales (`live`+`urg`, 210) | 51,9 % | 52,4 % | 12 / 11 | 1,0 | 72,9 % | 72,9 % |
| Raras reales (116) | 53,4 % | 52,6 % | 6 / 7 | 1,0 | 69,0 % | 69,8 % |
| No raras reales (94) | 50,0 % | 52,1 % | 6 / 4 | 0,75 | 77,7 % | 76,6 % |
| `exam` (60) | 83,3 % | 80,0 % | 1 / 3 | 0,63 | 88,3 % | 88,3 % |
| Total (300) | 61,3 % | 61,0 % | 14 / 15 | 1,0 | 78,3 % | 78,0 % |

- **La cifra agregada apenas se mueve** (un punto o menos en casos reales y en
  el total), **pero por debajo cambia el acierto en P1 de 1 de cada 10 casos**
  (29 de 300), en los dos sentidos.
- Por eso una diferencia de 2 o 3 puntos entre dos runs no dice nada por sí
  sola, y menos en un bloque de 60 casos: hace falta el McNemar sobre los
  mismos casos.
- Coste: 1,34 c$ por caso de generación y 4,30 $ de juez, igual que el primero.

**Sol, también dos veces (30-oct):** `config_gpt61sol_low_narrative_v2_rerun2.yaml`.

| Grupo | Sol run 1 | Sol run 2 | gana / pierde | p |
|---|---:|---:|---:|---:|
| Casos reales (210) | 58,1 % | 57,6 % | 11 / 12 | 1,0 |
| Raras reales (116) | 64,7 % | 60,3 % | 3 / 8 | 0,23 |
| No raras reales (94) | 50,0 % | 54,3 % | 8 / 4 | 0,39 |
| `exam` (60) | 86,7 % | 85,0 % | 0 / 1 | 1,0 |
| Total (300) | 67,0 % | 66,0 % | 11 / 14 | 0,69 |

Sol frente a Terra en R@1 con cada pareja de ejecuciones (McNemar exacto):

| Ejecuciones | Casos reales | p | Raras reales | p |
|---|---:|---:|---:|---:|
| Sol 1 / Terra 1 | 22 / 9 | 0,03 | 18 / 5 | 0,01 |
| Sol 1 / Terra 2 | 21 / 9 | 0,04 | 16 / 2 | 0,001 |
| Sol 2 / Terra 1 | 24 / 12 | 0,07 | 15 / 7 | 0,13 |
| Sol 2 / Terra 2 | 23 / 12 | 0,09 | 14 / 5 | 0,06 |
| **Las dos de cada uno** | **29 / 15** | **0,05** | **21 / 7** | **0,01** |

«Las dos de cada uno»: en cada caso, aciertos de Sol (0, 1 o 2) menos
aciertos de Terra, con una prueba de signos exacta sobre los casos en que esa
resta no es cero. R@1 medio: casos reales 57,9 % frente a 52,1 %; raras
reales 62,5 % frente a 53,0 %; no raras 52,1 % frente a 51,1 %.

- **La ventaja de Sol en raras se confirma**, pero es de unos 9,5 puntos, no
  los 11 de la primera ejecución. En no raras empatan.
- **Con una sola ejecución, la significación depende de qué ejecución toque**:
  en casos reales, p va de 0,03 a 0,09. Julián tenía razón con la n de 210.
  Para decidir entre dos modelos cercanos en `narrative_v2` hacen falta dos
  ejecuciones de cada uno, o más casos. Las 3.006 raras de HPO, donde la
  ventaja de Sol es clara (p < 0,001 con los dos jueces), pesan más que
  `narrative_v2` para esta decisión.
- **El juez también varía.** Con las mismas listas de Terra, una segunda
  llamada a Gemini 2.5 Pro (`__judge_gemini_2_5_pro_rerun`) cambia el 5,7 %
  de las 1.423 notas y el acierto en P1 en 8 de 300 casos: R@1 61,3 % frente
  a 60,0 %. En las 12 ejecuciones con juez Pro, la misma opción para el mismo
  caso y gold aparece 2.953 veces repetida, y en el 12,2 % recibe notas
  distintas; casi todas son 1 frente a 0, que no tocan la cifra estricta, y 75
  incluyen un 2.

### Punto 6 de Julián: la respuesta que nombra el gold y algo más (30-oct-2026)

La rúbrica dice qué hacer cuando la referencia es «X con Y» y la opción «X»
(C2.1, nota 2), pero no el caso contrario: la opción nombra el gold y añade
una causa o una complicación. Su ejemplo está en los datos, en
`L-PMC13354413` (gold «Choledochoduodenal fistula»): Terra dice «Ascending
cholangitis caused by a spontaneous choledochoduodenal fistula» y recibe un
1; Sol dice «Choledochoduodenal fistula with food impaction causing acute
suppurative cholangitis» y recibe un 2. Las dos nombran la fístula y la
colangitis; cambia el orden. Y la misma opción puede recibir notas distintas:
«Infected branchial cleft cyst» saca un 2 en una ejecución y un 1 en otra.

- De las 1.391 opciones que contienen el nombre entero del gold y algo más,
  el juez ya da un 2 al 95,3 %. Un 1 a 64; muchas con razón: disyuntivas
  («Stevens-Johnson / TEN»), otra enfermedad que contiene el nombre
  («Huntington's disease-like 2», «carcinoma ex pleomorphic adenoma»).
- Contando solo las opciones que contienen el nombre exacto del gold, el R@1
  cambiaría como mucho en 2 casos de 300 por modelo. **Esa estimación se
  quedó corta**: ver la medición de abajo.

`graded_v3` (en `evaluator.py`, `EVALUATOR.JUDGE_PROMPT_VERSION`; por defecto
desde el 30-oct, y `graded_v2` para reproducir lo anterior): nota 2 cuando la opción afirma que el paciente tiene el
diagnóstico de referencia, aunque añada una causa, una complicación u otro
hallazgo («X con Y», «X por Y», «Y causada por X»); siguen en 1 las
disyuntivas y otra enfermedad cuyo nombre contiene la referencia. Con
`EVALUATOR.JUDGE_GRADE_CACHE`, cada opción repetida (mismo gold y texto) se
puntúa una vez y la nota se reutiliza en todos los modelos
(`output/narrative_v2/judge_grades__gemini-2.5-pro__graded_v3.json`).
Medición del 30-oct: mismas listas de los seis modelos, juez Pro
(`<modelo>__graded_v3`, 23,93 $, 2.517 notas reutilizadas):

| R@1 | Reales v2 | Reales v3 | gana / pierde | Raras reales v2 | v3 | Total v2 | v3 |
|---|---:|---:|---:|---:|---:|---:|---:|
| gpt-6.1-sol | 58,1 % | 62,9 % | 10 / 0 | 64,7 % | 66,4 % | 67,0 % | 70,3 % |
| Claude Opus 5 | 54,3 % | 56,7 % | 6 / 1 | 54,3 % | 55,2 % | 64,7 % | 66,7 % |
| Terra 5.6 | 51,9 % | 53,3 % | 4 / 1 | 53,4 % | 55,2 % | 61,3 % | 62,3 % |
| gpt-6.1-terra | 50,0 % | 53,8 % | 8 / 0 | 56,0 % | 58,6 % | 59,3 % | 61,7 % |
| Gemini 3.1 Pro | 45,7 % | 46,7 % | 2 / 0 | 48,3 % | 48,3 % | 57,0 % | 57,7 % |
| gpt-5.4-mini | 41,9 % | 44,3 % | 5 / 0 | 42,2 % | 44,0 % | 54,7 % | 56,7 % |

- **Corrige el caso de Julián**: la P1 de Terra en la fístula pasa de 1 a 2,
  y también el pseudoquiste roto, el nanoftalmos o «faringitis con
  adenopatía reactiva» para adenopatía cervical.
- **Las respuestas iguales ya no puntúan distinto**: de 126 de 7.700 (1,6 %)
  a 0.
- **Sube más de lo que buscaba la regla escrita.** 37 casos pasan a acertar
  en P1 y 3 dejan de hacerlo; entre los que suben hay disyuntivas
  («Stevens-Johnson / NET», «colelitiasis / colecistitis») y respuestas
  relacionadas que no nombran el gold («herpangina» para faringoamigdalitis
  aguda). 9 de las ganancias vienen de una nota reutilizada.
- El orden casi no cambia: solo se cruzan gpt-6.1-terra y Terra 5.6, que
  están a medio punto. Sol frente a Terra 5.6 en raras reales: 16 / 3 con v3
  (p = 0,004), antes 18 / 5.
- **Decidido el 30-oct (Julián): se adopta `graded_v3` y se deja de ajustar
  la rúbrica con contraejemplos**, porque con cualquier dataset saldrá alguno.
  Criterio: la enfermedad que propone el modelo es la misma entidad si está
  relacionada con el gold y se trata de la misma forma. Las ganancias de
  arriba encajan en ese criterio. `graded_v3` es el juez por defecto; las
  cifras publicadas siguen con v2 hasta volver a puntuar con `narrative_v2`
  v0.2, con la caché de notas.
- Antes de la decisión se probó una versión más estricta (v3b: disyuntivas
  nunca 2, la opción tiene que nombrar el gold y cada opción nueva se puntúa
  dos veces) sobre las 178 opciones que cruzaban la línea del 2 (3,57 $).
  Se descartó con la decisión y no está en el código.

## Sol frente a Terra en raras (HPO v2, 29-oct-2026)

Run completo de gpt-6.1-sol low sobre los seis datasets de HPO v2
(`config_gpt61sol_low_<dataset>_hpo_v2.yaml`), con el mismo prompt,
parámetros y juez (Gemini 2.5 Pro) que las listas de Terra de julio. R@1 y R@5
estrictas con el gold con gen o sin gen; McNemar exacto sobre los mismos
casos:

| Dataset | Casos | R@1 Terra | R@1 Sol | gana / pierde | p | R@5 Terra | R@5 Sol | p R@5 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| DDD | 1.746 | 43,2 % | 48,1 % | 158 / 72 | < 0,001 | 53,7 % | 59,5 % | < 0,001 |
| RAMEDIS | 616 | 34,1 % | 38,6 % | 59 / 31 | 0,004 | 57,5 % | 70,3 % | < 0,001 |
| LIRICAL | 370 | 41,6 % | 47,3 % | 37 / 16 | 0,005 | 58,1 % | 64,3 % | 0,006 |
| MyGene2 | 146 | 37,0 % | 38,4 % | 15 / 13 | 0,85 | 53,4 % | 65,8 % | 0,005 |
| HMS | 88 | 40,9 % | 39,8 % | 3 / 4 | 1,0 | 58,0 % | 55,7 % | 0,63 |
| MME | 40 | 50,0 % | 67,5 % | 8 / 1 | 0,04 | 67,5 % | 75,0 % | 0,45 |
| **Total** | **3.006** | **40,9 %** | **45,6 %** | **280 / 137** | **< 0,001** | **55,3 %** | **62,7 %** | **< 0,001** |

Solo con el gold con gen (`score_blocks.py --without-clinical`), R@1 del total
pasa de 27,2 % a 32,4 % (287 / 129, p < 0,001).

Control de longitud: Terra da 4 opciones de mediana en DDD y 5 en el resto;
Sol, 5 en todos. Contando solo hasta las opciones que dio Terra en cada caso
(máximo 5), R@5 del total pasa de 55,3 % a 61,3 % (312 / 132, p < 0,001). La
ventaja de Sol en R@5 no viene de dar listas más largas.

- **Sol mejora a Terra en raras de forma clara:** +4,7 puntos en R@1 y +7,4 en
  R@5 sobre 3.006 casos. Gana en DDD, RAMEDIS, LIRICAL y MME; en MyGene2 y HMS
  (146 y 88 casos) la diferencia de R@1 está dentro del azar.
- Coincide con `narrative_v2`, donde la ventaja de Sol estaba en las raras
  reales (64,7 % frente a 53,4 %).
- Coste de Sol: 1,04 c$ por caso de generación (31,40 $ los 3.006 casos),
  latencia mediana 20 s con 8 llamadas en paralelo; juez Pro 68,25 $.

### Gemini 3.8 Flash como juez en raras

Las listas de Terra y de Sol de los seis datasets se han vuelto a puntuar con
Gemini 3.8 Flash (carpetas `<modelo>__judge_gemini_3_8_flash`, configs en el
scratchpad como las de `narrative_v2`).

| Listas de | Casos | Mismo acierto P1 | Mismo «2 o no» (por opción) | Kappa | R@1 con Pro | R@1 con Flash |
|---|---:|---:|---:|---:|---:|---:|
| Terra 5.6 | 3.006 | 97,1 % | 97,8 % | 0,91 | 40,9 % | 40,5 % |
| gpt-6.1-sol | 3.006 | 96,9 % | 98,0 % | 0,92 | 45,6 % | 46,6 % |

- **Con Flash, Sol sigue ganando a Terra:** 46,6 % frente a 40,5 % de R@1
  (300 / 116, p < 0,001). Flash coincide con Pro en raras tanto como en
  `narrative_v2` (98,0 %), y el juez cuesta unas 30 veces menos (2,0 $ frente a
  68 $ por las listas de Sol).
- **Donde más se separan, el que se equivoca es Pro.** En MyGene2, 24 casos
  tienen como gold «Arthrogryposis with oculomotor limitation and
  electroretinal anomalies» (OMIM 108145), que en MONDO es sinónimo de
  «distal arthrogryposis type 5» (DA5, PIEZO2). Pro da un 2 a «type 5» en 6 de
  37 opciones y a «type 5D», que es otra enfermedad (ECEL1, OMIM 615065), en
  23 de 24. Flash da un 2 a «type 5» en 37 de 37 y a «type 5D» en 1 de 24. Por
  eso R@1 de Sol en MyGene2 es 38,4 % con Pro y 52,7 % con Flash, y con Flash
  Sol sí gana a Terra en MyGene2 (24 / 7, p = 0,003).
- El juez solo ve nombres. **Pasarle los sinónimos del gold (MONDO u
  Orphanet, a partir de sus códigos OMIM y ORPHA)** evitaría este tipo de error
  con cualquier juez. Probado a continuación.

### Prueba: sinónimos MONDO en el gold (30-oct-2026)

`data29/data-repos/hpo-v2/gold_synonyms.py` añade a `accepted_names` de cada
gold con código OMIM (en DDD, su id MONDO) la etiqueta y los sinónimos
exactos de MONDO, sacados de la API de Monarch. No usa los sinónimos
relacionados, amplios ni estrechos, ni los códigos Orphanet, que suelen ser
grupos. El evaluador ya enseñaba `accepted_names` al juez («also known as»),
así que el prompt no cambia. Cambia el gold en 2.805 de los 3.006 casos, con
unos 4,6 nombres más por gold. Los datasets `<dataset>_hpo_v2_syn.json` son una
prueba y no están versionados; el oficial sigue siendo HPO v2.

Mismas listas de Terra y Sol, vueltas a puntuar con Flash (los 6 datasets,
4,16 $) y con Pro (todos menos DDD, 1.260 casos, 44,63 $):

| Juez | Listas | Casos | R@1 gold v2 | R@1 con sinónimos | gana / pierde | p |
|---|---|---:|---:|---:|---:|---:|
| Pro | Terra 5.6 | 1.260 | 37,6 % | 37,9 % | 14 / 10 | 0,54 |
| Pro | gpt-6.1-sol | 1.260 | 42,1 % | 43,7 % | 25 / 6 | 0,001 |
| Flash | Terra 5.6 | 3.006 | 40,5 % | 40,5 % | 23 / 25 | 0,89 |
| Flash | gpt-6.1-sol | 3.006 | 46,6 % | 46,4 % | 15 / 23 | 0,26 |

Pro frente a Flash sobre los mismos 1.260 casos:

| Listas de | Mismo acierto P1, gold v2 | Con sinónimos | Mismo «2 o no», gold v2 | Con sinónimos | R@1 Pro / Flash, gold v2 | Con sinónimos |
|---|---:|---:|---:|---:|---:|---:|
| Terra 5.6 | 97,1 % | 99,2 % | 98,2 % | 99,2 % | 37,6 / 38,1 % | 37,9 / 38,3 % |
| gpt-6.1-sol | 97,1 % | 98,9 % | 98,3 % | 99,1 % | 42,1 / 44,3 % | 43,7 / 44,0 % |

- **Con los sinónimos, Pro corrige el error de la artrogriposis tipo 5:** da
  un 2 a «type 5» en 33 de 37 opciones (antes, 6) y a «type 5D» en 5 de 24
  (antes, 23). R@1 de Sol en MyGene2 pasa de 38,4 % a 51,4 %, lo mismo que con
  Flash.
- **Los dos jueces pasan a coincidir casi del todo:** el mismo acierto en P1
  en el 99 % de los casos, y menos de medio punto de diferencia en R@1.
- **Flash apenas cambia**: ya reconocía esos sinónimos. Los casos que pierde
  son sobre todo 2 que no debía dar (una enfermedad de otro gen, como B3GAT3
  por B3GALT6).
- **Sol sigue ganando a Terra** con los dos jueces: 43,7 % frente a 37,9 % con
  Pro (127 / 55) y 46,4 % frente a 40,5 % con Flash (292 / 114).
- **Límite: el sinónimo es tan bueno como el código del dataset.** En HMS,
  «Reactive arthritis» lleva OMIM 270150 (síndrome de Sjögren), y «CREST
  syndrome» lleva la esclerodermia familiar. Después de esta prueba,
  `gold_synonyms.py` solo añade sinónimos si el nombre del gold comparte alguna
  palabra significativa con la entrada MONDO, y nunca de un término obsoleto.
  Así quedan fuera 117 gold, listados en `work/synonyms_skipped.txt`; casi
  todos son de DDD, donde a menudo hay sinónimos legítimos con otras palabras
  («deafness» frente a «hearing loss»). Los resultados de arriba son con la
  versión anterior, que cambiaba 2.805 casos en vez de 2.688.
- Propuesta: incorporar los sinónimos a la siguiente versión de raras cuando
  David valide la muestra del bloque F de la tarea 3. Así, la elección de juez
  queda casi solo en el coste.

## Claude Opus 5 en raras (HPO v2, 30-oct-2026)

En `narrative_v2` Opus 5 es el mejor en casos reales no raros, pero en raras
reales queda por detrás de Sol (19 / 3, p = 0,001). Para comprobarlo con más
casos, run completo de Opus 5 low sobre los cuatro datasets pequeños de HPO v2
(`config_claude_opus5_low_<dataset>_hpo_v2.yaml`), con el mismo prompt y juez
(Gemini 2.5 Pro) que Sol y Terra. McNemar de Sol frente a Opus:

| Dataset | Casos | R@1 Terra | R@1 Sol | R@1 Opus | Sol frente a Opus | p | R@5 Terra | R@5 Sol | R@5 Opus |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| LIRICAL | 370 | 41,6 % | 47,3 % | 38,4 % | 54 / 21 | < 0,001 | 58,1 % | 64,3 % | 54,9 % |
| MyGene2 | 146 | 37,0 % | 38,4 % | 18,5 % | 34 / 5 | < 0,001 | 53,4 % | 65,8 % | 43,2 % |
| HMS | 88 | 40,9 % | 39,8 % | 37,5 % | 6 / 4 | 0,75 | 58,0 % | 55,7 % | 58,0 % |
| MME | 40 | 50,0 % | 67,5 % | 37,5 % | 12 / 0 | < 0,001 | 67,5 % | 75,0 % | 50,0 % |
| **Total** | **644** | **41,0 %** | **45,5 %** | **33,7 %** | **106 / 30** | **< 0,001** | **57,6 %** | **64,1 %** | **52,3 %** |

- **Opus queda por detrás de Sol y también de Terra** (82 / 35 a favor de
  Terra, p < 0,001). En R@5 tampoco lo compensa, aunque da 10 opciones de
  mediana.
- **No es que nombre la enfermedad de forma menos precisa.** Contando también
  las notas 1 en P1, Opus llega al 57,0 %, Terra al 63,4 % y Sol al 67,5 %
  (Sol frente a Opus 123 / 55, p < 0,001). Los tres tienen unos 145 casos de
  nota 1 en P1.
- **MyGene2 es donde más pierde (18,5 %)**. Las listas son válidas, pero en
  los casos de artrogriposis distal tipo 5 pone en P1 otras enfermedades
  (Emery-Dreifuss, CFEOM y similares) en vez de esa.
- **Coste:** 6,7 c$ por caso en generación (43,42 $ los 644), frente a
  1,04 c$ de Sol. Juez Pro: 17,91 $. DDD y RAMEDIS no se han pasado por coste.
- Para raras, Opus solo no aporta: Sol es mejor y seis veces más barato.

## Prompt de sermas: Sol frente a Terra (30-oct-2026)

sermas es la versión de DxGPT solo para raras, en App Service. Su prompt
(`sermas/server/assets/prompts.js`) es el de DxGPT con «specialized in rare
diseases», «rare disease diagnoses» y «description of the rare disease». Para
elegir modelo: listas nuevas de Sol y Terra con ese prompt
(`bench/candidate-prompts/sermas_rare.txt`) en LIRICAL, MyGene2, HMS y MME
(644 casos de HPO v2), juez Gemini 3.8 Flash, que es el mismo con el que ya
estaban puntuadas las listas del prompt de DxGPT
(`output/<dataset>_hpo_v2/sermas_rare/<modelo>__judge_gemini_3_8_flash`).

| Prompt | R@1 Sol | R@1 Terra | gana / pierde | p | R@5 Sol | R@5 Terra | gana / pierde | p |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| DxGPT (`juanjo_classic_v2`) | 49,7 % | 42,2 % | 77 / 29 | < 0,001 | 66,0 % | 59,0 % | 78 / 33 | < 0,001 |
| sermas (`sermas_rare`) | 52,5 % | 44,6 % | 79 / 28 | < 0,001 | 66,0 % | 61,0 % | 67 / 35 | 0,002 |

| Modelo | R@1 DxGPT | R@1 sermas | gana / pierde | p | R@5 DxGPT | R@5 sermas | p |
|---|---:|---:|---:|---:|---:|---:|---:|
| Terra 5.6 | 42,2 % | 44,6 % | 52 / 37 | 0,14 | 59,0 % | 61,0 % | 0,23 |
| gpt-6.1-sol | 49,7 % | 52,5 % | 38 / 20 | 0,03 | 66,0 % | 66,0 % | 1,0 |

- **Sol gana a Terra con el prompt de sermas igual que con el de DxGPT**, en
  R@1 y en R@5. Por dataset, en R@1: MyGene2 56,8 frente a 40,4 % (28 / 4,
  p < 0,001), LIRICAL 50,8 frente a 45,9 % (37 / 19, p = 0,02); en HMS y
  MME va por delante sin significación.
- **El prompt de raras no resta.** Sube R@1 unos 2,5 puntos en los dos
  modelos (en Sol, p = 0,03), pero las listas del prompt de DxGPT son de otra
  ejecución (Terra de julio, Sol de octubre) y parte puede ser la variación
  entre ejecuciones. R@5 no cambia.
- **Listas con el prompt de sermas:** 5 opciones de mediana en los dos;
  menos de 5 en el 3 % de los casos con Sol y el 9 % con Terra. Latencia
  mediana 20,2 s con Sol y 11,3 s con Terra; coste 1,09 c$ por caso con Sol y
  1,74 c$ con Terra.
- **Para sermas, Sol.** App Service no corta a los 30 s como SWA (el límite
  de Azure es de unos 230 s) y ni el servidor ni el cliente de sermas ponen
  timeout. Antes de desplegar hay que comprobar que `f29webopenai` y
  `dxgptswitzerland` tienen un despliegue llamado `gpt-6.1-sol`, porque antes
  era `o3-sermas`.

## Pendiente

Decidido e implementado en `graded_v2` (reglas de la rúbrica que contestó
Julián; detalle en el §12 de
`bench/multimodal_beta/JULIAN_HARNESS_REVIEW.md`):

- ~~**ICD-10 exacto**~~: lo decide el juez; solo SNOMED exacto decide sin
  juez (C1). ICD-10 agrupa enfermedades distintas bajo un código: déficit de
  piruvato deshidrogenasa frente a déficit de piruvato carboxilasa.
- ~~**Gold compuestos**~~ («X with Y», «finding due to X»): se aciertan con
  «X» (C2).
- ~~**Casos con varios gold**~~: basta con acertar uno, sean nombres
  alternativos o diagnósticos simultáneos (C3). En `narrative_v2`, los
  secundarios solo puntúan en `urg`; en el resto de bloques son
  comorbilidades y no puntúan.
- ~~**Gold amplios**~~: se mantienen y se aciertan con una forma más
  específica (C4). En `narrative_v2` ya no hay gold inespecíficos («viral
  illness», «… pain»), y los que no son enfermedad los revisa David en la
  tarea 1.
- ~~**Raras (HPO): nombre de la enfermedad sin gen**~~. Hecho en HPO v2
  (`data29/data-repos/hpo-v2/README.md`). Con Terra low, R@1 estricta del
  total HPO: 29,9 % con V4 strict, 27,2 % con V5 y solo el gold con gen,
  40,9 % con V5 y el gold con gen o sin gen.

Pendiente de David (`docs/tareas-david/`):

- **Tarea 1:** validar el gold de `narrative_v2`. Con su resultado sale la
  v0.2 y se re-puntúan los runs con `REFRESH_GOLD_FROM_DATASET`.
- **Tarea 2:** validar la escala 2/1/0 y elegir juez (Gemini 2.5 Pro frente a
  Gemini 3.8 Flash).
- **Tarea 3:** revisar los nombres sin gen de raras y los 9 casos con HPO
  insuficientes.
