# PoC offline de la capa agéntica

Paso 8 del [ROADMAP](../../docs/ROADMAP.md). ¿Mejora DxGPT si, después de la
primera lista, el modelo hace una segunda pasada? Se prueba offline, sobre
`narrative_v2` v0.1, sin tocar producción.

Cada brazo parte de la lista que gpt-5.6-terra (el modelo de producción,
esfuerzo `low`) ya dio para cada caso, añade una segunda etapa y se puntúa con
Pipeline V5 (`graded_v2`) y el mismo juez que la línea base, Gemini 2.5 Pro.
La cifra principal son los casos reales (`live + urg`, 210).

## Brazos

| Brazo | Qué hace | Para qué |
|---|---|---|
| A. Autocrítica (`arm_a_self_critique.py`) | Terra relee el caso y su lista, pesa los hallazgos a favor y en contra, y devuelve un top 5 revisado | Control: «pensarlo dos veces», sin información nueva |
| B. Panel (`arm_b_panel.py`) | Terra modera un panel con las listas que ya dieron Terra, gpt-6.1-sol y Claude Opus 5 (anónimas) y devuelve un top 5 consolidado | Idea de MAI-DxO, offline |
| B2. Panel Terra + Sol (`arm_b_panel.py --panel terra sol`) | Igual que B, sin Opus | ¿Hace falta el modelo más caro y lento? |
| C. Fuentes (`arm_c_sources.py`) | Terra extrae los hallazgos como términos HPO y dos búsquedas; con HPO local (`hpo_tools.py`) y PubMed (`pubmed_tools.py`) revisa su lista | Herramientas: lo que según la literatura aporta más |

Herramientas del brazo C:

- **HPO** (release 2026-02-16, en `data29/data-repos/raw/ddd_g2p/`): las
  enfermedades raras cuyas anotaciones mejor encajan con los hallazgos
  (puntuación por contenido de información, al estilo Phenomizer; solo si hay
  al menos 3 hallazgos emparejados) y el perfil fenotípico de cada hipótesis.
- **PubMed**: títulos y resúmenes publicados **hasta el 30-jun-2026**,
  excluyendo el PMID del propio caso. Los casos `live` entraron en PubMed
  desde el 1-jul-2026, así que la búsqueda no puede encontrar su artículo.

## Cómo ejecutar

```powershell
cd "C:\repos\DxGPT\eval\bench\agentic_poc"
py arm_a_self_critique.py
py arm_b_panel.py
py arm_b_panel.py --panel terra sol
py arm_c_sources.py
py evaluate_arm.py arm_a_self_critique arm_b_panel arm_b_panel_terra_sol arm_c_sources

# Con Sol como base (arms *_on_sol)
py arm_a_self_critique.py --base sol
py arm_b_panel.py --panel terra sol --moderator sol
py arm_c_sources.py --base sol
py evaluate_arm.py arm_a_self_critique_on_sol arm_b_panel_terra_sol_on_sol arm_c_sources_on_sol

py compare_arms.py
```

Cada brazo escribe en `work/` (no versionado) su lista en formato labeler y
una traza por caso (`<brazo>_traces.json`: lista base, hallazgos, términos
HPO, enfermedades por fenotipo, búsquedas y artículos). `evaluate_arm.py`
genera `configs/<brazo>.yaml` a partir de la configuración de Terra y lo
puntúa con `REUSE_LABELED_DDX`; los runs quedan en
`bench/pipelines/pipeline_v5/main/output/narrative_v2/juanjo_classic_v2/gpt_5_6_terra_low_translated_en__<brazo>/`.
`compare_arms.py` saca las tablas de abajo.

Cuando David valide `narrative_v2`, basta con re-puntuar los brazos con
`REFRESH_GOLD_FROM_DATASET`, como los demás runs.

## Resultados (29-oct-2026)

`narrative_v2` v0.1, sin validación clínica. Una ejecución por brazo. Tabla
completa: `py compare_arms.py`.

R@1 estricta:

| Run | Casos reales (`live + urg`, 210) | Raras reales (116) | No raras reales (94) | `exam` (60) | Total (300) |
|---|---:|---:|---:|---:|---:|
| gpt-5.6-terra (base, producción) | 51,9 % | 53,4 % | 50,0 % | 83,3 % | 61,3 % |
| gpt-6.1-sol solo | 58,1 % | 64,7 % | 50,0 % | 86,7 % | 67,0 % |
| claude-opus-5 solo | 54,3 % | 54,3 % | 54,3 % | 88,3 % | 64,7 % |
| A. Autocrítica | 57,1 % | 55,2 % | 59,6 % | 85,0 % | 65,3 % |
| B. Panel Terra + Sol + Opus | **61,0 %** | 62,1 % | 59,6 % | 86,7 % | **68,0 %** |
| B2. Panel Terra + Sol | 60,5 % | **63,8 %** | 56,4 % | 85,0 % | **68,0 %** |
| C. Fuentes (HPO + PubMed) | 58,1 % | 56,9 % | 59,6 % | 76,7 % | 64,3 % |

Frente a la base en casos reales (McNemar exacto sobre los mismos casos):

| Run | R@1: gana / pierde | p | R@1 raras: gana / pierde | p | R@5, control de longitud: gana / pierde | p |
|---|---:|---:|---:|---:|---:|---:|
| gpt-6.1-sol solo | 22 / 9 (+6,2 pp) | 0,029 | 18 / 5 | 0,011 | 13 / 12 | 1,0 |
| A. Autocrítica | 20 / 9 (+5,2 pp) | 0,061 | 8 / 6 | 0,79 | 13 / 8 | 0,38 |
| B. Panel de tres | 27 / 8 (+9,0 pp) | 0,002 | 15 / 5 | 0,041 | 17 / 8 | 0,11 |
| B2. Panel Terra + Sol | 23 / 5 (+8,6 pp) | **0,001** | 15 / 3 | **0,008** | 11 / 6 | 0,33 |
| C. Fuentes | 17 / 4 (+6,2 pp) | 0,007 | 7 / 3 | 0,34 | 10 / 5 | 0,30 |

«Control de longitud»: los brazos devuelven 5 opciones (mediana) y Terra 4–5;
el acierto solo cuenta dentro del número de opciones que dio Terra en ese
caso. Sin ese control, el R@5 de los brazos sube 3–6 puntos, pero casi todo
es por tener listas más largas.

Coste y latencia por caso, como serían en producción (precios de
`Server/services/costUtils.js`; latencias medidas con 8 llamadas en paralelo,
orientativas):

| Opción | Coste | Frente a hoy | Latencia aproximada |
|---|---:|---:|---:|
| Terra sola (hoy) | 1,34 c$ | — | 8 s |
| Sol solo | 1,04 c$ | −22 % | 22 s |
| A. Terra + autocrítica | 2,11 c$ | +57 % | 14 s |
| C. Terra + fuentes | 2,60 c$ | +94 % | 16 s |
| B2. Terra y Sol en paralelo + moderador | 2,72 c$ | +103 % | 24 s |
| B. Con Opus además | más (Opus no está en `costUtils.js`) | — | ≈ 30 s |

### Qué se ve

- **Una segunda etapa mejora a Terra en P1 entre 5 y 9 puntos en casos
  reales, sin perder R@5.** De las ganancias, la mitad viene de reordenar lo
  que Terra ya tenía y la otra mitad de añadir un diagnóstico nuevo.
- **El panel Terra + Sol es lo mejor:** +8,6 puntos en P1 (23 casos ganados,
  5 perdidos) y +10,4 en raras. Opus no aporta: el panel de tres no mejora al
  de dos y es más caro y lento.
- **Para raras, lo que más cuenta es el modelo, no las herramientas.** Sol
  solo ya sube 11 puntos en raras; la autocrítica y las fuentes apenas las
  mueven (+2 y +4, no significativo). Las dos suben las no raras (+10).
- **Las herramientas del brazo C no superan a la autocrítica** salvo en que
  pierden menos casos (4 frente a 9), y **empeoran `exam`** (−6,7 puntos):
  en casos de libro, la literatura y el encaje por HPO distraen. Tal como
  están (emparejamiento de HPO sencillo, búsquedas de 3–5 palabras), no
  justifican su coste.
- **Frente a Sol solo, ningún brazo es significativamente mejor** en casos
  reales (el panel Terra + Sol, +2,4 puntos, p = 0,41). La ventaja del panel
  sobre Sol está en las no raras (56,4 % frente a 50,0 %).

Con los criterios de la auditoría de flujos (R@1 en raras al menos +5 puntos
y significativo, sin perder R@5), **pasan los paneles B y B2; A y C no**. Por
latencia, ninguno cabe en una respuesta síncrona de +6 s: el panel tendría
que llegar como segunda fase asíncrona (primero la lista de Terra, después la
del panel), como proponía la auditoría.

### Límites

- **`narrative_v2` v0.1 sin validar.** Las cifras pueden moverse cuando David
  corrija el gold; los brazos se re-puntúan sin coste de generación.
- **Una ejecución por brazo.** El juez varía en uno o dos casos entre
  repeticiones, y la generación no se ha repetido. Con cuatro brazos
  comparados, solo B, B2 y C mantienen p < 0,05 tras corregir por
  comparaciones múltiples (Bonferroni ×4).
- **No se ha probado en el track de raras HPO** (listas de fenotipos), donde
  el encaje por HPO del brazo C debería rendir más que en narrativa.

## Con gpt-6.1-sol como base (29-oct-2026)

¿Y si Sol fuera el modelo de producción? Mismos brazos sobre la lista de Sol
(`--base sol`, `--moderator sol`); Sol hace también la segunda etapa. Arms
`*_on_sol`.

R@1 estricta en casos reales (`live + urg`, 210), frente a Sol solo:

| Run | R@1 | Raras (116) | No raras (94) | Gana / pierde frente a Sol | p | Coste por caso | Latencia aprox. |
|---|---:|---:|---:|---:|---:|---:|---:|
| Sol solo | 58,1 % | 64,7 % | 50,0 % | — | — | 1,04 c$ | 22 s |
| A. Sol + autocrítica | 58,6 % | 61,2 % | 55,3 % | 9 / 8 | 1,0 | 1,35 c$ | 29 s |
| B2. Panel Terra + Sol, modera Sol | 60,5 % | 62,9 % | 57,4 % | 11 / 6 | 0,33 | 2,62 c$ | 26 s |
| C. Sol + fuentes | 57,1 % | 61,2 % | 52,1 % | 7 / 9 | 0,80 | 1,83 c$ | 34 s |

- **Sobre Sol, la segunda etapa no mejora el R@1**: la autocrítica +0,5
  puntos y las fuentes −1,0. Lo que la capa añadía sobre Terra era, sobre
  todo, subirla al nivel de Sol.
- **En raras, ningún brazo mejora a Sol solo** (todos 2–4 puntos por debajo,
  no significativo).
- **El panel Terra + Sol da lo mismo lo modere quien lo modere** (60,5 % con
  Terra y con Sol). Su ventaja sobre Sol solo está en las no raras: 7 casos
  ganados y 0 perdidos (p = 0,016), con el coste y la latencia de llamar a los
  dos modelos.

Lectura conjunta de las dos bases:

| Opción para producción | R@1 casos reales | R@1 raras | Coste | Latencia |
|---|---:|---:|---:|---:|
| Terra sola (hoy) | 51,9 % | 53,4 % | 1,34 c$ | 8 s |
| Terra + autocrítica | 57,1 % | 55,2 % | 2,11 c$ | 14 s |
| Sol solo | 58,1 % | **64,7 %** | **1,04 c$** | 22 s |
| Panel Terra + Sol | **60,5 %** | 62,9–63,8 % | 2,6–2,7 c$ | 24–26 s |

- **La palanca grande es el modelo.** Sol solo da casi toda la mejora en
  raras, más barato que Terra, a cambio de casi triplicar la espera.
- **La capa agéntica, tal como se ha probado (autocrítica, fuentes HPO +
  PubMed), no añade nada sobre un modelo fuerte.** Sirve para subir un modelo
  más débil o más rápido.
- **El panel Terra + Sol es la única opción por encima de Sol solo** (+2,4
  puntos, no significativo), solo en no raras y al doble de coste.
- Con una ejecución por brazo y el gold sin validar, la elección entre Sol
  solo y el panel no se puede cerrar aún: hace falta repetir y confirmar con
  `narrative_v2` v0.2.

## Próximos pasos propuestos

1. **Confirmar con `narrative_v2` v0.2** (re-puntuar todo con el gold de David)
   y **repetir la generación** de Terra sola, Sol solo y el panel Terra + Sol
   para medir cuánto varían.
2. **Decidir entre Sol solo y el panel Terra + Sol** con esos datos. Sol solo
   es más barato y mejor en raras; el panel suma algo en no raras al doble de
   coste. Ver también Sol sobre el track de raras HPO.
3. **Aparcar las herramientas HPO + PubMed en narrativa**: no aportan sobre
   un modelo fuerte. Si se retoman, que sea en el track HPO, donde el encaje
   fenotípico es la entrada natural.
4. Si se elige el panel, diseñar la segunda fase asíncrona en el servidor: el
   primer modelo responde como hoy y el panel llega después por Web PubSub, sin
   reordenar lo ya mostrado sin avisar.
