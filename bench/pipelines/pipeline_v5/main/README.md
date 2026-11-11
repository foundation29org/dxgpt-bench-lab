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

## Reglas congeladas (desde el 5-nov-2026)

Son las reglas con las que se hizo la línea base oficial de `narrative_v2`
v0.2. Julián señaló el riesgo: si las reglas se ajustan mirando qué falla
cada modelo, las cifras mejoran en este dataset pero no se extrapolan a
otro. Por eso quedan fijas.

Un cambio solo se admite si cumple las tres condiciones:

1. se decide sin mirar qué casos aciertan o fallan los modelos;
2. se aplica a todos los casos;
3. se vuelve a puntuar todo y se publican las cifras de antes y de después.

**Generación**
- Prompt `juanjo_classic_v2_n5`: pide exactamente 5 diagnósticos. Es el de
  producción desde la v0.00196.
- Temperatura 0,1 y razonamiento `low` (`thinking_level` `low` en Gemini).
- Los casos de urgencias se traducen al inglés (`TRANSLATE_CASE`).
- Las configuraciones salen de `config_<modelo>_low_narrative_v2.yaml`
  cambiando solo el prompt.

**Evaluación**
- Juez `gemini-3.8-flash`, con `thinking_level` `low` y temperatura 0,1.
  Puntúa cada opción con la rúbrica `graded_v3` y una caché de notas por juez
  y rúbrica.
- Solo el SNOMED exacto acierta sin juez.
- Un caso se acierta cuando una opción saca un 2 frente a algún gold. Cuentan
  el principal y, en urgencias, los diagnósticos simultáneos del alta.
- La rúbrica no se ajusta con contraejemplos (decisión de Julián del 30-oct).
  Criterio: misma enfermedad si está relacionada con el gold y se trata de la
  misma forma.

**Cifras**
- Principal: R@1 estricta en los casos reales validados (`live` + `urg`).
- Se dan también por raras y no raras y por bloque.
- Secundarias: R@5 y la nota laxa (2 o 1), que es de uso interno.
- `exam` es el control comparable con la literatura.
- Pruebas: McNemar exacto con una ejecución por modelo; prueba de signos
  agrupada con dos.

**Gold de `narrative_v2`**
- Rige el bloque `rules` de
  `data29/data-repos/narrative-v2/decisions_v0.2.yaml`:
  - fuga solo si el texto nombra el diagnóstico o da un resultado que lo
    establece por sí solo;
  - un caso no diagnosticable se excluye;
  - rara = Orphanet o prevalencia < 1/2.000;
  - un caso por diagnóstico principal.
- Nombres aceptados: solo sinónimos y abreviaturas de la misma entidad, sin
  términos más amplios ni más estrechos.
- La validación clínica revisa todos los casos sin ver ningún resultado de
  los modelos. Sus decisiones se aplican a todos antes de puntuar.

**Raras (HPO)**
- Siempre se publican las dos notas: con el gold con gen, y con el gold con
  gen o sin gen.
- Los nombres sin gen se validan sobre una muestra al azar, sin mirar si el
  modelo acierta. Así están hechas las tareas 3 y 4 de David.

**Lo que no se hace**
- Cambiar el gold, los nombres aceptados o la rúbrica, o excluir casos,
  después de ver qué falla o acierta cada modelo.
- Revisar solo los fallos. Si hace falta una revisión, entran aciertos y
  fallos por igual, como en la tarea 2.

**Lo único elegido mirando fallos hasta ahora** son los 11 casos de gold
dudoso que salieron de HPO v2. Se buscaron entre los fallos de Terra (T3) y
mueven el R@1 ≈ 0,15 puntos. En `narrative_v2` no se adaptó ningún caso por
los resultados.

Además, 7 de esos 11 siguen un patrón que tienen 115 casos de RAMEDIS
(fenilcetonuria con hipertirosinemia), y los otros 109 siguen dentro. David
decidió en la tarea 3 que se quedan los 115. En HPO v3 vuelven esos 7 y la
alcaptonuria RAMEDIS_132, y siguen fuera los 3 de DDD.

**Comprobación:** la próxima renovación de casos `live` se construye con
estas reglas, se valida sin ver resultados y se puntúa una sola vez. Hace de
dataset virgen: si las cifras y el orden de los modelos se parecen a los de la
v0.2, las reglas generalizan.

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
  possible diagnoses»; `withDiseases`: «generate 5 more»), desplegado en la
  v0.00196. Para que el benchmark mida lo mismo que producción, las próximas
  ejecuciones oficiales (el re-scoring con `narrative_v2` v0.2) usarán
  `juanjo_classic_v2_n5`.
- **Con imágenes tampoco resta** (MedReaMM pilot250 T+I, 3-nov, evaluador V4
  strict): Terra «5» con el Server v0.00196 frente a la Terra «N» del 24-sep,
  58,8 % frente a 60,8 % en R@1 (16 / 21, p = 0,51) y 78,8 % frente a 77,6 %
  en R@5 (p = 0,70). Mismo día y mismo Server, gpt-6.1-sol: 66,4 % en R@1
  (39 / 20 frente a Terra, p = 0,02) y 83,6 % en R@5 (p = 0,08). Detalle en
  `bench/multimodal_beta/results/2026-11-03-medreamm-pilot250-t-plus-i-sol-vs-terra-n5.md`
  y en la sección «Con imágenes» del informe.

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
  dependía de cuál se parece más al criterio de David (tarea 2 de
  `docs/tareas-david/`). **Resuelta el 6-nov a favor de Flash:** en 96
  parejas difíciles coincide con él en «¿es un 2?» en el 90 % (kappa 0,78),
  frente al 84 % de Pro y el 83 % de Opus 5.5, y se equivoca hacia los dos
  lados por igual.

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

### Juez de referencia: Gemini 3.8 Flash (3-nov-2026)

Google retira Gemini 2.5 Pro el 1-dic-2026: desde ese día las peticiones a
`gemini-2.5-pro` se contestan con Gemini 3.8 Flash. Cambios:

- **Flash es el juez por defecto** en `evaluator.py` (`DEFAULT_JUDGE_MODEL`) y
  en las 29 configs de V5. Las cifras publicadas siguen siendo las de Pro con
  `graded_v2` hasta el re-scoring con `narrative_v2` v0.2; la cabecera del
  informe dice qué juez y qué rúbrica hay detrás, y avisa si los runs
  principales los mezclan.
- **`utils/llm` se niega a usar `gemini-2.5-pro` desde el 1-dic**
  (`RETIRED_GEMINI`), en los evaluadores V4 y V5 y en los scripts de datos, y
  cada llamada a Gemini guarda en `served_model` el modelo que contestó.
- **Puente antes de la retirada:** las mismas listas de los seis modelos,
  puntuadas con `graded_v3` por Flash
  (`<modelo>__judge_gemini_3_8_flash_graded_v3`, notas compartidas en
  `judge_grades__gemini-3.8-flash__graded_v3.json`, 0,86 $; las 1.839
  llamadas las contestó `gemini-3.8-flash`):

| R@1, `graded_v3` | Reales, Pro | Reales, Flash | Raras reales, Pro | Raras reales, Flash | Total, Pro | Total, Flash |
|---|---:|---:|---:|---:|---:|---:|
| gpt-6.1-sol | 62,9 % | 62,9 % | 66,4 % | 65,5 % | 70,3 % | 70,3 % |
| Claude Opus 5 | 56,7 % | 55,7 % | 55,2 % | 53,4 % | 66,7 % | 65,7 % |
| Terra 5.6 | 53,3 % | 55,2 % | 55,2 % | 55,2 % | 62,3 % | 64,0 % |
| gpt-6.1-terra | 53,8 % | 53,8 % | 58,6 % | 56,9 % | 61,7 % | 62,3 % |
| Gemini 3.1 Pro | 46,7 % | 45,7 % | 48,3 % | 47,4 % | 57,7 % | 57,3 % |
| gpt-5.4-mini | 44,3 % | 44,8 % | 44,0 % | 42,2 % | 56,7 % | 57,0 % |

- Mismo acierto en P1 en el 97,3 % de los 1.800 casos y mismo «¿es un 2?» en
  el 97,6 % de las 10.211 opciones (kappa 0,92). Ningún modelo se mueve más
  de 2 puntos.
- El orden en casos reales es el mismo salvo las dos Terra, que se cruzan
  (con Pro estaban a 0,5 puntos).
- Sol sigue ganando a Terra 5.6 con Flash: 23 / 7 en casos reales
  (p = 0,005) y 15 / 3 en raras reales (p = 0,008).
- El juez Flash cuesta unas 28 veces menos que Pro con la misma rúbrica
  (0,86 $ frente a 23,93 $ los seis modelos); su precio se duplica el
  1-ene-2027.

## `narrative_v2` v0.2: línea base oficial (4-nov-2026; 210 casos desde el 6-nov)

Los seis modelos generan listas nuevas sobre los textos finales de la v0.2.
Usan el prompt «5» (`juanjo_classic_v2_n5`), el de producción desde la
v0.00196. Las puntúa Gemini 3.8 Flash con `graded_v3`. Son ejecuciones
completas, con la caché de notas de Flash compartida:
- carpetas `juanjo_classic_v2_n5/<modelo>__v0_2`;
- Sol y Terra 5.6 llevan además `__v0_2_rerun2`.

Las configuraciones salen de las seis `config_<modelo>_low_narrative_v2.yaml`
cambiando el prompt, `OUTPUT_TAG` y la caché. Cada ejecución guarda su copia.

**La cifra principal es R@1 estricta en los 210 casos reales validados**
(150 `live` y 60 `urg`; 113 raras y 97 no raras).

Los 3 recambios de la reserva (`U-T698`, `U-T1328` y `U-T675`) se validaron
el 6-nov. Se volvieron a puntuar las mismas listas (`REUSE_LABELED_DDX` +
`REFRESH_GOLD_FROM_DATASET`), en la misma carpeta de cada ejecución. La única
excepción es `U-T675`: se le recortó una fuga, así que su lista se regeneró
en las 8 ejecuciones con la configuración de cada una.

| Modelo | R@1 reales | Raras | No raras | `live` | `urg` | R@5 reales | R@5 laxa reales | `exam` | `synth` | Total (300) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| gpt-6.1-sol | 64,8 % | 67,3 % | 61,9 % | 66,0 % | 61,7 % | 86,2 % | 97,1 % | 86,7 % | 86,7 % | 71,3 % |
| Claude Opus 5 | 63,3 % | 60,2 % | 67,0 % | 62,0 % | 66,7 % | 84,3 % | 97,1 % | 88,3 % | 93,3 % | 71,3 % |
| Terra 5.6 | 59,0 % | 61,9 % | 55,7 % | 58,0 % | 61,7 % | 82,9 % | 95,7 % | 83,3 % | 86,7 % | 66,7 % |
| gpt-6.1-terra | 58,1 % | 58,4 % | 57,7 % | 56,0 % | 63,3 % | 83,3 % | 98,6 % | 85,0 % | 93,3 % | 67,0 % |
| Gemini 3.1 Pro | 52,9 % | 52,2 % | 53,6 % | 49,3 % | 61,7 % | 73,3 % | 96,7 % | 88,3 % | 76,7 % | 62,3 % |
| gpt-5.4-mini | 47,1 % | 49,6 % | 44,3 % | 45,3 % | 51,7 % | 73,3 % | 94,8 % | 83,3 % | 86,7 % | 58,3 % |

**Antes y después de los 3 recambios** (R@1 en casos reales):

| Modelo | 207 casos (4-nov) | 210 casos (6-nov) |
|---|---:|---:|
| gpt-6.1-sol | 64,7 % | 64,8 % |
| Claude Opus 5 | 63,3 % | 63,3 % |
| Terra 5.6 | 58,5 % | 59,0 % |
| gpt-6.1-terra | 58,0 % | 58,1 % |
| Gemini 3.1 Pro | 52,2 % | 52,9 % |
| gpt-5.4-mini | 46,9 % | 47,1 % |

El orden no cambia.

- **Sol y Opus 5 quedan arriba, empatados**: 29 / 26 casos (p = 0,79).
- **Frente a Terra 5.6 (producción)**, R@1 en casos reales:

  | Modelo | Gana / pierde | p |
  |---|---:|---:|
  | Sol | 22 / 10 | 0,05 |
  | Opus 5 | 32 / 23 | 0,28 |
  | gpt-6.1-terra | 17 / 19 | 0,87 |
  | Gemini 3.1 Pro | 15 / 28 | 0,07 |
  | gpt-5.4-mini | 9 / 34 | < 0,001 |

  Con una sola ejecución, Sol queda justo en el límite: con los 207 casos
  daba 22 / 9 y p = 0,03. La prueba más fuerte es la de las dos ejecuciones,
  que va a continuación.
- **Sol frente a Terra 5.6, con las dos ejecuciones de cada uno:**

  | Grupo | Sol | Terra 5.6 | p |
  |---|---:|---:|---:|
  | Casos reales | 65,2 % | 59,5 % | 0,02 |
  | R@5 en casos reales | 86,0 % | 82,6 % | 0,06 |
  | Raras | 67,7 % | 61,9 % | 0,12 |
  | No raras | 62,4 % | 56,7 % | 0,13 |
  | `live` | 67,0 % | 58,3 % | 0,003 |
  | `urg` | 60,8 % | 62,5 % | 0,77 |

  Con los 207 casos, la de R@5 daba p = 0,04. Con 210 ya no baja de 0,05.

  **Cambia la lectura de la puntuación provisional:** la ventaja ya no está en
  las raras. Está en los case reports (`live`), igual en raras que en no raras;
  en urgencias empatan.
- **De una ejecución a otra:** Sol 64,8 % y 65,7 %, Terra 5.6 59,0 % y
  60,0 %. El acierto en P1 coincide en 192 y 190 de los 210 casos.
- **El prompt «5» frente al clásico** se ha medido en los 126 casos validados
  cuyo texto no cambió desde la v0.1, con el mismo gold y el mismo juez. No
  cambia el R@1 de forma significativa en ningún modelo. La mayor diferencia
  es la de Sol: 67,5 % con «5» frente a 72,2 % con el clásico (3 / 9,
  p = 0,15). Ahora todos dan 5 opciones; antes Opus 5 daba unas 10.
- **Por qué baja respecto a la puntuación provisional** (Sol, de 73,2 % a
  64,8 %):
  - en los 126 casos sin cambios, las listas nuevas aciertan algo menos;
  - los 22 casos con la fuga recortada, ya con el texto limpio, son más
    difíciles para casi todos (Sol 54,5 %);
  - entran los 46 de la reserva: 43 el 4-nov y los 3 recambios el 6-nov.
- **Coste:**
  - generación de Sol 3,10 $, Terra 5.6 4,35 $, Opus 5 13,43 $ y
    gpt-5.4-mini 1,38 $; las segundas ejecuciones de Sol y Terra, 3,10 $ y
    4,34 $;
  - gpt-6.1-terra y Gemini 3.1 Pro no tienen precio registrado (gpt-6.1-terra
    serían ≈ 2,5 $ si cuesta como Terra 5.6);
  - juez, 0,89 $ las 8 ejecuciones, 0 llamadas fallidas;
  - con los 3 recambios (6-nov): regenerar `U-T675` costó 0,10 $ más Gemini,
    y volver a puntuar las 8 ejecuciones, 0,01 $ de juez;
  - en total, unos 33 $ más Gemini.
- **Latencia** (mediana por caso con 8 llamadas en paralelo, 4 en Opus):

  | Modelo | Latencia |
  |---|---:|
  | Opus 5 | 19 s |
  | Sol | 18 s |
  | Gemini 3.1 Pro | 13 s |
  | Terra 5.6 | 9 s |
  | gpt-5.4-mini | 7 s |
  | gpt-6.1-terra | 5 s |

## `narrative_v2` v0.2: primera puntuación con el gold validado (4-nov-2026)

Mismas listas de los seis modelos, con el gold de la v0.2 (validación de
David) y `graded_v3`. Se lanza con `REUSE_LABELED_DDX` y
`REFRESH_GOLD_FROM_DATASET`, en las carpetas
`<modelo>__v0_2_judge_<juez>_graded_v3`. Cuenta solo los 164 casos reales
validados que tienen lista: 91 raros y 73 no raros. Los 43 de la reserva,
validados después, aún no la tienen.

**Es provisional.** En 22 casos se recortó la frase que daba el diagnóstico, y
sus listas se hicieron con el texto anterior. Sin ellos, todos los modelos
bajan entre 2 y 4 puntos.

R@1 con Gemini 3.8 Flash:

| Modelo | Reales | Raras | No raras | R@5 reales | Sin los 22 recortados | Mismos casos, gold v0.1 |
|---|---:|---:|---:|---:|---:|---:|
| gpt-6.1-sol | 73,2 % | 78,0 % | 67,1 % | 87,2 % | 70,4 % | 71,3 % |
| Terra 5.6 | 66,5 % | 67,0 % | 65,8 % | 86,0 % | 64,1 % | 64,0 % |
| Claude Opus 5 | 64,0 % | 62,6 % | 65,8 % | 83,5 % | 59,9 % | 61,6 % |
| gpt-6.1-terra | 64,0 % | 68,1 % | 58,9 % | 79,3 % | 61,3 % | 62,2 % |
| Gemini 3.1 Pro | 56,1 % | 59,3 % | 52,1 % | 69,5 % | 54,2 % | 51,8 % |
| gpt-5.4-mini | 53,7 % | 53,8 % | 53,4 % | 75,6 % | 50,0 % | 50,6 % |

- **Corregir el gold** sube el R@1 de todos los modelos entre 1 y 4 puntos,
  sin diferencia significativa en ninguno, y no cambia el orden.
- **Sol frente a Terra 5.6**, con las dos ejecuciones de cada uno:
  - casos reales: 71,3 % frente a 63,7 % (27 / 12, p = 0,02);
  - raras: 75,3 % frente a 64,8 % (16 / 5, p = 0,03);
  - no raras: 66,4 % frente a 62,3 % (p = 0,48);
  - sin los 22 casos recortados: p = 0,06.

  Con el prompt «5», 72,0 % frente a 64,0 % (17 / 4, p = 0,007), y en raras
  78,0 % frente a 65,9 % (p = 0,007). Es lo mismo que con la v0.1: la ventaja
  de Sol está en las raras.
- **Los tres jueces** sobre las mismas listas:

  | Jueces | Mismo acierto en P1 | Mismo «¿es un 2?» | Kappa |
  |---|---:|---:|---:|
  | Flash / Opus 5.5 | 96,2 % | 98,3 % | 0,94 |
  | Flash / Pro | 96,2 % | 97,4 % | 0,91 |
  | Pro / Opus 5.5 | 95,7 % | 97,1 % | 0,90 |

  Sol es el primero con los tres. Los del medio (Terra 5.6, gpt-6.1-terra y
  Opus 5) se cruzan dentro de 2–3 puntos según el juez.
- **Coste:** Flash 0,53 $ (con las segundas ejecuciones y las de «5»), Pro
  4,70 $ y Opus 5.5 9,45 $. Flash y Pro reutilizan las notas de los gold que
  no cambian.
- **La hoja de la tarea 2** sale de estas notas: 100 parejas de casos
  validados. El modelo y las notas de cada juez están en una clave aparte,
  fuera de git.

La línea base oficial, con listas nuevas para todos los casos, está en la
sección anterior.

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

## HPO v3: Terra y Sol con el gold nuevo (10-nov-2026)

HPO v3 (`data29/data-repos/hpo-v2/README.md`) cambia tres cosas:

- rehace los nombres sin gen con los criterios de David (tareas 3 y 4);
- saca 107 casos por la regla de la causa C;
- recupera 8 casos de RAMEDIS.

Son las mismas listas de Terra (julio) y Sol (29-oct), con el juez Gemini 3.8
Flash y la rúbrica `graded_v3` (carpetas
`output/<dataset>_hpo_v3/juanjo_classic_v2/<modelo>__judge_gemini_3_8_flash`).
Sol no tenía listas de los 8 casos de RAMEDIS que vuelven, porque se generó
sobre la v2. Se han generado con la misma configuración
(`output/ramedis_hpo_v3_sol_missing`).

**Antes y después con la misma rúbrica.** Las cifras v2 publicadas son de
`graded_v2`. Para medir solo el efecto del gold, el gold v2 se ha vuelto a
puntuar con `graded_v3` (carpetas `<modelo>__judge_gemini_3_8_flash_graded_v3`).
Esa puntuación usa una caché de notas sacada de la puntuación v3 del mismo
modelo. En cada caso, el gold que no cambia lleva la misma nota en los dos
lados, así que la diferencia solo viene de los nombres que cambian.

En los mismos 2.899 casos, R@1 y R@5 estrictas con el gold con gen o sin gen:

| Listas | R@1 gold v2 | R@1 gold v3 | gana / pierde | p | R@5 gold v2 | R@5 gold v3 | gana / pierde | p |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Terra 5.6 | 41,6 % | 43,3 % | 68 / 19 | < 0,001 | 56,5 % | 59,4 % | 99 / 14 | < 0,001 |
| gpt-6.1-sol | 47,7 % | 49,3 % | 64 / 19 | < 0,001 | 64,9 % | 67,5 % | 90 / 16 | < 0,001 |

Totales (la v2 tiene 3.006 casos y la v3, 2.907):

| Listas | R@1 v2 publicada (`graded_v2`) | R@1 v2 con `graded_v3` | R@1 v3 | R@5 v2 publicada | R@5 v3 | R@1 v3, solo gold con gen |
|---|---:|---:|---:|---:|---:|---:|
| Terra 5.6 | 40,5 % | 40,4 % | 43,1 % | 55,0 % | 59,2 % | 28,3 % |
| gpt-6.1-sol | 46,6 % | 46,4 % | 49,2 % | 63,3 % | 67,4 % | 34,1 % |

Sol frente a Terra con la v3 (McNemar exacto):

| Dataset | Casos | R@1 Terra | R@1 Sol | gana / pierde | p | R@5 Terra | R@5 Sol | gana / pierde | p |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| DDD | 1.648 | 46,7 % | 52,9 % | 169 / 68 | < 0,001 | 59,8 % | 66,3 % | 166 / 59 | < 0,001 |
| RAMEDIS | 621 | 32,9 % | 37,5 % | 63 / 34 | 0,004 | 55,1 % | 69,4 % | 115 / 26 | < 0,001 |
| LIRICAL | 370 | 43,5 % | 48,6 % | 34 / 15 | 0,009 | 60,5 % | 67,3 % | 40 / 15 | 0,001 |
| MyGene2 | 140 | 41,4 % | 57,1 % | 28 / 6 | < 0,001 | 60,7 % | 73,6 % | 24 / 6 | 0,001 |
| HMS | 88 | 45,5 % | 43,2 % | 5 / 7 | 0,77 | 68,2 % | 62,5 % | 2 / 7 | 0,18 |
| MME | 40 | 52,5 % | 67,5 % | 8 / 2 | 0,11 | 65,0 % | 75,0 % | 6 / 2 | 0,29 |
| **Total** | **2.907** | **43,1 %** | **49,2 %** | **307 / 132** | **< 0,001** | **59,2 %** | **67,4 %** | **353 / 115** | **< 0,001** |

- **Los nombres de la v3 suben el R@1 unos 1,7 puntos en los dos modelos**,
  sobre los mismos casos.
  - Las ganancias son sobre todo de DDD: nombres de serie sin número
    («Developmental and epileptic encephalopathy», «Hereditary spastic
    paraplegia», «Autosomal recessive primary microcephaly») y epónimos.
  - Las pérdidas son gold más específicos, según los criterios de David. Por
    ejemplo, «Mucopolysaccharidosis type IIIB» donde antes valía
    «Mucopolysaccharidosis», o «Griscelli syndrome type 1» cuando la lista dice
    la tipo 2.
- **Parte de la subida depende de `refine`, que no está validado:** 15 de las
  68 ganancias de Terra y 8 de las 64 de Sol. Sin ellas la subida sigue siendo
  significativa: 53 / 19 en Terra y 56 / 19 en Sol.
- **La regla de la causa C explica el resto de la subida del total.**
  - Los 107 casos que salen tenían un R@1 del 8,4 % con Terra y del 11,2 % con
    Sol.
  - Ninguno de los dos modelos acierta en P1 los 8 de RAMEDIS que vuelven: las
    7 fenilcetonurias con hipertirosinemia y la alcaptonuria.
- **La rúbrica no mueve las raras.** Con el gold v2, pasar de `graded_v2` a
  `graded_v3` da 20 / 24 en Terra y 12 / 18 en Sol (p = 0,65 y 0,36).
- **Solo con el gold con gen la nota casi no cambia:** 3 / 0 en los dos
  modelos.
  - Uno es HMS_011, por el gold corregido.
  - Los otros dos son un fallo de la v3: el nombre sin gen se guardó como
    nombre legible del gold con gen (`accepted_names`), así que cuenta también
    en la nota «solo con gen». Por ejemplo, «Constitutional mismatch repair
    deficiency syndrome» para el gold de PMS2.
  - La v3 tiene 17 casos más que la v2 con nombre legible en el gold con gen,
    aunque no todos son este fallo. En la nota principal no cambia nada,
    porque ese nombre ya valía como nombre sin gen. Pendiente de corregir en la
    siguiente versión.
- **Sol sigue ganando a Terra con la v3:** +6,1 puntos de R@1 y +8,2 de R@5.
  Gana en todos los datasets salvo HMS (88 casos), donde la diferencia está
  dentro del azar.
- **Coste del juez:**
  - 4,68 $ las dos puntuaciones v3;
  - 0,81 $ el gold v2 con `graded_v3`, porque con la caché solo se puntúan los
    nombres que cambian;
  - unos céntimos las 8 listas de Sol.

## Con imágenes: MedReaMM con el evaluador V5 (11-nov-2026)

Las listas de Sol y Terra con imágenes del 3-nov (MedReaMM pilot250 T+I, Server
v0.00196, prompt «5»; `bench/multimodal_beta/results/2026-11-03-medreamm-pilot250-t-plus-i-sol-vs-terra-n5.md`)
se habían puntuado con el evaluador V4 (`strict_equivalence`, juez Gemini 2.5
Pro). Ahora se puntúan con el V5, como el resto: labeler, SNOMED idéntico y
juez Gemini 3.8 Flash con `graded_v3`. Son las mismas listas y el gold es
solo el diagnóstico principal, como en V4.

- `medreamm_to_v5.py` pasa los `responses.jsonl` al formato del evaluador:
  `bench/datasets/medreamm_pilot250_ti.json` y un
  `*___ddxs_from_emulator.json` por modelo.
- `config_gpt61sol_medreamm250_ti.yaml` y `config_gpt56terra_medreamm250_ti.yaml`
  no emulan (`SHOULD_EMULATE: false`): solo etiquetan y evalúan.
- Salida: `output/medreamm_pilot250_ti/juanjo_classic_v2_n5/<modelo>__server_v0_00196`.

| Listas | R@1 V4 | R@1 V5 | R@3 V5 | R@5 V4 | R@5 V5 | Pos. media V5 |
|---|---:|---:|---:|---:|---:|---:|
| gpt-6.1-sol | 66,4 % | 68,4 % | 79,2 % | 83,6 % | 82,0 % | 1,298 |
| Terra 5.6 | 58,8 % | 62,0 % | 72,8 % | 78,8 % | 78,0 % | 1,421 |

- **Sol sigue por delante de Terra:** R@1 31 / 15 (p = 0,026); R@5 26 / 16
  (p = 0,16). Con V4 era 39 / 20 (p = 0,018) y p = 0,081.
- **El evaluador V5 sube algo el R@1 en los dos**, con las mismas listas:
  Sol +2,0 puntos (13 / 8, p = 0,38) y Terra +3,2 (10 / 2, p = 0,04). R@5
  baja un poco en los dos.
- Las 3 listas vacías son los mismos casos en los dos modelos: el filtro
  clínico previo los clasifica como pregunta general o con datos
  insuficientes.
- **Coste:** juez 0,23 $ (247 llamadas por modelo, 0 fallidas), más el labeler.
- Estas son las cifras de imágenes de la página /aboutus y de la sección «Con
  imágenes» de `benchmark-report-v5.html`, que mantiene debajo la evaluación
  V4 original.

## `narrative_v2` v0.2: 17 modelos más (11-nov-2026)

Para la página /aboutus, misma configuración que la línea base oficial: los 300
casos de la v0.2, prompt «5» (`juanjo_classic_v2_n5.txt`), traducción de `urg`
al inglés, juez Gemini 3.8 Flash con `graded_v3` y la caché de notas
compartida (`output/narrative_v2/judge_grades__gemini-3.8-flash__graded_v3.json`).
Configuraciones: `config_<modelo>_n5_narrative_v2_v0_2.yaml`; salida en
`output/narrative_v2/juanjo_classic_v2_n5/<modelo>_translated_en__v0_2`.
Claude y grok van por las API de Anthropic y xAI; el resto, por Azure OpenAI y
la API de Gemini.

R@1 y R@5 estrictas. «Reales» son los 210 casos validados (113 raras y 97 no
raras; 150 `live` y 60 `urg`); «total», los 300. Comparación con Sol low por
McNemar exacto sobre los 210 reales. Coste de generación a precio de lista
(Anthropic, OpenAI, Google y xAI, consultados el 11-nov-2026; `LIST_PRICES`
en `build_report.py`) con los tokens del `emulator.log`. Gemini, grok y o3 no
guardan el recuento en el log: «≈» son los tokens medios de una muestra de 20
casos (`output/narrative_v2/token_sample_2026-11-11.json`), con el
razonamiento facturado como salida. gemini-3.5-flash no tiene precio
publicado; Gemini 4 duplica precio desde el 1-dic-2026.

| Modelo | R@1 reales | Raras | No raras | live | urg | R@5 reales | R@1 exam | R@1 total | s/caso | Coste/caso | Frente a Sol, R@1 reales |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| Claude Fable 5.2 low | 77,1 % | 79,6 % | 74,2 % | 79,3 % | 71,7 % | 91,4 % | 86,7 % | 80,3 % | 14,4 | 7,26 c$ | 34 / 8 (p < 0,001) |
| gpt-6.1-sol medium | 66,7 % | 69,9 % | 62,9 % | 68,0 % | 63,3 % | 83,8 % | 85,0 % | 72,3 % | 20,8 | 1,16 c$ | 12 / 8 (p = 0,503) |
| Claude Opus 5.5 low | 66,2 % | 69,9 % | 61,9 % | 67,3 % | 63,3 % | 85,2 % | 83,3 % | 72,0 % | 12,8 | 3,29 c$ | 23 / 20 (p = 0,761) |
| gemini-4-carbon low | 64,8 % | 69,9 % | 58,8 % | 67,3 % | 58,3 % | 87,1 % | 85,0 % | 70,3 % | 15,2 | ≈ 1,45 c$ | 24 / 24 (p = 1,000) |
| **gpt-6.1-sol low** (producción) | 64,8 % | 67,3 % | 61,9 % | 66,0 % | 61,7 % | 86,2 % | 86,7 % | 71,3 % | 18,2 | 1,03 c$ | — |
| Claude Opus 5 low | 63,3 % | 60,2 % | 67,0 % | 62,0 % | 66,7 % | 84,3 % | 88,3 % | 71,3 % | 18,9 | 4,48 c$ | 26 / 29 (p = 0,788) |
| gemini-4-argon low | 63,3 % | 65,5 % | 60,8 % | 64,0 % | 61,7 % | 84,8 % | 90,0 % | 70,0 % | 18,2 | ≈ 1,19 c$ | 21 / 24 (p = 0,766) |
| gpt-5.6-terra medium | 61,0 % | 64,6 % | 56,7 % | 62,7 % | 56,7 % | 82,9 % | 85,0 % | 68,3 % | 9,6 | 1,57 c$ | 14 / 22 (p = 0,243) |
| gpt-5.6-terra high | 60,5 % | 61,9 % | 58,8 % | 59,3 % | 63,3 % | 82,9 % | 81,7 % | 67,0 % | 12,4 | 2,12 c$ | 13 / 22 (p = 0,175) |
| Claude Sonnet 5.5 low | 59,5 % | 60,2 % | 58,8 % | 58,0 % | 63,3 % | 78,6 % | 88,3 % | 68,3 % | 10,3 | 1,72 c$ | 20 / 31 (p = 0,161) |
| gpt-5.6-terra low | 59,0 % | 61,9 % | 55,7 % | 58,0 % | 61,7 % | 82,9 % | 83,3 % | 66,7 % | 8,8 | 1,45 c$ | 10 / 22 (p = 0,050) |
| gpt-6.1-terra low | 58,1 % | 58,4 % | 57,7 % | 56,0 % | 63,3 % | 83,3 % | 85,0 % | 67,0 % | 4,6 | 0,36 c$ | 12 / 26 (p = 0,034) |
| gpt-5.4 low | 56,7 % | 54,9 % | 58,8 % | 50,7 % | 71,7 % | 82,9 % | 81,7 % | 64,7 % | 11,5 | 1,67 c$ | 15 / 32 (p = 0,019) |
| grok-4.7 low | 56,7 % | 57,5 % | 55,7 % | 54,7 % | 61,7 % | 79,0 % | 86,7 % | 65,3 % | 20,8 | ≈ 1,30 c$ | 11 / 28 (p = 0,009) |
| gemini-3.8-flash low | 55,7 % | 60,2 % | 50,5 % | 54,0 % | 60,0 % | 77,1 % | 88,3 % | 64,7 % | 8,6 | ≈ 0,41 c$ | 16 / 35 (p = 0,011) |
| gpt-5.6-luna low | 54,3 % | 52,2 % | 56,7 % | 52,0 % | 60,0 % | 81,4 % | 86,7 % | 63,7 % | 6,7 | 0,13 c$ | 10 / 32 (p = 0,001) |
| o3 high | 53,8 % | 52,2 % | 55,7 % | 51,3 % | 60,0 % | 76,7 % | 85,0 % | 62,0 % | 21,8 | ≈ 2,02 c$ | 21 / 44 (p = 0,006) |
| gemini-3.1-pro-preview low | 52,9 % | 52,2 % | 53,6 % | 49,3 % | 61,7 % | 73,3 % | 88,3 % | 62,3 % | 13,1 | ≈ 2,17 c$ | 11 / 36 (p < 0,001) |
| grok-4.6 low | 51,9 % | 52,2 % | 51,5 % | 50,7 % | 55,0 % | 79,5 % | 83,3 % | 61,3 % | 18,4 | ≈ 0,90 c$ | 7 / 34 (p < 0,001) |
| gemini-3.5-flash low | 49,5 % | 51,3 % | 47,4 % | 47,3 % | 55,0 % | 75,7 % | 83,3 % | 59,7 % | 5,3 | — | 12 / 44 (p < 0,001) |
| gpt-5.4-mini low | 47,1 % | 49,6 % | 44,3 % | 45,3 % | 51,7 % | 73,3 % | 83,3 % | 58,3 % | 6,7 | 0,46 c$ | 11 / 48 (p < 0,001) |
| gemini-3.1-flash-lite low | 42,9 % | 42,5 % | 43,3 % | 39,3 % | 51,7 % | 66,7 % | 75,0 % | 53,0 % | 2,9 | ≈ 0,15 c$ | 9 / 55 (p < 0,001) |
| gpt-4o | 31,0 % | 22,1 % | 41,2 % | 24,0 % | 48,3 % | 49,0 % | 56,7 % | 39,0 % | 6,5 | 0,74 c$ | 8 / 79 (p < 0,001) |

- **Claude Fable 5.2 es el único que supera a Sol con claridad:** +12,3
  puntos de R@1 en casos reales (34 / 8, p < 0,001), en raras y en no raras.
  - La ventaja es parecida en `live` (+13,3) y en `urg` (+10,0).
  - **No es contaminación.** Anthropic da junio de 2026 como corte de
    entrenamiento de Fable 5.2 (y de Opus 5.5 y Sonnet 5.5; ver
    `model_cutoffs.yaml`), aunque el modelo saliera el 9-nov: todos los casos
    `live` son de julio a octubre. Los 60 de urgencias son confidenciales: ningún
    fragmento aparece en el repositorio ni en su historial.
  - Por mes de publicación, la ventaja sobre Sol es de +16,7 (julio, 42
    casos), +16,2 (agosto, 37), +10,5 (septiembre, 38) y +9,1 (octubre, 33):
    diferencias entre meses dentro del azar con tan pocos casos.
  - Es más rápido que Sol (14,4 s frente a 18,2 s), pero cuesta unas 7 veces
    más por caso (7,26 c$ frente a 1,03 c$, a 8 / 40 $ por millón de tokens).
  - Antes de plantearlo para producción falta medirlo en raras (HPO),
    con imágenes y por el camino del Server.
- **Sol medium, Claude Opus 5.5, gemini-4-carbon y gemini-4-argon empatan con
  Sol low.** Más razonamiento en Sol o en Terra sube 1–2 puntos, sin
  significación.
- **grok-4.7 mejora a grok-4.6** (56,7 % frente a 51,9 %), pero queda por
  debajo de Sol.
- **o3 (el modelo anterior de producción) y gpt-4o quedan muy por debajo.**
  gpt-4o da diagnósticos menos específicos («Stress Fracture», «Lung Cancer»)
  y el juez estricto solo acepta la misma enfermedad. Las listas están
  completas (5 opciones en los 300 casos).
- gemini-3.8-flash es el mismo modelo que el juez: su cifra lleva esa salvedad.
- Coste total de los 17 runs: unos 70 $ de generación más el labeler y el
  juez (unos 0,1 $ por run gracias a la caché).

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

- ~~**Tarea 1:** validar el gold de `narrative_v2`~~. Hecha:
  - el 4-nov sale la v0.2, con la tanda de reserva;
  - el 6-nov se validan los 3 recambios: 210 casos reales validados y ninguno
    pendiente (detalle en `data29/data-repos/narrative-v2/README.md`);
  - la línea base oficial ya está puntuada con los 210.
- **Tarea 2:** hecha el 6-nov. Se queda Gemini 3.8 Flash como juez y la rúbrica
  `graded_v3` no cambia (detalle en `docs/tareas-david/02-escala-del-juez.md`).
- **Tareas 3 y 4:** hechas el 10-nov. Salen HPO v3 y su puntuación (sección
  «HPO v3: Terra y Sol con el gold nuevo»). Quedan los casos que se cuentan
  aparte y el nivel de Leigh por COX15 (`data29/data-repos/hpo-v2/README.md`).
