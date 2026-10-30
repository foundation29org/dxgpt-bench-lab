# DxGPT — roadmap operativo

**Última actualización:** 29-oct-2026. El detalle anterior al 15-sep está en
[ROADMAP_HISTORY.md](ROADMAP_HISTORY.md).

## Estado

| Pieza | Estado |
|---|---|
| Evaluador | **Pipeline V5** (`bench/pipelines/pipeline_v5/main`, prompt `graded_v2`): solo SNOMED exacto decide sin juez y el juez puntúa 2/1/0 cada opción. Decisiones en el §12 de [JULIAN_HARNESS_REVIEW.md](../bench/multimodal_beta/JULIAN_HARNESS_REVIEW.md). Pipeline V4 se mantiene para la serie histórica |
| Dataset narrativo | **`narrative_v2` v0.1**, 300 casos, de los que 150 son case reports de jul–oct 2026. Pendiente de validación clínica. Ver `data29/data-repos/narrative-v2/README.md`. `all_256_clean` pasa a ser histórico |
| Raras (HPO) | **HPO v2**: 3.006 casos; además del gold con gen vale el nombre de la enfermedad sin gen, y salen los gold dudosos de T3. Evaluados con V5. Ver `data29/data-repos/hpo-v2/README.md`. V4 strict sobre los 3.017 originales queda para la serie histórica |
| Multimodal | MedReaMM, sin cambios |

Cifras de referencia con Terra low:

| Dataset | Evaluador | R@1 | R@5 |
|---|---|---:|---:|
| `all_256_clean` | V4 strict | 63,3 % | 83,2 % |
| `narrative_v2` v0.1, total | V5 | 61,3 % | 78,3 % |
| `narrative_v2`, casos reales (`live` y `urg`) | V5 | 51,9 % | 72,9 % |
| `narrative_v2`, preguntas de examen (`exam`) | V5 | 83,3 % | 88,3 % |
| Raras HPO v2, total (3.006), gold con gen o sin gen | V5 | 40,9 % | 55,3 % |
| Raras HPO, total (3.017) | V4 strict | 29,8 % | 46,6 % |

## Próximos pasos

### Ahora (no esperan a nadie)

1. ~~**Modelos de referencia sobre `narrative_v2` con V5**~~. Hecho el 28-oct:
   gpt-5.4-mini, gpt-6.1-terra, gemini-3.1-pro-preview (Gemini 3 Pro ya no
   está en la API), Claude Opus 5 y gpt-6.1-sol. Tablas en el
   [README de V5](../bench/pipelines/pipeline_v5/main/README.md). En casos
   reales (`live`+`urg`), solo gpt-6.1-sol mejora a Terra 5.6 en P1 (58,1 %
   frente a 51,9 %, p = 0,03). Para re-puntuar con el gold de David:
   `REUSE_LABELED_DDX` + `REFRESH_GOLD_FROM_DATASET`. gpt-6.1-terra en
   `all_256_clean` con V4 strict, para la serie histórica: R@1 62,5 %, R@5
   77,3 % (`judge_audit/all256_gpt61terra_low_strict/`). **Esfuerzo `medium`**
   (29-oct, Terra 5.6 y gpt-6.1-sol): sin diferencia significativa con `low` en
   ningún grupo, igual que en `all_256_clean`. Se mantiene `low`.
   **Variabilidad entre ejecuciones** (29-oct, Terra 5.6 repetido entero): la
   cifra agregada se mueve un punto o menos, pero cambia el acierto en P1 de 1
   de cada 10 casos, así que diferencias de 2–3 puntos sin McNemar no dicen
   nada. La ventaja de Sol se mantiene frente a la segunda ejecución (21 / 9 en
   casos reales, p = 0,04).
2. ~~**Raras para V5**~~. Hecho el 28-oct en HPO v2
   ([README](../data29/data-repos/hpo-v2/README.md)): en 1.495 casos vale
   también el nombre de la enfermedad sin gen («Leber congenital amaurosis»
   además de «RPGRIP1-related Leber congenital amaurosis»), 11 casos de gold
   dudoso de T3 fuera, y evaluación V5 con las listas de Terra de julio. R@1
   estricta del total: 29,9 % (V4 strict), 27,2 % (V5, gold con gen), 40,9 %
   (V5, gold con gen o sin gen). Pendiente: que David revise una muestra de
   los nombres sin gen (los propone el LLM) y decidir qué hacer con los 9
   casos de HPO insuficientes de T3 (causa C). **gpt-6.1-sol en HPO v2**
   (29-oct, mismo prompt y juez): R@1 45,6 % frente a 40,9 % de Terra y R@5
   62,7 % frente a 55,3 % (280 / 137, p < 0,001), sin dar listas más largas.
   Gana en DDD, RAMEDIS, LIRICAL y MME; en MyGene2 y HMS no hay diferencia
   significativa.
3. ~~**Fechas de corte de los modelos evaluados**~~. Hecho el 28-oct
   (`data29/data-repos/narrative-v2/model_cutoffs.yaml`, con la fuente de cada
   una). Ningún modelo pasa de junio de 2026, así que por `entrez_date` todo
   `live` es no visto. Por fecha de publicación online, 21 casos `live` ya
   estaban publicados antes de fin de junio: gpt-6.1-terra pudo ver 21,
   Opus 5 7 y gpt-6.1-sol 4. `score_blocks.py --live-dates` da la cifra sin
   ellos: varía 1–2 puntos y no da ventaja a quien pudo verlos.

### Cuando David termine sus revisiones

Las revisiones de David tienen cada una su ficha en
[docs/tareas-david/](tareas-david/README.md): validación de `narrative_v2`
(tarea 1, encargada), escala del juez (tarea 2, se prepara tras la 1) y
nombres sin gen de raras más los 9 casos de la causa C de T3 (tarea 3, hoja
lista).

4. **`narrative_v2` v0.2** (tras la tarea 1): aplicar sus correcciones y
   exclusiones, cubrir las bajas con casos de reserva (la selección es estable
   por caso) y re-puntuar los runs. Con eso, línea base oficial.
5. **Validar la escala 2/1/0** (tarea 2) sobre casos de `narrative_v2`,
   incluida la frontera entre 1 y 0, y decidir si la nota laxa se publica.
   **Raras HPO v2** (tarea 3): aplicar sus correcciones a los nombres sin gen
   y a la causa C, y re-puntuar. Propuesta para la misma versión: pasar al
   juez los sinónimos del gold (MONDO u Orphanet, desde sus códigos OMIM y
   ORPHA), porque el juez solo ve nombres y falla con sinónimos poco usados.
6. **Elegir el juez** con esa validación. Si el orden de los modelos no cambia
   con un juez más barato, usar el más barato; si cambia, mantener Gemini 2.5 Pro.
   Primera mitad hecha el 29-oct sobre las listas de los seis modelos: con
   Gemini 3.8 Flash y con Gemini 2.5 Flash el orden en R@1 no cambia, y 3.8
   Flash coincide con Pro en «¿es un 2?» casi tanto como Pro consigo mismo
   (98,0 % frente a 98,5 % de las opciones), por unas 30 veces menos coste.
   En raras (29-oct, listas de Terra y de Sol, 3.006 casos cada una) pasa lo
   mismo: 97,8–98,0 % de opciones con el mismo «2 o no» y Sol sigue ganando a
   Terra con Flash (46,6 % frente a 40,5 %, p < 0,001). Donde más se separan,
   en MyGene2, el que se equivoca es Pro: no reconoce que «Arthrogryposis with
   oculomotor limitation and electroretinal anomalies» es la «distal
   arthrogryposis type 5» y en cambio da por buena la «type 5D», que es otra.
   Falta la segunda mitad: cuál se parece más a las notas de David (tarea 2).
   Detalle en el [README de V5](../bench/pipelines/pipeline_v5/main/README.md).

### Después

7. **Publicar por bloque.** Decidido el 30-oct: la cifra principal es R@1 en
   casos reales (`live` + `urg`) **por separado en raras y en no raras**, y la
   conjunta queda como secundaria. Son poblaciones distintas y mezclarlas
   diluye las diferencias: la ventaja de Sol sobre Terra está toda en raras
   (64,7 % frente a 53,4 %, p = 0,01) y en no raras empatan (50,0 %). Ya está
   así en `benchmark-report-v5.html`. `exam` queda como control comparable
   con la literatura; `synth` aporta poco porque es demasiado fácil.
8. ~~**PoC offline de la capa agéntica**~~. Primera ronda hecha el 29-oct sobre
   `narrative_v2` v0.1 ([bench/agentic_poc](../bench/agentic_poc/README.md)).
   Sobre la lista de Terra 5.6, en casos reales, R@1 pasa de 51,9 % a:
   57,1 % con autocrítica (p = 0,06), 58,1 % con fuentes HPO + PubMed
   (p = 0,007) y **60,5 % con un panel Terra + Sol (p = 0,001; +10 puntos en
   raras)**. Sol solo llega a 58,1 %. Solo el panel cumple el criterio de raras
   de la auditoría; las herramientas no aportan más que la autocrítica y
   empeoran `exam`. Coste del panel: unas 2 veces el actual, y ≈ 24 s, así que
   tendría que ser una segunda fase asíncrona.
   **Con Sol como base, la capa no aporta:** autocrítica +0,5 puntos, fuentes
   −1,0, panel +2,4 (no significativo, solo en no raras); en raras ningún
   brazo mejora a Sol solo (64,7 %). Lo que la capa añadía a Terra era subirla
   al nivel de Sol: la palanca grande es el modelo. Lo apoyan dos pruebas del
   29-oct: Terra repetido mantiene su cifra y Sol le sigue ganando (paso 1), y
   Sol también gana a Terra en las 3.006 raras de HPO v2 (paso 2). Pendiente:
   confirmarlo con `narrative_v2` v0.2. **La decisión entre Sol solo y el
   panel Terra + Sol espera a esa confirmación.**
9. **Renovar el bloque `live` cada trimestre** con `harvest_pmc.py` y fechas
   nuevas: los modelos acabarán entrenando con estos casos.
10. **Track de «mimics»**, enfermedades raras que se presentan como algo
    común: casos de Appendicure (cáncer de apéndice), si los envían. Se
    guardan fuera del repo y se reportan aparte.
11. **Tracks externos**, siempre aparte y sin mezclar: HealthBench (OpenAI)
    para el modo Ask; SDBench (Microsoft) para la capa agéntica, si se publica.

## Reglas

- Un cambio cada vez sobre las mismas listas, con tabla antes/después
  (`bench/pipelines/pipeline_v5/main/compare_runs.py`).
- Toda cifra indica dataset y versión, y evaluador y versión (`V4 strict`,
  `V5 graded_v2`).
- **El repo es público: ningún texto de caso en git.** Los datasets (`*.json`)
  y las hojas de validación clínica están en `.gitignore`.

## Plan del evaluador de octubre: en qué quedó

| Paso | Estado |
|---|---|
| 1. Acordar con Julián | Hecho: §12 de JULIAN_HARNESS_REVIEW.md |
| 2. Mirar cuánto pesa cada capa | Hecho: en `all_256_clean`, 24 aciertos por jerarquía ICD (13 eran otra enfermedad); BERT no aporta aciertos que no dé el juez |
| 3. Probar los cambios de capas | Hecho de una vez en V5, con cada cambio atribuido a su capa en `comparison.md` |
| 4. Revisar con David los casos que dejan de ser acierto | Sustituido por la validación de `narrative_v2` |
| 5. Juez acierto / casi / fallo | Hecho: `graded_v2` |
| 6. David etiqueta con la escala nueva | Pendiente (paso 5 de arriba) |
| 7. Elegir juez | Pendiente (paso 6 de arriba) |
| 8. Cerrar y publicar | V5 publica R@1, R@5 y cobertura por separado; falta publicar por bloque (paso 7 de arriba) |

## Fuentes

- [JULIAN_HARNESS_REVIEW.md](../bench/multimodal_beta/JULIAN_HARNESS_REVIEW.md): rúbrica del juez y decisiones
- [Cómo funciona Pipeline V5](pipeline/pipeline-v5.md): el evaluador vigente, de principio a fin
- [Informe V5](benchmark-report-v5.html): resultados con gráficas (se regenera con `build_report.py`)
- [Pipeline V5](../bench/pipelines/pipeline_v5/main/README.md): evaluador nuevo y resultados
- [narrative_v2](../data29/data-repos/narrative-v2/README.md): dataset narrativo nuevo
- [Guía del harness](../bench/multimodal_beta/HARNESS_EVAL.md)
- [Benchmark de jueces all_256](../bench/multimodal_beta/results/2026-09-16-judge-benchmark-all256-terra.md)
- [Historial](ROADMAP_HISTORY.md)
